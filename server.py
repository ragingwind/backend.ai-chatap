from aiohttp import web

async def handle_websocket(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            await ws.send_str(msg.data)
            print(f"Received message: {msg.data}")
    return ws

app = web.Application()
app.router.add_get('/ws', handle_websocket)

web.run_app(app, port=8080)   