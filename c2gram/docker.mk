.PHONY: build-c build-a purge controller agent

build-c:
	@docker build -t controller -f controller/Dockerfile .

build-a:
	@docker build -t agent -f agent/Dockerfile .

purge:
	@rm -rf .env.a

controller:
	@touch .env.a
	@docker run --rm -it \
		--env-file .env.c \
		-v $(PWD)/.env.a:/opt/.env.a \
		$@

agent:
	@docker run --rm -it \
		--env-file .env.a \
		$@