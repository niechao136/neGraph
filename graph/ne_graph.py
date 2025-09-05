import asyncio
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage
from langchain_mcp_adapters.client import MultiServerMCPClient, StreamableHttpConnection
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph.message import add_messages
from functools import partial
from typing import Annotated
from typing_extensions import TypedDict
from .tool_node import BasicToolNode


load_dotenv()


client = MultiServerMCPClient({
    "amap": StreamableHttpConnection(transport="streamable_http", url="https://mcp.amap.com/mcp?key=e934d9201922156d80e7edddb504a2a6"),
})
tools = asyncio.run(client.get_tools())


llm = init_chat_model(
    model="qwen-plus-2025-07-14",
    model_provider="openai",
    api_key=os.getenv("ALIYUN_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)
llm_with_tools = llm.bind_tools(tools)


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


async def chatbot(state: State):
    message = await llm_with_tools.ainvoke(state["messages"])
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


class MyPostgresSaver(PostgresSaver):
    async def aget_tuple(self, config):
        """异步版本的 get_tuple"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.get_tuple, config)

    async def aput(self, config, checkpoint, metadata, new_versions):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.put, config, checkpoint, metadata, new_versions)

    async def aput_writes(self, config, writes, task_id: str, task_path: str = ''):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.put_writes, config, writes, task_id, task_path)

    async def adelete_thread(self, thread_id: str):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.delete_thread, thread_id)

    async def alist(self, config, *, filter = None, before = None, limit = 20):
        loop = asyncio.get_running_loop()
        func = partial(self.list, config, filter=filter, before=before, limit=limit)
        return await loop.run_in_executor(None, lambda: list(func()))


cm = MyPostgresSaver.from_conn_string("postgresql://root:158818@150.109.15.178:5432/neGraph")
postgres_saver = cm.__enter__()
postgres_saver.setup()
graph = graph_builder.compile(checkpointer=postgres_saver)
