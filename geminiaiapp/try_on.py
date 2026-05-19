import os
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types
from datetime import datetime
from .config import MODEL, api_key, resolution, generated_images_dir, background_path, logo_path
from .prompts import try_on_prompt
from .utils import optimize_for_nano_banana 
from rembg import remove
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
                    image_bytes = part.inline_data.data
                    if not image_bytes:
                        continue
                    
                    #way5
                    # generated_img = Image.open(BytesIO(image_bytes)).convert("RGBA")
                    # bg = Image.open(background_path).convert("RGBA").resize(generated_img.size)
                    # bg.paste(generated_img, (0, 0), generated_img)
                    # generated_img = bg
                    

                    # generated_img = Image.open(BytesIO(image_bytes)).convert("RGBA")
                    # Remove AI-generated background using chroma/edge detection

                    #way4 with shop2
                    # generated_img_bytes = BytesIO()
                    # Image.open(BytesIO(image_bytes)).save(generated_img_bytes, format='PNG')
                    # generated_img = remove(generated_img_bytes.getvalue())
                    # generated_img = Image.open(BytesIO(generated_img)).convert("RGBA")
                    # bg = Image.open(background_path).convert("RGBA").resize(generated_img.size)
                    # bg.paste(generated_img, (0, 0), generated_img)
                    # generated_img = bg

                    #way1
                    # bg = Image.open(background_path).convert("RGBA").resize((512, 512))
                    # subject_w = int(bg.width * 0.75)
                    # subject_h = int(bg.height * 0.95)
                    # generated_img = generated_img.resize((subject_w, subject_h), Image.Resampling.LANCZOS)
                    # x = (bg.width - subject_w) // 2
                    # y = bg.height - subject_h
                    # bg.paste(generated_img, (x, y), generated_img)
                    # generated_img = bg


                    #way2
                    # bg = Image.open(background_path).convert("RGBA").resize(generated_img.size)
                    # bg.paste(generated_img, (0, 0), generated_img)
                    # generated_img = bg
                    # from PIL import ImageFilter
                    # # Slightly blur the alpha mask before pasting for softer edges
                    # alpha = generated_img.split()[3].filter(ImageFilter.GaussianBlur(radius=1))
                    # generated_img.putalpha(alpha)

                    #way3_full_image with the dress and girl but not the shop background
                    # bg = Image.open(background_path).convert("RGBA").resize(generated_img.size)
                    # bg.paste(generated_img, (0, 0), generated_img)
                    # generated_img = bg
                    # from PIL import ImageEnhance
                    # enhancer = ImageEnhance.Brightness(generated_img)
                    # generated_img = enhancer.enhance(1.05)  # slight warmth boost to match store lighting

                    #way8
                    # generated_img = Image.open(BytesIO(image_bytes)).convert("RGBA")
                    # bg = Image.open(background_path).convert("RGBA").resize(generated_img.size)
                    # from PIL import ImageFilter
                    # # Slightly blur the alpha mask before pasting for softer edges
                    # alpha = generated_img.split()[3].filter(ImageFilter.GaussianBlur(radius=1))
                    # generated_img.putalpha(alpha)
                    # bg.paste(generated_img, (0, 0), generated_img)


                    #way9
                    # generated_img = Image.open(BytesIO(image_bytes)).convert("RGBA")
                    # bg = Image.open(background_path).convert("RGBA").resize(generated_img.size)
                    # bg.paste(generated_img, (0, 0), generated_img)
                    # generated_img = bg
                    # from PIL import ImageEnhance
                    # enhancer = ImageEnhance.Brightness(generated_img)
                    # generated_img = enhancer.enhance(1.05)  # slight warmth boost to match store lighting

                    # Step 1: Remove AI background, keep full subject
                    generated_img = remove(image_bytes)
                    subject = Image.open(BytesIO(generated_img)).convert("RGBA")

                    # Step 2: Load your background
                    bg = Image.open(background_path).convert("RGBA")
                    bg_w, bg_h = bg.size

                    '''
                    # Step 3: Resize subject to fit bg height fully (no crop)
                    scale = bg_h / subject.height
                    new_w = int(subject.width * scale)
                    subject = subject.resize((new_w, bg_h), Image.Resampling.LANCZOS)

                    # Step 4: Center subject horizontally on background
                    x = (bg_w - new_w) // 2
                    bg.paste(subject, (x, 0), subject)
                    '''
                    # Step 3: Resize subject to fit bg height fully (no crop)
                    scale = (bg_h) / subject.height   # use 90% instead of 100%
                    new_w = int(subject.width * scale)
                    new_h = int(subject.height * scale)

                    subject = subject.resize((new_w, new_h), Image.Resampling.LANCZOS)

                    # Step 4: Center subject horizontally and vertically
                    x = (bg_w - new_w) // 2
                    y = (bg_h - new_h) // 2

                    bg.paste(subject, (x, y), subject)


                    generated_img = bg


                    # Apply logo at bottom-right corner (black background removed)
                    logo = Image.open(logo_path).convert("RGBA")

                    # Remove black background from logo
                    r, g, b, a = logo.split()
                    mask = Image.eval(r, lambda x: 255 if x > 30 else 0)  # keep only non-black pixels
                    logo.putalpha(mask)

                    # Resize logo to reasonable size (15% of image width)
                    img_w, img_h = generated_img.size
                    logo_w = int(img_w * 0.15)
                    ratio = logo_w / logo.size[0]
                    logo_h = int(logo.size[1] * ratio)
                    logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)

                    # Place bottom-right with padding
                    padding = 10
                    x = img_w - logo_w - padding
                    y = img_h - logo_h - padding
                    generated_img.paste(logo, (x, y), logo)

                    generated_img = generated_img.convert("RGB")
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