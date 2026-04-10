import os
from typing import Annotated, List, Literal

from langchain_core.tools import create_retriever_tool
from langchain_openai import OpenAIEmbeddings
from typing_extensions import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek

load_dotenv()


# --- 1. 初始化向量数据库检索器 ---
def get_retriever():
    """加载已创建的向量数据库"""
    embeddings = OpenAIEmbeddings()
    # vectorstore = Chroma(
    #     persist_directory="./chroma_db",
    #     embedding_function=embeddings
    # )
    # 每次检索返回最相关的3个文档块[reference:13]
    # return vectorstore.as_retriever(search_kwargs={"k": 3})
    return None


# 创建检索工具
retriever = get_retriever()
retrieval_tool = create_retriever_tool(
    retriever,
    name="search_local_documents",
    description="Searches and returns relevant excerpts from local documents. Use this for any question that might be answered by the content in your workspace.",
)

tools = [retrieval_tool]


# --- 2. 定义Agent状态 ---
# 使用 MessagesState，它会自动将新的消息追加到历史中[reference:14]
class AgentState(MessagesState):
    # 可以在这里添加自定义字段，例如 'steps' 用于限制循环次数
    pass


# --- 3. 初始化LLM并绑定工具 ---
llm = ChatDeepSeek(
    model="deepseek-chat",  # DeepSeek-V3 模型
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key='sk-a6b3b995625a4f1b99b232b8a8c6838b',
    # api_base="https://api.deepseek.com/anthropic"
    # api_key=os.getenv("DEEPSEEK_API_KEY")  # 从环境变量读取
)
llm_with_tools = llm.bind_tools(tools)


# --- 4. 定义节点函数 ---
def call_model(state: AgentState):
    """智能体节点：调用LLM进行推理和决策"""
    response = llm_with_tools.invoke(state["messages"])
    # 将LLM的响应添加到消息历史中
    return {"messages": [response]}


# 条件路由函数：决定下一步是进入工具节点还是直接结束
def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]
    # 如果LLM发出了工具调用请求，则路由到 'tools' 节点
    if last_message.tool_calls:
        return "tools"
    # 否则，结束流程
    return "__end__"


# --- 5. 构建图 ---
# 创建一个状态图，起始状态类型为 AgentState
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("agent", call_model)  # 智能体节点
workflow.add_node("tools", ToolNode(tools))  # 工具节点，负责执行具体的工具调用

# 添加边
workflow.add_edge(START, "agent")  # 设置起始节点为 'agent'
workflow.add_conditional_edges("agent", should_continue)  # 在 'agent' 后根据条件路由
workflow.add_edge("tools", "agent")  # 执行完工具后，回到 'agent' 进行下一步推理

# --- 6. 编译并添加内存 ---
# MemorySaver 用于在对话线程中持久化状态，实现短期记忆[reference:15]
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)


# --- 7. 交互循环 ---
def main():
    print("Local RAG Agent is ready! Type 'exit' to quit.")
    # 配置一个线程ID，用于保持同一对话的上下文记忆
    config = {"configurable": {"thread_id": "1"}}
    while True:
        user_input = input("\nUser: ")
        if user_input.lower() == "exit":
            break

        # 将用户输入包装成消息格式，并调用Agent
        messages = [{"role": "user", "content": user_input}]
        for event in app.stream({"messages": messages}, config, stream_mode="values"):
            # 打印Agent最后的响应
            event["messages"][-1].pretty_print()


if __name__ == "__main__":
    main()
