from aiohttp import web
import redis.asyncio as redis
import aiotools
import os

port = 3000
ws_connections = set()

# FIXME: Make this dynamic
redis_key = f"room_{0}"
redis_client = redis.Redis()

async def init_redis():
    await redis_client.ping()
    await redis_client.delete(redis_key)

async def store_message(message):
    await redis_client.lpush(redis_key, message)

async def get_messages():
    if not await redis_client.exists(redis_key):
        return []
    return await redis_client.lrange(redis_key, 0, -1)

async def handle_websocket(request):
    print(f">> WebSocket connection from {request.remote} to {request.path}")
    ws = web.WebSocketResponse()
    ws_connections.add(ws)
    
    try:
        await ws.prepare(request)
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    command, client_id, message = msg.data.split('||')
                    print(f">> Received command: {command}, client_id: {client_id}, message: {message}")
                    
                    if command == 'connect':
                        messages = await get_messages()

                        for message in messages:
                            decoded_message = message.decode('utf-8')
                            await ws.send_str(decoded_message)

                            print(f">> Sending stored message to {client_id}: {decoded_message}")
                    elif command == 'msg':
                        message = f"msg||{client_id}||{message}"
                        await store_message(message)

                        for client in ws_connections:
                            await client.send_str(message)
                    else:
                        await ws.send_str(f"error||Unknown command: {command}")
                except ValueError:
                    await ws.send_str(f"error||Invalid message format. Use: command||client_id||message")
    finally:
        ws_connections.remove(ws)
        print(f">> WebSocket connection closed for {request.remote}")
    return ws

async def server_shutdown(app) -> None:
    print(f">> [{app['pidx']}] Shutting down server")
    for ws in set(ws_connections):  # Create a copy of the set
        try:
            await ws.close(code=1000, message=b'Server shutdown')
        except Exception as e:
            print(f"Error closing websocket: {e}")
    
    try:
        await redis_client.aclose()
        pass
    except Exception as e:
        print(f"Error closing Redis: {e}")
    
async def server_cleanup(app) -> None:
    pass

@aiotools.server
async def start_server(loop, pidx, args):
    await init_redis()

    app = web.Application()
    app.router.add_get('/ws', handle_websocket)
    app.router.add_get('/', lambda r: web.FileResponse('static/index.html'))
    app.on_shutdown.append(server_shutdown)
    app.on_cleanup.append(server_cleanup)
    app["pidx"] = pidx

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(
        runner,
        port=port,
        backlog=1024,
        reuse_port=True
    )
    await site.start()
    
    try:
        print(f">> [{pidx}] Started server")
        yield
    finally:
        print(f">> [{pidx}] Shutting down server")
        await runner.cleanup()

if __name__ == '__main__':
    aiotools.start_server(start_server, num_workers=min(4, os.cpu_count() or 1))
