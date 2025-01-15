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
                try:
                    command, client_id, message = msg.data.split('||')
                    print(f"Received command: {command}, client_id: {client_id},message: {message}")
                    
                    if command == 'msg':
                        for client in ws_connections:
                            await client.send_str(f"msg||{client_id}||{message}")
                    else:
                        await ws.send_str(f"error||Unknown command: {command}")
                except ValueError:
                    await ws.send_str(f"error||Invalid message format. Use: command||client_id||message")
    finally:
        ws_connections.remove(ws)
        print(f"WebSocket connection closed for {request.remote}")
    return ws

app = web.Application()

app.router.add_get('/ws', handle_websocket)
app.router.add_get('/', lambda r: web.FileResponse('static/index.html'))

print("Starting server on port {port}")
web.run_app(app, port=port)

