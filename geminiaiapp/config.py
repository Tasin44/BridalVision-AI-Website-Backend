from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

generated_images_dir = BASE_DIR / "generated_image"

available_models = [
    "gemini-3.1-flash-image-preview",
    "gemini-3-pro-image-preview",
    "gemini-2.5-flash-image"
]


MODEL = "gemini-3.1-flash-image-preview"

api_key = os.getenv("GOOGLE_API_KEY")

resolution="512"

