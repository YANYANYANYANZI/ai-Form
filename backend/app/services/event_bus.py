import redis.asyncio as aioredis
import json
from backend.app.core.config import settings
from backend.app.api.v1.websockets import manager


async def listen_to_redis():
    """FastAPI 后台任务：监听 Redis 频道，收到消息就推给对应的 WebSocket"""
    # 连接 Redis
    redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = redis.pubsub()
    # 订阅频道
    await pubsub.subscribe("agent_results")

    print("📡 启动 Redis 事件总线监听...")
    async for message in pubsub.listen():
        if message["type"] == "message":
            # 收到消息，解析并推送
            data = json.loads(message["data"])
            client_id = data.get("client_id")
            content = data.get("content")
            if client_id and content:
                await manager.send_message(client_id, json.dumps(content))