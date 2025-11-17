import requests

# Korvaa omalla HERE API -avaimella

# Lisää oma HERE API -avaimesi tähän
HERE_API_KEY = "OQFZ4YGejiwxEtYlxNyHqgebBUb4vdmuER3qYcAzx5A"

# Geokoodaus

#def geocode(address):
#    url = f"https://geocode.search.hereapi.com/v1/geocode?q={address}&limit=1&apiKey={HERE_API_KEY}"
#    resp = requests.get(url)
#    if resp.status_code == 200:
#        data = resp.json()
#        items = data.get("items", [])
#        if items:
#            position = items[0]["position"]
#            return (position["lat"], position["lng"])
#    return None
#
## Reitin haku
#
#
#
#def route(origin, destination):
#    url = (
#        f"https://router.hereapi.com/v8/routes?transportMode=car"
#        f"&origin={origin[0]},{origin[1]}&destination={destination[0]},{destination[1]}"
#        f"&return=polyline&apiKey={HERE_API_KEY}"
#    )
#    resp = requests.get(url)
#    if resp.status_code == 200:
#        data = resp.json()
#        print("DEBUG: HERE Routing API response:", data)
#        return data
#    else:
#        print(f"DEBUG: Routing API status code: {resp.status_code}")
#        print(f"DEBUG: Routing API response: {resp.text}")
#        return None
#
## Liikennetiedot reitiltä
#
#def traffic_along_route(route_geometry):
#    # Esimerkki HERE Traffic API -kutsusta
#    # Voit käyttää reitin polylinea tai bounding boxia
#    # Tässä dummy, koska API vaatii tarkempaa toteutusta
#    return ["Integraatio vaatii polyline-dekoodauksen ja bounding boxin"]
#
# --- GEOKOODAUS (Osoite -> Koordinaatit) ---
def geocode(address):
    """
    Muuttaa osoitteen (esim. 'Helsinki') koordinaateiksi (lat, lon).
    """
    # KORJAUS 1: URL on nyt kokonainen ja sisältää apiKeyn
    url = f"https://geocode.search.hereapi.com/v1/geocode?q={address}&limit=1&apiKey={HERE_API_KEY}"
    
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            if items:
                position = items[0]["position"]
                # Palauttaa tuplen: (60.169, 24.938)
                return (position["lat"], position["lng"])
            else:
                print(f"DEBUG: Osoitetta '{address}' ei löytynyt.")
        else:
            print(f"DEBUG: Geocode virhe: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"DEBUG: Geocode exception: {e}")
    
    return None

# --- REITITYS (Koordinaatit A -> Koordinaatit B) ---
def route(origin, destination):
    """
    Hakee reitin kahden koordinaattipisteen välillä.
    origin: (lat, lon)
    destination: (lat, lon)
    """
    # KORJAUS 2: URL on korjattu ja f-stringit on suljettu oikein
    # Lisätty 'return=polyline,summary', jotta saadaan myös matka-aika tarvittaessa
    url = (
        f"https://router.hereapi.com/v8/routes?transportMode=car"
        f"&origin={origin[0]},{origin[1]}"
        f"&destination={destination[0]},{destination[1]}"
        f"&return=polyline,summary"
        f"&apiKey={HERE_API_KEY}"
    )
    
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            # Tulostetaan vain onnistumisviesti, koko data on usein liian iso luettavaksi
            print("DEBUG: Reitti haettu onnistuneesti HERE API:sta.") 
            return data
        else:
            print(f"DEBUG: Routing API status code: {resp.status_code}")
            print(f"DEBUG: Routing API response: {resp.text}")
            return None
    except Exception as e:
        print(f"DEBUG: Route exception: {e}")
        return None

# --- LIIKENNETIEDOT (Placeholder) ---
def traffic_along_route(route_geometry):
    """
    Tämä on toistaiseksi tyhjä runko.
    Oikea toteutus vaatisi Flow API:n käyttöä Bounding Boxilla.
    """
    return ["Liikennetietojen haku HEREltä vaatii Flow API -lisenssin tai monimutkaisemman logiikan."]