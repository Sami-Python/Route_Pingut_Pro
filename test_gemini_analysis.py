
import sys
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load env from .env file
load_dotenv()

# Ensure api directory is reachable
sys.path.append(os.getcwd())

try:
    from api.utils.gemini_client import GeminiRouteAnalyzer
    print("Successfully imported GeminiRouteAnalyzer")
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

def test_analysis():
    analyzer = GeminiRouteAnalyzer()
    
    if not analyzer.model:
        print("Model initialization failed (no API key?)")
        return

    # Try a different model
    model_name = 'gemini-flash-latest'
    print(f"Testing model: {model_name}")
    analyzer.model = genai.GenerativeModel(model_name)

    route_summary = {
        "length": 150000, # 150km
        "duration": 7200 # 2 hours
    }
    
    incidents = [
        {"tyyppi": "Tietyö", "kuvaus": "Tiepäällystystyö"}
    ]
    
    print("Starting analysis...")
    try:
        result = analyzer.analyze_route(route_summary, incidents, [])
        print("\n--- ANALYSIS RESULT ---\n")
        print(result)
        print("\n-----------------------\n")
    except Exception as e:
        print(f"Analysis failed with exception: {e}")

if __name__ == "__main__":
    test_analysis()
