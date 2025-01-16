from aiohttp import web
import aiotools
import os
from redis_client import RedisClient

async def handle_websocket(request):
    ws = web.WebSocketResponse()
    app = request.app    
    app["connections"].add(ws)

    print(f">> [{app['pidx']}] WebSocket connection from {request.remote} to {request.path}")

    try:
        await ws.prepare(request)
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    command, client_id, message = msg.data.split('||')
                    print(f">> [{app['pidx']}] Msg: {command}, client_id: {client_id}, message: {message}")
                    
                    if command == 'connect':
                        for message in await app["redis"].get_messages():
                            await ws.send_str(message)
                    elif command == 'msg':
                        message = f"msg||{client_id}||{message}"
                        await app["redis"].push_message(message)

                        for client in app["connections"]:
                            await client.send_str(message)
                    else:
                        await ws.send_str(f"error||Unknown command: {command}")
                except ValueError:
                    await ws.send_str(f"error||Invalid message format. Use: command||client_id||message")
    finally:
        app["connections"].remove(ws)
        print(f">> [{app['pidx']}] WebSocket connection closed for {request.remote}")
    return ws

async def server_shutdown(app) -> None:
    print(f">> [{app['pidx']}] Shutting down server")

    for ws in set(app["connections"]):
        try:
            await ws.close(code=1000, message=b'Server shutdown')
        except Exception as e:
            print(f">> [{app['pidx']}]Error closing websocket: {e}")
    
    try:
        await app["redis"].close()
        pass
    except Exception as e:
        print(f">> [{app['pidx']}] Error closing Redis: {e}")
    
async def server_cleanup(app) -> None:
    pass

@aiotools.server
async def start_server(loop, pidx, args):
    app = web.Application()

    app["pidx"] = pidx
    app["connections"] = set()
    app["redis"] = RedisClient(args[0])

    await app["redis"].connect()

    if pidx == 0:
        await app["redis"].delete_messages()

    app.router.add_get('/ws', handle_websocket)
    app.router.add_get('/', lambda r: web.FileResponse('static/index.html'))
    app.on_shutdown.append(server_shutdown)
    app.on_cleanup.append(server_cleanup)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(
        runner,
        port=3000,
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
    aiotools.start_server(
        start_server, 
        num_workers=min(4, os.cpu_count() or 1),
        args=('chatapp',))
