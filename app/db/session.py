from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import Pool

from app.core.config import get_settings

settings = get_settings()

# 优化的数据库引擎配置
engine = create_engine(
    str(settings.database_url),
    # 连接池配置
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
    pool_timeout=30,  # 获取连接超时时间（秒）
    pool_recycle=3600,  # 连接回收时间（秒），防止连接过期
    pool_pre_ping=True,  # 使用前ping检查连接有效性
    # 性能优化
    echo=settings.debug,  # 开发环境显示SQL
    echo_pool=False,  # 连接池日志
    # 连接参数
    connect_args={
        "connect_timeout": 10,  # 连接超时
        "options": "-c timezone=utc",  # 设置时区
    },
)


# 连接池事件监听 - 用于调试和监控
@event.listens_for(Pool, "connect")
def set_search_path(dbapi_connection, connection_record):
    """在新连接时设置schema搜索路径"""
    # 可以在这里添加连接级别的配置
    pass


@event.listens_for(Pool, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """连接从池中取出时触发"""
    # 可以在这里记录连接使用情况
    pass


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
