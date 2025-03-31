import os
import google.generativeai as genai
from dotenv import load_dotenv

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found. Please check your .env file.")
        return

    print(f"🔑 Using API Key: ...{api_key[-4:] if api_key else 'None'}")
    
    try:
        genai.configure(api_key=api_key)
        
        print("\n📡 Fetching available models from Google Generative AI...")
        print("=" * 60)
        
        # List models
        models = list(genai.list_models())
        
        # Filter for models that support content generation (chat/text)
        chat_models = [m for m in models if 'generateContent' in m.supported_generation_methods]
        
        if not chat_models:
            print("⚠️  No models found with 'generateContent' capability.")
        
        for m in chat_models:
            print(f"ID:           {m.name}")
            print(f"Display Name: {m.display_name}")
            print(f"Description:  {m.description}")
            print("-" * 60)
            
        print(f"\n✅ Found {len(chat_models)} models capable of content generation.")
        print("\nCopy the 'ID' of the model you want to use into your agent code.")
        
    except Exception as e:
        print(f"\n❌ Error listing models: {e}")
        print("\nTroubleshooting:")
        print("1. Check if your API key is correct.")
        print("2. Ensure 'google-generativeai' package is installed: pip install -q -U google-generativeai")

if __name__ == "__main__":
    main()
