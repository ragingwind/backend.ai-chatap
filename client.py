import asyncio
from aiohttp import ClientSession

import random
import string

MAX_CLIENTS = 3

def generate_client_id(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_random_message():
    messages = [
        "Hello there!",
        "How are you?",
        "Nice weather today",
        "What's up?",
        "Good morning!",
        "Testing, testing...",
        "Anyone here?",
    ]
    return random.choice(messages)

async def recv_messages(ws, client_id):
    while True:
        try:
            response = await ws.receive_str()
            command, resv_client_id, message = response.split('||')
            
            if command == 'msg':
                print(f"[{client_id}]>> {resv_client_id}: {message}")
            elif command == 'error':
                print(f"[{client_id}]>> Server error: {message}")
            else:
                print(f"[{client_id}]>> Unknown command: {command}")
        except Exception as e:
            print(f"[{client_id}]>> Error receiving message for client {resv_client_id}: {e}")
            break

async def send_messages(ws, client_id):
    while True:
        try:
            message = generate_random_message()
            await ws.send_str(f"msg||{client_id}||{message}")
            await asyncio.sleep(random.uniform(1, 5))
        except Exception as e:
            print(f"[{client_id}]>> Error sending message for client {client_id}: {e}")
            break

async def client_session():
    client_id = generate_client_id()
    print(f"[{client_id}]>> Conntecting to server")
    
    async with ClientSession() as session:
        async with session.ws_connect('http://localhost:3000/ws') as ws:
            await asyncio.gather(
                send_messages(ws, client_id),
                recv_messages(ws, client_id)
            )

async def main():# Number of simultaneous clients
    clients = [client_session() for _ in range(MAX_CLIENTS)]
    await asyncio.gather(*clients)

if __name__ == "__main__":
    asyncio.run(main())
