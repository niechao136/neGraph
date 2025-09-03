from fastapi import APIRouter
from pydantic import BaseModel
from db.db_helper import helper
from .jwt_helper import create_access_token


router = APIRouter()


# -----------------------------
# 请求模型
# -----------------------------
class UserRegister(BaseModel):
    username: str
    email: str | None = None
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    status: int
    error_msg: str | None = None


# -----------------------------
# 注册
# -----------------------------
@router.post("/register", response_model=TokenResponse)
async def register(user: UserRegister):
    user_id = await helper.register(username=user.username, password=user.password, email=user.email)
    if user_id is None:
        return {
            "status": 0,
            "error_msg": "Username already exists"
        }
    token = create_access_token({"user_id": str(user_id), "username": user.username})
    return {
        "status": 1,
        "access_token": token
    }


# -----------------------------
# 登录
# -----------------------------
@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin):
    user_id = await helper.login(username=user.username, password=user.password)
    if user_id is None:
        return {
            "status": 0,
            "error_msg": "Username or password is incorrect"
        }
    token = create_access_token({"user_id": str(user_id), "username": user.username})
    return {
        "status": 1,
        "access_token": token
    }
