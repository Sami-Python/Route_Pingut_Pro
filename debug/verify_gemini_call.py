
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)



candidate_models = [
    'gemini-flash-latest',
    'gemini-2.0-flash-lite-preview-02-05',
    'gemini-2.5-flash',
    'gemini-2.0-flash-001'
]


for model_name in candidate_models:
    print(f"\n--- Testing model: {model_name} ---")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello, can you hear me?")
        print(f"SUCCESS with {model_name}!")
        print(response.text)
        break # Stop after finding a working one
    except Exception as e:
        print(f"FAILED with {model_name}: {e}")

