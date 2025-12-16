
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Add project root to sys.path to ensure we can import api modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.utils.gemini_client import GeminiRouteAnalyzer

def test_analyzer():
    print("Initializing GeminiRouteAnalyzer...")
    analyzer = GeminiRouteAnalyzer()
    
    if not analyzer.model:
        print("ERROR: Model not initialized (Check API Key)")
        return

    print(f"Model initialized: {analyzer.model._model_name}")

    # Dummy data
    route_summary = {"duration": 3600, "length": 50000} # 1h, 50km
    incidents = [{"tyyppi": "Tietyö"}]
    weather = ["Camera1", "Camera2"]

    print("Analyzing route...")
    try:
        result = analyzer.analyze_route(route_summary, incidents, weather)
        print("\n--- ANALYSIS RESULT ---")
        print(result)
        print("-----------------------")
        if "Virhe" in result or "Pahoittelut" in result:
             print("FAILURE: Analysis returned an error message.")
        else:
             print("SUCCESS: Analysis generated.")
    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    test_analyzer()
