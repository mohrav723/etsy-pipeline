# backend/src/services/bfl_api.py
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BFL_API_KEY = os.getenv("BFL_API_KEY")
if not BFL_API_KEY:
    raise ValueError("BFL_API_KEY not found in .env file.")

def generate_art_image(
    prompt: str,
    aspect_ratio: str,
    steps: int,
    guidance: float,
    seed: int,
    prompt_upsampling: bool,
    safety_tolerance: int
) -> bytes:
    """
    Handles the full end-to-end process of generating an image,
    using all the parameters from the job.
    """
    print("--- Starting image generation with custom parameters...")
    
    start_url = "https://api.bfl.ai/v1/flux-pro-1.1"
    headers = {"x-key": BFL_API_KEY, "Content-Type": "application/json"}
    
    sizes = {"16:9": (1344, 768), "1:1": (1024, 1024), "9:16": (768, 1344)}
    width, height = sizes.get(aspect_ratio, (1024, 1024))
    
    payload = {
        "prompt": prompt,
        "width": width,
        "height": height,
        "steps": steps,
        "guidance": guidance,
        "seed": seed,
        "prompt_upsampling": prompt_upsampling,
        "safety_tolerance": safety_tolerance,
        "output_format": "png"
    }

    initial_response = requests.post(start_url, json=payload, headers=headers)
    initial_response.raise_for_status()
    
    polling_url = initial_response.json().get("polling_url")
    if not polling_url:
        raise ValueError("Polling URL not found in API response.")
    print(f"--- Job started. Polling at: {polling_url}")

    # Polling logic remains the same
    for i in range(30):
        print(f"--- Polling attempt {i+1}...")
        poll_response = requests.get(polling_url, headers={"x-key": BFL_API_KEY})
        poll_response.raise_for_status()
        poll_data = poll_response.json()
        status = poll_data.get("status")

        if status == "Ready":
            final_url = poll_data.get("result", {}).get("sample")
            if not final_url:
                raise ValueError("Generation complete, but no final URL found.")
            print("--- Status is Ready! Downloading image...")
            image_response = requests.get(final_url)
            image_response.raise_for_status()
            print("--- Image downloaded successfully.")
            return image_response.content
        else:
            print(f"--- Status is '{status}'. Waiting 5 seconds...")
            time.sleep(5)
            
    raise Exception("Polling timed out.")