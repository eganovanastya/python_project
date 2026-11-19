import asyncio
import websockets
import json


async def test_connection():
    # ВАЖНО: замените PSVX4F на ваш реальный код, если он изменился
    room_code = "CT437I"
    username = "Оппа"
    uri = f"ws://127.0.0.1:8000/ws/{room_code}/{username}"

    print(f"Пытаюсь подключиться к комнате {room_code}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Успешно подключились!")
            # Ждем первого сообщения от сервера (список игроков)
            response = await websocket.recv()
            print(f"📩 Сообщение от сервера: {response}")

    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")


# Запуск
asyncio.run(test_connection())