from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from backend.app.agents.reviewer import SQLReviewer
from backend.app.services.query_executor import executor
from backend.app.agents.workflow import app_workflow
# === 新增：引入数据库会话与模型 ===
from backend.app.core.database import get_db
from backend.app.models.schema import SheetData

router = APIRouter()

# --- 原有的 AI 对话与查询接口保持不变 ---
class SQLQuery(BaseModel):
    sql: str

@router.post("/query/")
def run_ai_sql(query: SQLQuery):
    is_safe, result = SQLReviewer.is_safe(query.sql)
    if not is_safe:
        raise HTTPException(status_code=403, detail=result)
    execute_result = executor.execute_sql(result)
    return {
        "original_sql": query.sql,
        "executed_sql": result,
        "engine_result": execute_result
    }

class ChatQuery(BaseModel):
    message: str


@router.post("/chat/")
def run_agent_workflow(query: ChatQuery):
    # 💡 核心魔法：把刚才上传的文档内容全部拼接，塞给大模型
    context = "\n\n".join([f"[{doc['filename']}]: {doc['content']}" for doc in global_knowledge_base])

    initial_state = {
        "user_query": query.message,
        "knowledge_context": context  # 将知识注入状态流
    }
    result_state = app_workflow.invoke(initial_state)

    return {
        "intent": result_state.get("intent"),
        "sheet_updates": result_state.get("sheet_updates"),
        "user_query": result_state.get("user_query"),
        "generated_sql": result_state.get("sql_query"),
        "echarts_config": result_state.get("bi_json"),
        "answer": result_state.get("answer")  # 将大模型的回答返回给前端
    }

# ==========================================
# === 新增：FortuneSheet 电子表格数据云端同步 API ===
# ==========================================

class SheetUpdateData(BaseModel):
    workspace_id: int
    sheet_name: str
    # celldata: List[Dict[str, Any]]  # 接收前端 FortuneSheet 极其复杂的单元格 JSON 数组
    celldata: list

@router.post("/sheet/save/")
def save_sheet_data(data: SheetUpdateData, db: Session = Depends(get_db)):
    """静默保存/更新表格数据 (供前端防抖调用)"""
    # 查找数据库中是否已有该表格
    sheet = db.query(SheetData).filter(
        SheetData.workspace_id == data.workspace_id,
        SheetData.sheet_name == data.sheet_name
    ).first()

    if sheet:
        # 如果存在，直接覆写 JSONB 字段
        sheet.celldata = data.celldata
    else:
        # 如果不存在，创建一条新记录
        sheet = SheetData(
            workspace_id=data.workspace_id,
            sheet_name=data.sheet_name,
            celldata=data.celldata
        )
        db.add(sheet)

    db.commit()
    return {"status": "success", "message": "表格数据已安全落盘到 PostgreSQL！"}

@router.get("/sheet/{workspace_id}/{sheet_name}")
def get_sheet_data(workspace_id: int, sheet_name: str, db: Session = Depends(get_db)):
    """拉取最新的表格数据 (供前端初始化页面调用)"""
    sheet = db.query(SheetData).filter(
        SheetData.workspace_id == workspace_id,
        SheetData.sheet_name == sheet_name
    ).first()

    if sheet:
        return {"status": "success", "celldata": sheet.celldata}
    else:
        # 如果还没建过表，返回空数组，让前端渲染白板
        return {"status": "empty", "celldata": []}


from backend.app.services.document_parser import extract_text_from_pdf

# 内存知识库（本节课为了尽量简单，我们先存在内存列表里，下节课再放进 Qdrant 向量库）
global_knowledge_base = []


@router.post("/upload/")
async def upload_document(file: UploadFile = File(...)):
    """接收前端上传的文件并解析"""
    content = await file.read()

    if file.filename.lower().endswith('.pdf'):
        text = extract_text_from_pdf(content)
        # 存入全局知识库（截取前3000字防爆）
        global_knowledge_base.append({
            "filename": file.filename,
            "content": text[:3000]
        })
        return {"status": "success", "filename": file.filename, "message": "📄 文件已成功解析并加入知识库！"}

    return {"status": "error", "message": "目前仅支持 PDF 文件哦！"}


@router.get("/knowledge/")
def get_knowledge_base():
    """获取当前知识库里的所有文件名"""
    return {"files": [doc["filename"] for doc in global_knowledge_base]}