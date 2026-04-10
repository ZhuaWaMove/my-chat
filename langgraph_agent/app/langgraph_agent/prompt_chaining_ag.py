from openai import BaseModel
from pydantic import Field
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

from langgraph_agent.app.langgraph_agent.agent import llm


# 1. 定义状态结构
class JokeState(TypedDict):
    joke: str
    topic: str
    needs_improvement: bool

# 2. 定义结构化评估模型
class PunchlineEvaluation(BaseModel):
    needs_improvement: bool = Field(description="笑话是否需要改进（笑点平庸则返回 true）")
evaluator = llm.with_structured_output(PunchlineEvaluation)

# 3. 定义节点函数
def generate_joke(state: JokeState) -> JokeState:
    """生成主题相关笑话"""
    joke = llm.invoke(f"写一个关于 {state['topic']} 的笑话")
    return {"joke": joke.content}

def check_punchline(state: JokeState) -> JokeState:
    """评估笑话是否需要改进"""
    evaluation = evaluator.invoke(f"评估笑点：{state['joke']}")
    return {"needs_improvement": evaluation.needs_improvement}

def improve_joke(state: JokeState) -> JokeState:
    """改进笑话"""
    improved = llm.invoke(f"优化笑话使其更有趣：{state['joke']}")
    return {"joke": improved.content}

def polish_joke(state: JokeState) -> JokeState:
    """润色笑话"""
    polished = llm.invoke(f"润色笑话：{state['joke']}")
    return {"joke": polished.content}

# 4. 定义条件分支函数
def should_improve(state: JokeState) -> str:
    return "improve_joke" if state["needs_improvement"] else "polish_joke"

# 5. 构建工作流
builder = StateGraph(JokeState)
builder.add_node("generate", generate_joke)
builder.add_node("check", check_punchline)
builder.add_node("improve", improve_joke)
builder.add_node("polish", polish_joke)

# 6. 连接节点（固定边+条件边）
builder.add_edge(START, "generate")
builder.add_edge("generate", "check")
builder.add_conditional_edges("check", should_improve, {
    "improve_joke": "improve",
    "polish_joke": "polish"
})
builder.add_edge("improve", "polish")
builder.add_edge("polish", END)

# 7. 编译并执行
workflow = builder.compile()
result = workflow.invoke({"topic": "旅游"})
print("最终笑话：", result["joke"])