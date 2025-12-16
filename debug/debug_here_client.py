
import sys
import os
import datetime
# Add root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from api.utils.here_client import route
except ImportError as e:
    print(f"ImportError: {e}")
    # Try adding api to path too
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../api")))
    try:
        from utils.here_client import route
    except ImportError as e2:
        print(f"ImportError 2: {e2}")
        sys.exit(1)

def test_route_direct():
    print("Testing here_client.route directly...")
    
    origin = (60.17116, 24.93265)
    dest = (65.01035, 25.47357)
    now = datetime.datetime.now().isoformat()
    
    result = route(
        origin=origin,
        destination=dest,
        departure_time=now,
        routing_mode="fast"
    )
    
    if result and not result.get("error"):
        print("SUCCESS: Route found")
        print(f"Keys: {result.keys()}")
    else:
        print("FAILURE: Route returned error")
        print(result)

if __name__ == "__main__":
    test_route_direct()
