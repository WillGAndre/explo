#!/usr/bin/env python3

def xor(data: bytes, key: str) -> bytes:
    """XOR encode/decode with repeating key"""
    key_bytes = key.encode()
    return bytes([b ^ key_bytes[i % len(key_bytes)] for i,b in enumerate(data)])