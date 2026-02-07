.PHONY: linux-amd64 linux-arm64 windows-amd64 darwin-arm64 cross clean

BIN=lock
LDFLAGS=-s -w

linux-amd64:
	GOOS=linux GOARCH=amd64 go build -ldflags="$(LDFLAGS)" -o $(BIN)-linux-amd64 $(BIN).go
	upx --best --lzma $(BIN)-linux-amd64

linux-arm64:
	GOOS=linux GOARCH=arm64 go build -ldflags="$(LDFLAGS)" -o $(BIN)-linux-arm64 $(BIN).go
	upx --best --lzma $(BIN)-linux-arm64

windows-amd64:
	GOOS=windows GOARCH=amd64 go build -ldflags="$(LDFLAGS)" -o $(BIN)-windows-amd64.exe $(BIN).go
	upx --best --lzma $(BIN)-windows-amd64.exe

# upx will break the binary in darwin (https://github.com/upx/upx/issues/612)
darwin-arm64:
	GOOS=darwin GOARCH=arm64 go build -ldflags="$(LDFLAGS)" -o $(BIN)-darwin-arm64 $(BIN).go

cross: linux-amd64 linux-arm64 windows-amd64 darwin-arm64

clean:
	@rm -f $(BIN) $(BIN)-*