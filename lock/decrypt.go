package main

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
)

var (
	keyFlag  = flag.String("key", "", "decryption passphrase")
	dataFlag = flag.String("data", "", "base64 encrypted data (or use stdin)")
	fileFlag = flag.String("file", "", "JSON file from webhook containing 'd' field")
)

func deriveKey(pass string) []byte {
	h := sha256.Sum256([]byte(pass))
	return h[:]
}

func decrypt(ciphertext string, key []byte) ([]byte, error) {
	data, err := base64.StdEncoding.DecodeString(ciphertext)
	if err != nil {
		return nil, err
	}

	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, err
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}

	nonceSize := gcm.NonceSize()
	if len(data) < nonceSize {
		return nil, fmt.Errorf("ciphertext too short")
	}

	nonce, ciphertextBytes := data[:nonceSize], data[nonceSize:]
	return gcm.Open(nil, nonce, ciphertextBytes, nil)
}

func main() {
	flag.Parse()

	if *keyFlag == "" {
		log.Fatal("Usage: decrypt -key <passphrase> [-data <base64> | -file <path>]")
	}

	var encrypted string

	if *fileFlag != "" {
		content, err := os.ReadFile(*fileFlag)
		if err != nil {
			log.Fatalf("Failed to read file: %v", err)
		}
		var wrapper map[string]string
		if err := json.Unmarshal(content, &wrapper); err != nil {
			log.Fatalf("Failed to parse JSON: %v", err)
		}
		encrypted = wrapper["d"]
	} else if *dataFlag != "" {
		encrypted = *dataFlag
	} else {
		log.Fatal("Provide -data or -file")
	}

	key := deriveKey(*keyFlag)
	plaintext, err := decrypt(encrypted, key)
	if err != nil {
		log.Fatalf("Decryption failed: %v", err)
	}

	var pretty map[string]interface{}
	if err := json.Unmarshal(plaintext, &pretty); err == nil {
		out, _ := json.MarshalIndent(pretty, "", "  ")
		fmt.Println(string(out))
	} else {
		fmt.Println(string(plaintext))
	}
}
