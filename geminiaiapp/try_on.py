import os
from PIL import Image
from google import genai
from google.genai import types
from datetime import datetime
from .config import MODEL,api_key,resolution,generated_images_dir
from .prompts import try_on_prompt
from .utils import optimize_for_nano_banana 

class VirtualTryOn:
    def __init__(self, model=None):
        self.client = genai.Client(api_key=api_key)
        self.model = model or MODEL
        
        # Use underscores for filename safety
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.output_filename = f"AI_tryon_{current_time}.jpg"

    def perform_try_on(self, person_path, garment_path):
        try:
            # 1. Validate inputs and handle potential None returns from utils
            image1 = optimize_for_nano_banana(person_path)
            image2 = optimize_for_nano_banana(garment_path)

            if image1 is None or image2 is None:
                print("Error: One or both images could not be processed. Check file paths and formats.")
                return None

            # Define the configuration
            gen_config = {
                "response_modalities": ['IMAGE']
            }

            # Only add image_config if it's not the specific model that lacks it
            if self.model != "gemini-2.5-flash-image":
                gen_config["image_config"] = types.ImageConfig(
                    image_size=resolution
                )

            # 2. API Call with error handling
            response = self.client.models.generate_content(
                model=self.model,
                contents=[try_on_prompt, image1, image2],
                config=types.GenerateContentConfig(**gen_config),
            )

            # 3. Defensive checks on response parts
            if not response or not response.parts:
                print("Error: The model returned an empty response.")
                return None

            # Process and save the output
            for part in response.parts:
                # Use getattr or check for existence to avoid attribute errors
                if hasattr(part, 'inline_data') and part.inline_data is not None:
                    generated_img = part.as_image()
                    
                    # Ensure directory exists
                    if not os.path.exists(generated_images_dir):
                        os.makedirs(generated_images_dir)
                        
                    save_path = os.path.join(generated_images_dir, self.output_filename)
                    generated_img.save(save_path)
                    
                    # Fixed f-string usage here
                    print(f"Success! Image saved as: {save_path}")
                    return generated_img
                
                elif hasattr(part, 'text') and part.text is not None:
                    print(f"Model Feedback: {part.text}")

        except Exception as e:
            print(f"An unexpected error occurred during try-on: {e}")
            return None
        
        return None # Return None if no image part was found in the loop

if __name__== "__main__":
    vr = VirtualTryOn()
    # Adding a check to ensure we don't call .show() on a None object
    img = vr.perform_try_on(
        r"C:\Users\MRH RAFI\Pictures\Screenshots\Screenshot 2026-05-06 100202.png",
        r"C:\Users\MRH RAFI\Downloads\SECWTAG-600x618.jpg"
    )
    
    if img:
        img.show()
    else:
        print("Failed to generate or display the try-on image.")