import json
import uvicorn
from typing import List, Optional, Any

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import BaseMessage
from pydantic import BaseModel

from graph.ne_graph import graph, MyPostgresSaver
from db.db_helper import helper
from auth import auth_router
from auth.jwt_helper import get_current_user
from util.type import to_dict

app = FastAPI(root_path="/api")
# 将路由注册到主应用
app.include_router(auth_router.router, prefix="/auth", tags=["auth"])

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许访问的域名列表，["*"] 表示允许所有
    allow_credentials=True,  # 是否允许携带 cookie
    allow_methods=["*"],      # 允许的方法，例如 ["GET", "POST"]
    allow_headers=["*"],      # 允许的请求头
)

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
    stream: bool = True

class ChatHistoryRequest(BaseModel):
    conversation_id: str

class ChatSendResponse(BaseModel):
    messages: List[BaseMessage]

class ChatBlock(BaseModel):
    user: BaseMessage
    tool_calls: List[BaseMessage]
    tool_results: List[BaseMessage]
    assistant: BaseMessage

class ChatHistoryResponse(BaseModel):
    messages: List[ChatBlock]

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
    if not req.stream:
        out_messages = []
        async for event in graph.astream(input={"messages": [("user", req.message)]}, config=config, stream_mode="values"):  # 简化写法
            for value in event.values():
                message = value[-1]
                if message.type != "human":
                    out_messages.append(message)
        return {"messages": out_messages}

    # 流式模式（StreamingResponse + chunked JSON）
    async def event_generator():
        async for _event in graph.astream(input={"messages": [("user", req.message)]},config=config,stream_mode="values"):
            for _value in _event.values():
                _message = _value[-1]
                if getattr(_message, "type", None) != "human":
                    payload = to_dict(_message)
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        # SSE 结束标记
        yield "data: {\"done\":true}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

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
    history: List[ChatBlock] = []
    # 初始化一个空块
    block: dict | None = None

    for msg in state["channel_values"]["messages"]:
        if msg.type == "human":
            # 遇到用户消息，开始新对话块
            if block:
                # 上一个块结束，加入历史
                history.append(ChatBlock(**block))
            block = {
                "user": msg,
                "tool_calls": [],
                "tool_results": [],
                "assistant": None
            }
        elif msg.type == "ai":
            # AI 消息
            if msg.additional_kwargs.get("tool_calls"):
                block["tool_calls"].append(msg)
            else:
                block["assistant"] = msg
        elif msg.type == "tool":
            block["tool_results"].append(msg)

    # 最后一个块也加入
    if block:
        history.append(ChatBlock(**block))

    return {"messages": history}

# -----------------------------
# 列出会话
# -----------------------------
@app.get("/chat/list", response_model=ChatListResponse)
async def chat_list(limit = 10, before = None, current_user=Depends(get_current_user)):
    return await helper.conversation_list(user_id=current_user["user_id"], limit=limit, before=before)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10085)

