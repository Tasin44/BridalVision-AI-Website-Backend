import os
from PIL import Image, UnidentifiedImageError

def optimize_for_nano_banana(image_path):
    """
    Optimizes an image for Nano Banana with error handling.
    Returns the Image object if successful, or None if an error occurs.
    """
    # 1. Check if file exists before trying to open it
    if not os.path.exists(image_path):
        print(f"Error: The file '{image_path}' does not exist.")
        return None

    try:
        with Image.open(image_path) as img:
            # Load the image data into memory so we can return it after the 'with' block closes
            img.load()
            
            # Handle Alpha channel (RGBA)
            if img.mode == 'RGBA':
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3]) 
                img = background
            else:
                img = img.convert("RGB")

            # Resize while maintaining aspect ratio
            max_size = (512, 512)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            return img

    except UnidentifiedImageError:
        print(f"Error: '{image_path}' is not a valid image file.")
    except PermissionError:
        print(f"Error: Permission denied when accessing '{image_path}'.")
    except Exception as e:
        print(f"An unexpected error occurred processing '{image_path}': {e}")
    
    return None