import requests
from typing import List, Tuple, Optional, Dict, Any

# Käynnistä:  python API_DIGI_test.py

# --- 1. TESTIDATA ---
# Koordinaatit testialueen luomiseksi (Helsinki - Tampere reitin alkuosa)
TEST_ROUTE_COORDS = [
    (60.1698, 24.938),  # Helsinki
    (60.200, 24.800),   # Espoo
    (60.450, 24.600)    # Vihti
]

# --- 2. APUFUNKTIOT ---

def calculate_bbox(route_coords: List[Tuple[float, float]], buffer: float = 0.05) -> Optional[str]:
    """
    Laskee reittipisteiden ympärille Bounding Boxin (BBox).
    Palauttaa stringin: "minLon,minLat,maxLon,maxLat" (Digitraffic-järjestys).
    HUOM: Liikennetiedote-API EI tue bbox-parametria, tätä voi käyttää omassa
    jatkologiikassa / debugissa.
    """
    if not route_coords:
        return None

    lats = [p[0] for p in route_coords]
    lons = [p[1] for p in route_coords]

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    # Lisätään puskuri (buffer)
    bbox = f"{min_lon - buffer},{min_lat - buffer},{max_lon + buffer},{max_lat + buffer}"
    return bbox


def fetch_digitraffic_messages() -> Dict[str, Any]:
    """
    Suorittaa API-kutsun Digitrafficin Liikennetiedote-rajapintaan (Simple JSON).
    Käytetään vain dokumentoituja parametreja:
      - inactiveHours
      - includeAreaGeometry
      - situationType (valinnainen, mutta hyvä rajaukseen)
    """
    base_url = "https://tie.digitraffic.fi/api/traffic-message/v1/messages"

    params = {
        "inactiveHours": 0,              # vain aktiiviset
        "includeAreaGeometry": "false",  # kevyempi vastaus
        # Halutessasi voit poistaa tämän tai vaihtaa:
        # EXEMPTED_TRANSPORT, ROAD_WORK, TRAFFIC_ANNOUNCEMENT, WEIGHT_RESTRICTION
        "situationType": "TRAFFIC_ANNOUNCEMENT"
    }

    headers = {
        "User-Agent": "StreamlitTrafficAppTest/1.0",
        "Accept-Encoding": "gzip",
        # Suositeltu: oma yhteystieto – Digitraffic voi ottaa yhteyttä ongelmatilanteessa
        # Vaihda tähän oma sähköpostisi
        "Digitraffic-User": "oma.email@esimerkki.fi"
    }

    print(f"DEBUG: Kutsutaan URL: {base_url} parametreilla: {params}")

    try:
        resp = requests.get(base_url, params=params, headers=headers, timeout=15)

        # Jos HTTP-status ei ole 2xx, nostetaan poikkeus -> käsitellään alla
        resp.raise_for_status()

        data = resp.json()
        return {
            "status": "SUCCESS",
            "data": data,
            "count": len(data.get("features", []))
        }

    except requests.HTTPError as e:
        # Palautetaan tarkempi HTTP-virhe
        return {
            "status": "FAILED",
            "code": resp.status_code,
            "error": resp.text
        }
    except Exception as e:
        return {
            "status": "EXCEPTION",
            "error": str(e)
        }


# --- 3. PÄÄTESTILOHKO ---

if __name__ == "__main__":
    print("=" * 50)
    print("      DIGITRAFFIC API TESTI ALKAA      ")
    print("=" * 50)

    # 1. BBoxin laskenta (debug-tieto / myöhempää käyttöä varten)
    test_bbox = calculate_bbox(TEST_ROUTE_COORDS)

    if not test_bbox:
        print("🛑 TESTI EPÄONNISTUI: Bounding Boxin laskenta epäonnistui.")
    else:
        print(f"✅ BBox laskettu (ei lähetetä API:lle, vain debug): {test_bbox}")

        # 2. API-kutsun suoritus
        result = fetch_digitraffic_messages()

        print("\n--- API-VASTAUKSEN TARKISTUS ---")

        if result["status"] == "SUCCESS":

            # Tarkistetaan, että data sisältää "features"-avaimen
            if "features" in result["data"]:
                print("✅ TESTI ONNISTUI: Status 200 OK.")
                print(f"ℹ️ Liikennetiedotteita löytyi: {result['count']} kpl.")

                if result["count"] > 0:
                    first = result["data"]["features"][0]
                    props = first.get("properties", {})
                    first_type = props.get("situationType", "Tuntematon")
                    first_title = ""
                    if props.get("announcements"):
                        first_title = props["announcements"][0].get("title", "")

                    print(f"ℹ️ Ensimmäisen tiedotteen tyyppi: {first_type}")
                    if first_title:
                        print(f"   Otsikko: {first_title}")

                print("==================================================")
            else:
                print("⚠️ TESTI EPÄONNISTUI: Status 200 OK, mutta vastauksesta puuttuu 'features'-avain.")
                print("==================================================")

        elif result["status"] == "FAILED":
            print(f"🛑 TESTI EPÄONNISTUI: HTTP-virhe {result['code']}.")
            print(f"   Palvelimen vastaus: {result['error'][:300]}...")
            print("   Varmista myös, ettei kyselymääriä ole rajoitettu IP:ltäsi.")
            print("==================================================")

        elif result["status"] == "EXCEPTION":
            print("🛑 TESTI EPÄONNISTUI: Verkkovirhe tai muu poikkeus.")
            print(f"   Virhe: {result['error']}")
            print("==================================================")
