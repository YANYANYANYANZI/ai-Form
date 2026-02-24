import asyncio
import websockets
import urllib.request


async def test():
    # 1. 模拟前端建立 WebSocket 连接
    async with websockets.connect("ws://127.0.0.1:8000/ws/leron_001") as ws:
        print("✅ 1. 前端：WebSocket 连接成功！")

        # 2. 模拟前端点击按钮，发送 API 请求启动海冰预测任务
        print("⏳ 2. 前端：触发 UNet 预测任务，请等待 5 秒...")
        req = urllib.request.Request(
            "http://127.0.0.1:8000/api/v1/test-async/?task_name=UNet_Arctic_Ice_Prediction&client_id=leron_001",
            method="POST")
        urllib.request.urlopen(req)

        # 3. 前端什么都不做，纯等服务器的 WebSocket 主动推送
        result = await ws.recv()
        print(f"🎉 3. 前端：收到服务器零延迟主动推送: {result}")


asyncio.run(test())