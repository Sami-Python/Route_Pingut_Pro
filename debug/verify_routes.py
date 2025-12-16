
import sys
import os
from fastapi.routing import APIRoute, Mount

# Add 'api' to path to simulate running from root or inside api
sys.path.append(os.path.join(os.getcwd(), 'api'))

try:
    from api.main import app
    print("Successfully imported api.main.app")
    
    print("\n--- ROUTES ---")
    
    def print_routes(routes, prefix=""):
        for route in routes:
            if isinstance(route, APIRoute):
                print(f"PATH: {prefix}{route.path} | REF: {route.name}")
            elif isinstance(route, Mount):
                print(f"MOUNT: {prefix}{route.path} -> {route.name}")
                # Recurse into mount
                print_routes(route.app.routes, prefix=prefix + route.path)
                
    print_routes(app.routes)
    
except Exception as e:
    print(f"Import failed: {e}")
    # Try importing directly if we are 'in' the folder structure differently
    try:
        sys.path.append(os.getcwd())
        from api.main import app
        print("Successfully imported api.main.app (attempt 2)")
        print_routes(app.routes)
    except Exception as e2:
        print(f"Import failed again: {e2}")
