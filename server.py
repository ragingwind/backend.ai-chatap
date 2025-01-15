from aiohttp import web

port = 3000
ws_connections = set()

async def handle_websocket(request):
    print(f"WebSocket connection from {request.remote} to {request.path}")
    ws = web.WebSocketResponse()
    ws_connections.add(ws)
    
    try:
        await ws.prepare(request)
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                print(f"WebSocket message received from {request.remote}: {msg.data}")
                for client in ws_connections:
                    if (client != ws):
                        await client.send_str(msg.data)
    finally:
        ws_connections.remove(ws)
        print(f"WebSocket connection closed for {request.remote}")
    return ws

app = web.Application()

app.router.add_get('/ws', handle_websocket)
app.router.add_get('/', lambda r: web.FileResponse('static/index.html'))

print("Starting server on port {port}")
web.run_app(app, port=port)

