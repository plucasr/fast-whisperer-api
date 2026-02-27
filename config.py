import os
from dotenv import load_dotenv

load_dotenv()

# AI Model Configuration
GEMINI_MODEL = "models/gemini-flash-latest"
GoogleAPIKey = os.getenv("GOOGLE_API_KEY")
