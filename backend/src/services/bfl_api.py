import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BFL_API_KEY = os.getenv("BFL_API_KEY")
if not BFL_API_KEY:
    raise ValueError("BFL_API_KEY not found in .env file.")

def generate_art_image(prompt: str, width: int = 1024, height: int = 768) -> bytes:

    print(f"--- Starting image generation for prompt: '{prompt[:50]}...'")
    
    start_url = "https://api.bfl.ai/v1/flux-dev"
    headers = {
        "x-key": BFL_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "width": width,
        "height": height,
        "steps": 28,
        "prompt_upsampling": False,
        "seed": -1,
        "guidance": 3,
        "safety_tolerance": 6,
        "output_format": "png"
    }

    initial_response = requests.post(start_url, json=payload, headers=headers)
    initial_response.raise_for_status()
    
    # 2. Get the polling URL from the initial response
    polling_url = initial_response.json().get("polling_url")
    if not polling_url:
        raise ValueError("Polling URL not found in API response.")
    print(f"--- Job started successfully. Polling at: {polling_url}")

    # 3. Poll the URL until the image is ready
    for i in range(30): # Poll for a maximum of 2.5 minutes
        print(f"--- Polling attempt {i+1}...")
        
        poll_response = requests.get(polling_url, headers={"x-key": BFL_API_KEY})
        poll_response.raise_for_status()
        poll_data = poll_response.json()
        status = poll_data.get("status")

        if status == "Ready":
            final_url = poll_data.get("result", {}).get("sample")
            if not final_url:
                raise ValueError("Generation complete, but no final image URL found.")

            print(f"--- Status is Ready! Downloading image from final URL...")
            
            # 4. Download the final image
            image_response = requests.get(final_url)
            image_response.raise_for_status()
            
            print("--- Image downloaded successfully.")
            return image_response.content
        
        else:
            print(f"--- Status is '{status}'. Waiting 5 seconds...")
            time.sleep(5)
            
    raise Exception("Polling timed out. Image took too long to generate.")