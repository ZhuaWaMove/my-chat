from pydantic import BaseModel, Field
from typing_extensions import TypedDict, Literal
from langgraph.graph import StateGraph, START, END

from langgraph_agent.app.langgraph_agent.agent import llm


# 1. 定义状态结构
class OptimizeState(TypedDict):
    joke: str
    topic: str
    feedback: str
    funny_or_not: str

# 2. 定义评估模型
class JokeFeedback(BaseModel):
    grade: Literal["funny", "not funny"] = Field(description="笑话是否有趣")
    feedback: str = Field(description="改进建议")

evaluator = llm.with_structured_output(JokeFeedback)

# 3. 定义节点
def generate_joke(state: OptimizeState) -> OptimizeState:
    """生成笑话（结合反馈）"""
    if state.get("feedback"):
        res = llm.invoke(f"写关于 {state['topic']} 的笑话，参考反馈：{state['feedback']}")
    else:
        res = llm.invoke(f"写关于 {state['topic']} 的笑话")
    return {"joke": res.content}

def evaluate_joke(state: OptimizeState) -> OptimizeState:
    """评估笑话"""
    res = evaluator.invoke(f"评价笑话：{state['joke']}")
    return {"funny_or_not": res.grade, "feedback": res.feedback}

# 4. 分支决策函数（循环/终止）
def route_joke(state: OptimizeState) -> str:
    return "Accepted" if state["funny_or_not"] == "funny" else "Rejected"

# 5. 构建工作流（含循环逻辑）
builder = StateGraph(OptimizeState)
builder.add_node("generate", generate_joke)
builder.add_node("evaluate", evaluate_joke)

# 6. 连接节点（循环+终止）
builder.add_edge(START, "generate")
builder.add_edge("generate", "evaluate")
builder.add_conditional_edges("evaluate", route_joke, {
    "Accepted": END,
    "Rejected": "generate"  # 不满足则循环优化
})

# 7. 执行
workflow = builder.compile()
result = workflow.invoke({"topic": "猫","protem":"只输出一条笑话"})
print("最终优化笑话：", result["joke"])