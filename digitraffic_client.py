# digitraffic_client.py
import requests
from typing import List, Tuple, Optional, Dict, Any

# -------------------------
# APU: BBox reitin ympärille
# -------------------------

def calculate_bbox(route_coords: List[Tuple[float, float]], buffer: float = 0.05) -> Optional[str]:
    """
    Laskee reittipisteiden ympärille Bounding Boxin (BBox).
    Palauttaa stringin: "minLon,minLat,maxLon,maxLat".
    HUOM: Digitrafficin liikennetiedote-API ei tue bbox-parametria suoraan,
    mutta tätä voi käyttää jatkokehityksessä esim. oman filtteröinnin tukena.
    """
    if not route_coords:
        return None

    lats = [p[0] for p in route_coords]
    lons = [p[1] for p in route_coords]

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    bbox = f"{min_lon - buffer},{min_lat - buffer},{max_lon + buffer},{max_lat + buffer}"
    return bbox

# --------------------------------------
# DIGITRAFFIC: Liikennetiedote-API (v1)
# --------------------------------------

def fetch_digitraffic_messages() -> Dict[str, Any]:
    """
    Hakee Digitrafficin liikennetiedotteet (Simple JSON API / v1).
    Palauttaa:
        {
            "status": "SUCCESS" | "FAILED" | "EXCEPTION",
            "data": ... (raaka JSON),
            "count": int
        }
    """
    base_url = "https://tie.digitraffic.fi/api/traffic-message/v1/messages"

    params = {
        "inactiveHours": 0,
        "includeAreaGeometry": "false",
        "situationType": "TRAFFIC_ANNOUNCEMENT"
    }

    headers = {
        "User-Agent": "StreamlitTrafficApp/1.0",
        "Accept-Encoding": "gzip",
        "Digitraffic-User": "oma.email@esimerkki.fi"  # vaihda omaksesi
    }

    try:
        resp = requests.get(base_url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return {
            "status": "SUCCESS",
            "data": data,
            "count": len(data.get("features", []))
        }
    except requests.HTTPError:
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

# --------------------------------------
# APUMUUNNOS: API -> yksinkertainen lista
# --------------------------------------

def traffic_messages_near_route(coords: List[Tuple[float, float]]) -> List[Dict[str, str]]:
    """
    Hakee Digitraffic-liikennetiedotteet ja palauttaa yksinkertaistetun listan,
    jonka rakenteen Streamlit-appisi voi näyttää (otsikko, sijainti, kuvaus, aika).
    Tässä vaiheessa emme vielä oikeasti "rajaa reitin ympärille", vaan palautamme
    kaikki aktiivit ilmoitukset – jatkokehityksessä voit käyttää BBoxia/filtteröintiä.
    """
    if not coords:
        return []

    result = fetch_digitraffic_messages()

    if result.get("status") != "SUCCESS":
        # Voit halutessasi logittaa result["error"]
        return []

    features = result["data"].get("features", [])
    simplified: List[Dict[str, str]] = []

    for feat in features:
        props = feat.get("properties", {})
        announcements = props.get("announcements") or []
        # Otetaan ensimmäinen ilmoitus, jos olemassa
        title = ""
        description = ""
        if announcements:
            first = announcements[0]
            title = first.get("title", "")
            description = first.get("description", "")

        situation_type = props.get("situationType", "Tuntematon")
        # Esim. "Helsinki, Teollisuuskatu" löytyy usein title/descriptionista
        location = props.get("roadAddress", "") or title

        simplified.append({
            "otsikko": title or "Liikennetiedote",
            "sijainti": location or "Tuntematon sijainti",
            "kuvaus": description or situation_type,
            "aika": props.get("creationTime", "Tuntematon aika")
        })

    return simplified


def tms_near_route(coords: List[Tuple[float, float]]) -> List[str]:
    """
    Placeholder TMS (sääasemat) -tieto.
    Oikeassa toteutuksessa tänne tulisi kutsu TMS-rajapintaan ja filtteri BBoxin avulla.
    """
    if not coords:
        return []

    # TODO: toteuta oikea TMS-kutsu (tie.digitraffic.fi/api/tms-stations...) BBoxilla
    return ["Digitrafficin TMS (sääasema) tiedon haku vaatii erillisen TMS-API-kutsun."]
