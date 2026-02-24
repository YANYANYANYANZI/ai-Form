from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB # 引入 PG 强大的 JSONB 类型
from sqlalchemy.sql import func
from backend.app.core.database import Base

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# === 新增：电子表格数据模型 ===
class SheetData(Base):
    __tablename__ = "sheet_data"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True) # 归属哪个工作区
    sheet_name = Column(String, nullable=False, default="Sheet1")
    # 核心：用 JSONB 存储 FortuneSheet 极其复杂的单元格结构
    # JSONB 在 PG 中支持高效的索引和局部更新
    celldata = Column(JSONB, nullable=False, server_default='[]')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())