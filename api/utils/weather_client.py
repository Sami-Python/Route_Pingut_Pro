import requests
import time

def get_rainviewer_data() -> tuple:
    """
    Hakee RainViewerin aktiivisen palvelimen (host) ja aikaleimat.
    Palauttaa: (host_url, timestamps_dict)
    """
    # Metadata-API on yleensä erittäin vakaa
    url = "https://api.rainviewer.com/public/weather-maps.json"
    headers = {"User-Agent": "StreamlitApp/1.0"}
    timestamps = {}
    host = "https://tile.cache.rainviewer.com" # Fallback-osoite jos API ei kerro
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        
        # 1. Otetaan host API:sta (Tämä on avain toimivuuteen!)
        if "host" in data:
            host = data["host"]
            # Poistetaan mahdollinen lopun kauttaviiva
            if host.endswith("/"):
                host = host[:-1]

        # 2. Mennyt data
        if "radar" in data and "past" in data["radar"]:
            for item in data["radar"]["past"]:
                timestamps[item["time"]] = item["path"]
                
        # 3. Ennuste
        if "radar" in data and "nowcast" in data["radar"]:
            for item in data["radar"]["nowcast"]:
                timestamps[item["time"]] = item["path"]
                
    except Exception as e:
        print(f"RainViewer API error: {e}")
        # Hätätapaus: luodaan nykyhetki
        now = int(time.time())
        now = now - (now % 600)
        timestamps[now] = f"/v2/radar/{now}" # Fallback path assumption
        
    return host, timestamps

def get_closest_timestamp(target_ts: int, available_timestamps: list) -> int:
    """Etsii listasta aikaleiman, joka on lähimpänä kohdeaikaa."""
    if not available_timestamps:
        return int(time.time())
    return min(available_timestamps, key=lambda x: abs(x - target_ts))