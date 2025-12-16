import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.getcwd())

# Load env as main.py does
load_dotenv()

def test_full_analysis():
    print("Testing GeminiRouteAnalyzer...")
    
    # 1. Check API Key
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("CRITICAL: No API Key found in env!")
        return
        
    try:
        from api.utils.gemini_client import GeminiRouteAnalyzer
        
        # 2. Initialize
        analyzer = GeminiRouteAnalyzer()
        if not analyzer.model:
            print("ERROR: Analyzer failed to initialize model (check logs/print above)")
            return

        print(f"Model initialized: {analyzer.model.model_name}")

        # 3. Prepare Data (Mocking maps_api.py logic)
        # Frontend sends: distance_km=120, duration_hours=1.5
        d_km = 120.0
        t_h = 1.5
        
        adapter_summary = {
            "length": d_km * 1000,
            "duration": t_h * 3600
        }
        
        incidents = []
        weather = []
        
        print(f"Sending data: {adapter_summary}")
        
        # 4. Call Analyze
        # Modify gemini_client temporarily to raise exception if we want? 
        # Or just rely on it printing to stdout (which run_command captures)
        
        result = analyzer.analyze_route(adapter_summary, incidents, weather)
        
        print("\n--- RESULT ---")
        print(result)
        
    except Exception as e:
        print(f"\nCRITICAL EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_analysis()
