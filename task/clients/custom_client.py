import json
import aiohttp
import requests

from task.clients.base import BaseClient
from task.constants import DIAL_ENDPOINT
from task.models.message import Message
from task.models.role import Role

class CustomDialClient(BaseClient):
    _endpoint: str
    _api_key: str

    def __init__(self, deployment_name: str, api_key: str):
        super().__init__(deployment_name)
        self._endpoint = DIAL_ENDPOINT + f"/openai/deployments/{deployment_name}/chat/completions"
        self._api_key = api_key

    def get_completion(self, messages: list[Message]) -> Message:
        # 1. Create headers dict with api-key and Content-Type
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json"
        }
        # 2. Create request_data dictionary
        request_data = {
            "messages": [msg.to_dict() for msg in messages]
        }
        # 3. Make POST request
        response = requests.post(
            self._endpoint,
            headers=headers,
            json=request_data
        )
        # 5. If status code != 200 then raise Exception
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        # 4. Get content from response, print it and return message
        resp_json = response.json()
        if not resp_json.get("choices"):
            raise Exception("No choices in response found")
        content = resp_json["choices"][0]["message"]["content"]
        print("Request:", json.dumps(request_data, indent=2))
        print("Response:", json.dumps(resp_json, indent=2))
        print(content)
        return Message(role=Role.ASSISTANT, content=content)

    async def stream_completion(self, messages: list[Message]) -> Message:
        # 1. Create headers dict
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json"
        }
        # 2. Create request_data dictionary
        request_data = {
            "stream": True,
            "messages": [msg.to_dict() for msg in messages]
        }
        # 3. Create empty list called 'contents'
        contents = []
        # 4. Create aiohttp.ClientSession()
        async with aiohttp.ClientSession() as session:
            # 5. Make POST request
            async with session.post(
                self._endpoint,
                json=request_data,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"HTTP {resp.status}: {text}")
                async for line in resp.content:
                    decoded_line = line.decode("utf-8").strip()
                    if decoded_line.startswith("data: "):
                        data = decoded_line[6:]
                        if data == "[DONE]":
                            break
                        snippet = self._get_content_snippet(data)
                        if snippet:
                            print(snippet, end="", flush=True)
                            contents.append(snippet)
        print()  # End of streaming
        full_content = "".join(contents)
        return Message(role=Role.ASSISTANT, content=full_content)

    def _get_content_snippet(self, data: str) -> str:
        # 1. Parse streaming data chunk
        try:
            chunk = json.loads(data)
            # 2. Extract content from chunk
            choices = chunk.get("choices")
            if choices and "delta" in choices[0] and "content" in choices[0]["delta"]:
                return choices[0]["delta"]["content"]
        except Exception as e:
            print(f"Error parsing chunk: {e}")
        return ""