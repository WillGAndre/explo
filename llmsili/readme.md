# LLM on Silicon (Darwin M1)

## Requirements

- (macOS) Apple Silicon M1
- [Ollama](https://ollama.ai/download)
- [ghost-8b-beta-1608-gguf:Q4_0](https://huggingface.co/ghost-x/ghost-8b-beta-1608-gguf) / 4.7GB
- 16GB RAM

## Installation

1. Install [Ollama](https://ollama.ai/download)

2. Create the model using the optimized Modelfile:
   ```bash
   make pull
   ```

3. Install and run prompt:
   ```bash
   make build
   ```

## Usage

### Basic Usage

Run the model with default parameters:

```bash
make run
```

### Custom Parameters

You can override model parameters at runtime:

```python
response = generate_response(
    "Summarize the benefits of Apple Silicon",
    custom_params={
        "temperature": 0.5,
        "num_predict": 2048
    }
)
```

## Configuration

The model is configured in the [`Modelfile`](./Modelfile).

## Performance Tuning

```
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER min_p 0.05
PARAMETER repeat_penalty 1.2
PARAMETER repeat_last_n 128
PARAMETER num_ctx 4096
PARAMETER num_predict 4096
PARAMETER num_thread 7
```

### Memory Usage

Ghost-8B as a memory footprint:
- Model weights: ~4GB with Q4_0 quantization (instead of 16-32GB unquantized)
- Context window (2048 tokens): ~250-500MB additional memory
- Total runtime memory: ~4.5-5GB

## Makefile Commands

- `make pull`: Create the model using the Modelfile
- `make build`: Set up Python environment and install dependencies
- `make run`: Run the example script
- `make clean`: Remove the model and virtual environment

## Acknowledgements

- [Ollama](https://ollama.ai/) for making local LLMs accessible
- [Ghost-8B](https://huggingface.co/ghost-x/ghost-8b-beta-1608-gguf) model