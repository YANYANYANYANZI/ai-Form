from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.core.config import settings

# 创建数据库引擎
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)

# 创建会话工厂，用于操作数据库
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 所有数据表模型的基类
Base = declarative_base()

# 依赖注入：为每个请求提供独立的数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()