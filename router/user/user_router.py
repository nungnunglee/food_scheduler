from fastapi import APIRouter

user_router = APIRouter(prefix="/user", tags=["user"])

@user_router.get("/list")
async def get_user_list():
    return {"message": "Hello, World!"}