import asyncio
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.database import engine, Base, get_db
from backend.app.models.schema import Workspace
from pydantic import BaseModel

# --- 引入新写的模块 ---
from backend.app.worker.celery_app import dummy_ai_task
from backend.app.api.v1.websockets import router as ws_router
from backend.app.services.event_bus import listen_to_redis
# ⚠️ 就是缺了下面这一行，导致找不到 api_router！
from backend.app.api.v1.endpoints import router as api_router

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时开启后台任务：监听 Redis
    task = asyncio.create_task(listen_to_redis())
    yield
    # 关闭时取消任务
    task.cancel()

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# --- 挂载路由 ---
app.include_router(ws_router)
app.include_router(api_router, prefix=settings.API_V1_STR)

# === 新增：CORS 跨域资源共享配置 ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有前端来源访问
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法 (GET, POST等)
    allow_headers=["*"],  # 允许所有请求头
)



class WorkspaceCreate(BaseModel):
    name: str
    description: str = None

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post(f"{settings.API_V1_STR}/workspaces/")
def create_workspace(workspace: WorkspaceCreate, db: Session = Depends(get_db)):
    db_workspace = Workspace(name=workspace.name, description=workspace.description)
    db.add(db_workspace)
    db.commit()
    db.refresh(db_workspace)
    return db_workspace

@app.post(f"{settings.API_V1_STR}/test-async/")
def run_async_task(task_name: str, client_id: str = "test_user"):
    task = dummy_ai_task.delay(task_name, client_id)
    return {"task_id": task.id, "status": "后台计算中..."}