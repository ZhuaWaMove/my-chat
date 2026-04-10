from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

from langgraph_agent.app.langgraph_agent.agent import llm


# 1. 定义结构化任务模型
class Section(BaseModel):
    name: str = Field(description="报告章节名称")
    description: str = Field(description="章节描述")

class ReportPlan(BaseModel):
    sections: list[Section] = Field(description="报告章节列表")

planner = llm.with_structured_output(ReportPlan)

# 2. 定义状态结构
class ReportState(TypedDict):
    topic: str
    sections: list[Section]
    completed_sections: list[str]
    final_report: str

# 3. 定义节点
def orchestrator(state: ReportState) -> ReportState:
    """协调器：拆分报告章节"""
    plan = planner.invoke([
        SystemMessage(content="生成报告章节计划"),
        HumanMessage(content=f"报告主题：{state['topic']}")
    ])
    return {"sections": plan.sections}

def worker(state: ReportState) -> ReportState:
    """工作者：撰写单个章节"""
    sections_content = []
    for sec in state["sections"]:
        res = llm.invoke([
            SystemMessage(content="按章节名称和描述撰写 Markdown 内容，无需前言"),
            HumanMessage(content=f"章节：{sec.name}，描述：{sec.description}")
        ])
        sections_content.append(res.content)
    return {"completed_sections": sections_content}

def synthesizer(state: ReportState) -> ReportState:
    """聚合器：合并章节为完整报告"""
    final = "\n\n---\n\n".join(state["completed_sections"])
    return {"final_report": final}

# 4. 构建工作流
builder = StateGraph(ReportState)
builder.add_node("orchestrate", orchestrator)
builder.add_node("work", worker)
builder.add_node("synthesize", synthesizer)

# 5. 连接节点（线性流程）
builder.add_edge(START, "orchestrate")
builder.add_edge("orchestrate", "work")
builder.add_edge("work", "synthesize")
builder.add_edge("synthesize", END)

# 6. 执行
workflow = builder.compile()
result = workflow.invoke({"topic": "LLM 缩放定律"})
print("完整报告：", result["final_report"])
