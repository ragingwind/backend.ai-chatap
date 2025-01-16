import redis.asyncio as redis

class RedisClient:
    _client = None

    def __init__(self, name):
        self.name = name

    async def connect(self):
        self._client = await redis.Redis()

    async def close(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def delete_messages(self):
        await self._client.delete(self.name)

    async def push_message(self, message):
        await self._client.lpush(self.name, message)

    async def get_messages(self):
        if not await self._client.exists(self.name):
            return []
        messages = await self._client.lrange(self.name, 0, -1)
        return [message.decode('utf-8') for message in messages]
    
