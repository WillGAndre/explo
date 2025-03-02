.PHONY: pull build run clean

SRC := prompt
ENV := .venv
#--------------------------------------------------
MODEL := ghost
BASEM := hf.co/ghost-x/ghost-8b-beta-1608-gguf:Q4_0 # https://huggingface.co/ghost-x/ghost-8b-beta-1608-gguf

# Pull Modelfile
pull:
	@ollama create $(MODEL) -f Modelfile
	@ollama rm $(BASEM)
	@ollama list
	@ollama show $(MODEL)
#ollama run $(MODEL)

# Setup the virtual environment, install dependencies, and run the script
build:
	@if [ -d "$(ENV)" ]; then rm -rf $(ENV); fi
	@python3 -m venv $(ENV)
	@. $(ENV)/bin/activate; pip3 install -r requirements.txt; python3 $(SRC).py

# Run the script using the virtual environment
run:
	@if [ -d "$(ENV)" ]; then \
		. $(ENV)/bin/activate; python3 $(SRC).py; \
	fi

clean:
	@rm -rf $(ENV)
	@ollama rm $(MODEL)

