import requests
import psutil
import json
import time

# Base URL for Ollama API
BASE_URL = "http://localhost:11434/api"
MODEL    = "ghost"

def generate_response(prompt, model_name=MODEL, stream=False, custom_params=None):
    """
    Generate a response from the Ollama model using parameters defined in the Modelfile.
    
    Args:
        prompt (str): The input prompt
        model_name (str): Name of your model in Ollama
        stream (bool): Whether to stream the response
        custom_params (dict): Optional parameters to override Modelfile settings
    
    Returns:
        dict: The models response
    """
    url = f"{BASE_URL}/generate"
    
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": stream
    }
    
    if custom_params:
        payload["options"] = custom_params
    
    if stream:
        response = requests.post(url, json=payload, stream=True)
        response.raise_for_status()
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                json_response = json.loads(line)
                chunk = json_response.get("response", "")
                full_response += chunk
                print(chunk, end="", flush=True)
                
                # Check if response is complete
                if json_response.get("done", False):
                    print("\n")
                    return {"response": full_response, "metrics": json_response.get("metrics", {})}
    else:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()

def system_usage():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_use = psutil.virtual_memory().percent
    
    return {
        "timestamp": time.time(),
        "cpu_percent": cpu_percent,
        "memory_percent": memory_use
    }

if __name__ == "__main__":
    pre_metrics = system_usage()
    print(f"System before request: CPU {pre_metrics['cpu_percent']}%, Memory {pre_metrics['memory_percent']}%")

    start_time = time.time()
    response = generate_response(
        "What is white but has red eyes?", 
        model_name=MODEL,
        stream=True
    )
    end_time = time.time()
    
    post_metrics = system_usage()
    print(f"System after request: CPU {post_metrics['cpu_percent']}%, Memory {post_metrics['memory_percent']}%")