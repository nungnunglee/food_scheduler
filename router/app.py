from fastapi import FastAPI
import uvicorn
from user.user_router import user_router
from food.food_router import food_router
from agent.agent_router import agent_router

app = FastAPI(
    title="AI Agent API",
    description="AI Agent API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.include_router(user_router)
app.include_router(food_router)
app.include_router(agent_router)

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)