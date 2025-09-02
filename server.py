import uvicorn
from typing import List, Optional, Any

from fastapi import FastAPI, Depends
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.postgres import PostgresSaver
from pydantic import BaseModel

from graph.ne_graph import graph, MyPostgresSaver
from graph.postgre_memory import helper
from auth import auth_router
from auth.jwt_helper import get_current_user

app = FastAPI()
# 将路由注册到主应用
app.include_router(auth_router.router, prefix="/auth", tags=["auth"])

# Graph 对象
saver: MyPostgresSaver = graph.checkpointer

# -----------------------------
# 请求/响应模型
# -----------------------------
class ChatStartRequest(BaseModel):
    summary: Optional[str] = None

class ChatSendRequest(BaseModel):
    conversation_id: str
    message: str

class ChatHistoryRequest(BaseModel):
    conversation_id: str

class MessageOut(BaseModel):
    content: str
    sender: str
    tool_calls: Optional[list] = []

class ChatSendResponse(BaseModel):
    messages: List[MessageOut]

class ChatHistoryResponse(BaseModel):
    messages: List[MessageOut]

class ChatListResponse(BaseModel):
    data: List[Any]
    limit: int
    has_more: bool

# -----------------------------
# 创建会话
# -----------------------------
@app.post("/chat/start")
async def start_chat(req: ChatStartRequest, current_user=Depends(get_current_user)):
    conversation_id = await helper.new_conversation(user_id=current_user["user_id"], summary=req.summary)
    return {"conversation_id": conversation_id}

# -----------------------------
# 发送消息
# -----------------------------
@app.post("/chat/send", response_model=ChatSendResponse)
async def send_message(req: ChatSendRequest, current_user=Depends(get_current_user)):
    config = {
        "configurable": {
            "thread_id": req.conversation_id,
            "user_id": current_user["user_id"]
        }
    }
    out_messages = []
    async for event in graph.astream(input={"messages": [("user", req.message)]}, config=config, stream_mode="values"):  # 简化写法
        for value in event.values():
            message = value[-1]
            if message.type == "ai":
                if message.content:
                    print("Assistant:", message.content)
                if hasattr(message, "tool_calls") and message.tool_calls:
                    print("Assistant called tool(s):", message.tool_calls)
            elif message.type == "tool":
                print("Tool call result:", message.content)
            out_messages.append(MessageOut(
                content=message.content,
                sender=message.type,
                tool_calls=message.additional_kwargs.get("tool_calls", [])
            ))
    return {"messages": out_messages}

# -----------------------------
# 获取历史消息
# -----------------------------
@app.get("/chat/history", response_model=ChatHistoryResponse)
async def chat_history(conversation_id: str, current_user=Depends(get_current_user)):
    state = await saver.aget({
        "configurable": {
            "thread_id": conversation_id,
            "user_id": current_user["user_id"]
        }
    }) or {"channel_values": {"messages": []}}
    out_messages = []
    for msg in state["channel_values"]["messages"]:
        out_messages.append(MessageOut(
            content=msg.content,
            sender="ai" if isinstance(msg, AIMessage) else "user",
            tool_calls=msg.additional_kwargs.get("tool_calls", [])
        ))
    return {"messages": out_messages}

# -----------------------------
# 列出会话
# -----------------------------
@app.get("/chat/list", response_model=ChatListResponse)
async def chat_list(limit = 10, before = None, current_user=Depends(get_current_user)):
    return await helper.conversation_list(user_id=current_user["user_id"], limit=limit, before=before)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10085)

