import uvicorn
from typing import List, Optional

from fastapi import FastAPI, Depends
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel

from graph.ne_graph import graph
from graph.postgre_memory import PostgresSaver
from auth import auth_router
from auth.jwt_helper import get_current_user

app = FastAPI()
# 将路由注册到主应用
app.include_router(auth_router.router, prefix="/auth", tags=["auth"])

# Graph 对象
saver: PostgresSaver = graph.checkpointer

# -----------------------------
# 请求/响应模型
# -----------------------------
class ChatStartRequest(BaseModel):
    summary: Optional[str] = None

class ChatSendRequest(BaseModel):
    conversation_id: str
    message: str

class MessageOut(BaseModel):
    content: str
    sender: str
    tool_calls: Optional[list] = []

class ChatSendResponse(BaseModel):
    messages: List[MessageOut]

class ChatHistoryResponse(BaseModel):
    messages: List[MessageOut]

class ChatListResponse(BaseModel):
    conversations: List[dict]

# -----------------------------
# 创建会话
# -----------------------------
@app.post("/chat/start")
async def start_chat(req: ChatStartRequest, current_user=Depends(get_current_user)):
    conversation_id = await saver.new_conversation(user_id=current_user["user_id"], summary=req.summary)
    return {"conversation_id": conversation_id}

# -----------------------------
# 发送消息
# -----------------------------
@app.post("/chat/send", response_model=ChatSendResponse)
async def send_message(req: ChatSendRequest, current_user=Depends(get_current_user)):
    # 1. 恢复历史消息
    state = await saver.get({
        "thread_id": req.conversation_id,
        "user_id": current_user["user_id"]
    }) or {"values": {"messages": []}}
    messages = state["values"]["messages"]

    # 2. 添加用户消息
    user_msg = HumanMessage(content=req.message)
    messages.append(user_msg)

    # 3. 运行 Graph
    checkpoint = await graph.invoke({"messages": messages}, config={
        "thread_id": req.conversation_id,
        "user_id": current_user["user_id"]
    })

    # 4. 保存 checkpoint
    await saver.put({
        "thread_id": req.conversation_id,
        "user_id": current_user["user_id"]
    }, checkpoint)

    # 5. 返回最新消息
    out_messages = []
    for msg in checkpoint["values"]["messages"][-1:]:
        out_messages.append(MessageOut(
            content=msg.content,
            sender="ai" if isinstance(msg, AIMessage) else "user",
            tool_calls=msg.additional_kwargs.get("tool_calls", [])
        ))
    return {"messages": out_messages}

# -----------------------------
# 获取历史消息
# -----------------------------
@app.get("/chat/history", response_model=ChatHistoryResponse)
async def chat_history(conversation_id: str, current_user=Depends(get_current_user)):
    state = await saver.get({
        "thread_id": conversation_id,
        "user_id": current_user["user_id"]
    }) or {"values": {"messages": []}}
    out_messages = []
    for msg in state["values"]["messages"]:
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
async def chat_list(current_user=Depends(get_current_user)):
    conversations = await saver.list({"user_id": current_user["user_id"]})
    return {"conversations": conversations}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10085)

