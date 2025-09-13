#!/usr/bin/env python3

import sys
import tty
import asyncio
import termios

original_term_settings = termios.tcgetattr(sys.stdin)
interactive_triggered = asyncio.Event()


def keyboard_listener(loop):
    fd = sys.stdin.fileno()
    try:
        tty.setcbreak(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch.lower() == 'm':
                loop.call_soon_threadsafe(interactive_triggered.set)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, original_term_settings)

# Coroutine to set the event that triggers prompt
async def trigger_interactive_mode():
    interactive_triggered.set()


def prompt_selection(title, options_dict):
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_term_settings)

    print(f"\n{title}")
    for k, v in options_dict.items():
        print(f"{k}: {v}")
    while True:
        choice = input("Enter your choice: ").strip()
        if choice in options_dict:
            return options_dict[choice]
        else:
            print("Invalid choice.")
        

async def exec_module(session, enc_fn: callable):
    if not session.agents:
        print("No agents available.")
        return
    
    agent_options = {str(i + 1): a for i, a in enumerate(session.agents)}
    config_options = {str(i + 1): a for i, a in enumerate(session.mdl_config)}
    agent_id = prompt_selection("Select an agent ID:", agent_options)
    config_path = prompt_selection("Select a config:", config_options)

    print(f"[!] Running config '{config_path}' on agent '{agent_id}'")
    await session.exec_mdl(config_path, agent_id, enc_fn=enc_fn)