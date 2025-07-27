import sys
import os
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.services.bfl_api import generate_art_image

def run_test():

    sample_prompt = "A quiet, forgotten corner of a Parisian library in late afternoon, shafts of golden sunlight streaming through a tall, arched window and illuminating dust motes dancing in the air, impressionist style."
    
    try:
        image_data = generate_art_image(prompt=sample_prompt, width=1344, height=768)
        image_name = f"test_output_{uuid.uuid4()}.png"
        with open(image_name, "wb") as f:
            f.write(image_data)
            
        print(f"\n--- SUCCESS! Image saved as {image_name}. ---")
    except Exception as e:
        print(f"--- ERROR: The API call failed. Details: {e}")

if __name__ == "__main__":
    run_test()