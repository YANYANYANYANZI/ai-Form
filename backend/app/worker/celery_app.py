from celery import Celery
import time
import redis
import json

celery_app = Celery("ai_form_worker", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0")

# ===================== 新增配置（仅这部分，消除版本警告）=====================
celery_app.conf.update(
    # 核心：解决broker_connection_retry的弃用警告，不影响原有功能
    broker_connection_retry_on_startup=True,
    # 以下为常规默认配置，可选添加（保证序列化一致性，避免潜在问题）
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",  # 可选，按自己的时区配置
    enable_utc=True,
)
# ============================================================================

# 同步 Redis 客户端，用于发布消息
redis_client = redis.from_url("redis://localhost:6379/0", decode_responses=True)


@celery_app.task(name="dummy_ai_task")
def dummy_ai_task(task_name: str, client_id: str = "test_user"):
    print(f"[{task_name}] 开始执行...")
    time.sleep(5)  # 模拟 FNO 模型计算耗时
    result = f"Task '{task_name}' completed!"

    # === 完工后广播 ===
    message = {
        "client_id": client_id,
        "content": {"task": task_name, "result": result, "status": "success"}
    }
    redis_client.publish("agent_results", json.dumps(message))
    print(f"[{task_name}] 结果已广播到 Redis！")

    return result