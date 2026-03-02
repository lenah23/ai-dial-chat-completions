# task/clients/client.py

import aiohttp
from typing import AsyncGenerator
from task.models.message import Message

class DialClient:
    def __init__(self, model: str, api_key: str = None):
        self.model = model
        self.api_key = api_key  # You may want to load this from constants or env

    async def stream_completion(self, messages: list[Message]) -> AsyncGenerator[str, None]:
        url = f"https://ai-proxy.lab.epam.com/openai/deployments/{self.model}/chat/completions"
        headers = {
            "api-key": self.api_key, 
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "stream": True
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                async for line in resp.content:
                    # Each line is a bytes object, decode it
                    line = line.decode("utf-8").strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    # Parse the JSON and extract the content chunk
                    import json
                    try:
                        chunk = json.loads(data)
                        content = chunk["choices"][0]["delta"].get("content", "")
                        if content:
                            yield content
                    except Exception:
                        continue