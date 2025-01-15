import asyncio
from aiohttp import ClientSession

async def connect_to_server():
    async with ClientSession() as session:
        async with session.ws_connect('http://localhost:8080/ws') as ws:
            while True:
                message = input("Enter message (or 'quit' to exit): ")
                if message.lower() == 'quit':
                    break
                
                await ws.send_str(message)
                response = await ws.receive_str()
                print(f"Server response: {response}")

if __name__ == "__main__":
    asyncio.run(connect_to_server())
