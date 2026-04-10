from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

from langgraph_agent.app.langgraph_agent.agent import llm


# 1. 定义状态结构
class ParallelState(TypedDict):
    prompt: str
    result_1: str
    result_2: str
    result_3: str
    final_result: str

# 2. 定义并行节点（多个独立 LLM 调用）
def call_llm_1(state: ParallelState) -> ParallelState:
    res = llm.invoke(f"从技术角度回答：{state['prompt']}")
    return {"result_1": res.content}

def call_llm_2(state: ParallelState) -> ParallelState:
    res = llm.invoke(f"从应用角度回答：{state['prompt']}")
    return {"result_2": res.content}

def call_llm_3(state: ParallelState) -> ParallelState:
    res = llm.invoke(f"从未来趋势角度回答：{state['prompt']}")
    return {"result_3": res.content}

# 3. 结果聚合节点
def aggregate(state: ParallelState) -> ParallelState:
    final = f"技术视角：{state['result_1']}\n\n应用视角：{state['result_2']}\n\n趋势视角：{state['result_3']}"
    return {"final_result": final}

# 4. 构建工作流（并行执行 3 个 LLM 调用）
builder = StateGraph(ParallelState)
builder.add_node("llm1", call_llm_1)
builder.add_node("llm2", call_llm_2)
builder.add_node("llm3", call_llm_3)
builder.add_node("aggregate", aggregate)

# 5. 并行连接：入口节点同时触发 3 个 LLM 节点
builder.add_edge(START, "llm1")
builder.add_edge(START, "llm2")
builder.add_edge(START, "llm3")

# 6. 所有并行节点完成后聚合
builder.add_edge("llm1", "aggregate")
builder.add_edge("llm2", "aggregate")
builder.add_edge("llm3", "aggregate")
builder.add_edge("aggregate", END)

# 7. 执行
workflow = builder.compile()
result = workflow.invoke({"prompt": "什么是人工智能？"})
print("聚合结果：", result["final_result"])