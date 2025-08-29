import asyncio
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage
from langchain_mcp_adapters.client import MultiServerMCPClient, StreamableHttpConnection
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import Annotated
from typing_extensions import TypedDict
from .tool_node import BasicToolNode
from .postgre_memory import PostgresSaver


load_dotenv()


client = MultiServerMCPClient({
    "amap": StreamableHttpConnection(transport="streamable_http", url="https://mcp.amap.com/mcp?key=e934d9201922156d80e7edddb504a2a6"),
})
tools = asyncio.run(client.get_tools())


llm = init_chat_model(
    model="qwen-max",
    model_provider="openai",
    api_key=os.getenv("ALIYUN_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)
llm_with_tools = llm.bind_tools(tools)


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def chatbot(state: State):
    message = asyncio.run(llm_with_tools.ainvoke(state["messages"]))
    assert len(message.tool_calls) <= 1
    return {
        "messages": [message]
    }
tool_node = BasicToolNode(tools=tools)
def route_tools(state: State):
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route to the end.
    """
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return END


graph_builder = StateGraph(State) # type: ignore
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)
graph_builder.add_conditional_edges("chatbot", route_tools, {"tools": "tools", END: END})
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")


postgres_saver = PostgresSaver(dsn="postgresql://root:158818@150.109.15.178:5432/neGraph")
graph = graph_builder.compile(checkpointer=postgres_saver)
