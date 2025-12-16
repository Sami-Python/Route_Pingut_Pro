
import os
from dotenv import load_dotenv

load_dotenv()

google = os.getenv("GOOGLE_API_KEY")
gemini = os.getenv("GEMINI_API_KEY")

if google:
    print(f"✅ GOOGLE_API_KEY löytyy! (Pituus: {len(google)})")
elif gemini:
    print(f"✅ GEMINI_API_KEY löytyy! (Pituus: {len(gemini)})")
else:
    print("❌ Avainta ei löytynyt. Varmista että muuttujan nimi on GOOGLE_API_KEY tai GEMINI_API_KEY.")
