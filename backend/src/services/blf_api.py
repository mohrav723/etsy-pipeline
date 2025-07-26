import os
import requests
from dotenv import load_dotenv

load_dotenv()

BFL_API_KEY = os.getenv("BFL_API_KEY")
if not BFL_API_KEY:
    raise ValueError("BFL_API_KEY not found in .env file. Please add it.")

def generate_art_image(prompt: str, width: int = 1024, height: int = 1024) -> bytes:

    print(f"--- Calling BFL API for prompt: '{prompt[:50]}...'")
    
    api_url = "https://api.bfl.ai/v1/flux-dev"
    
    payload = {
        "prompt": prompt,
        "width": width,
        "height": height,
        "output_format": "png",
        "prompt_upsampling": False,
        "seed": 42,
        "guidance": 3,
        "safety_tolerance": 6
    }

    headers = {
        "x-key": BFL_API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.post(api_url, json=payload, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"BFL API Error: {response.status_code} - {response.text}")

    # print("--- Image data received successfully from BFL API.")
    print(response.json())
    return response.content