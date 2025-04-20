.PHONY: all target
all:
	@clang -shared -fPIC -o core.dylib core.c
	@./clib.py

target:
	@docker build -t erlang-ssh-server .
	@docker run -it -p 2222:2222 erlang-ssh-server