from openai import BaseModel
from pydantic.v1 import Field
from typing_extensions import TypedDict, Literal
from langgraph.graph import StateGraph, START, END

from langgraph_agent.app.langgraph_agent.agent import llm


# 1. 定义状态结构
class RouteState(TypedDict):
    question: str
    question_type: str
    result: str

# 2. 定义路由结构化模型
class RouteDecision(BaseModel):
    question_type: Literal["technical", "philosophical", "creative"] = Field(
        description="问题类型：技术问题/哲学问题/创意问题"
    )
router_llm = llm.with_structured_output(RouteDecision)

# 3. 定义节点
def router(state: RouteState) -> RouteState:
    """判断问题类型"""
    decision = router_llm.invoke(f"分类问题：{state['question']}")
    return {"question_type": decision.question_type}

def answer_technical(state: RouteState) -> RouteState:
    """回答技术问题"""
    res = llm.invoke(f"以技术专家身份回答：{state['question']}")
    return {"result": res.content}

def answer_philosophical(state: RouteState) -> RouteState:
    """回答哲学问题"""
    res = llm.invoke(f"以哲学家身份回答：{state['question']}")
    return {"result": res.content}

def answer_creative(state: RouteState) -> RouteState:
    """回答创意问题"""
    res = llm.invoke(f"以创意专家身份回答：{state['question']}")
    return {"result": res.content}

# 4. 分支决策函数
def route_by_type(state: RouteState) -> str:
    return state["question_type"]

# 5. 构建工作流
builder = StateGraph(RouteState)
builder.add_node("router", router)
builder.add_node("tech", answer_technical)
builder.add_node("phil", answer_philosophical)
builder.add_node("creative", answer_creative)

# 6. 连接节点
builder.add_edge(START, "router")
builder.add_conditional_edges("router", route_by_type, {
    "technical": "tech",
    "philosophical": "phil",
    "creative": "creative"
})
builder.add_edge("tech", END)
builder.add_edge("phil", END)
builder.add_edge("creative", END)

# 7. 执行
workflow = builder.compile()
result = workflow.invoke({"question": "什么是量子计算？"})
print("回答：", result["result"])