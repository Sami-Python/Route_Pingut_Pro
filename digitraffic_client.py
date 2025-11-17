import requests

def calculate_bbox(route_coords):
    """
    Laskee reittipisteiden ympärille laatikon (Bounding Box).
    route_coords: lista tupleja [(lat, lon), (lat, lon), ...]
    Palauttaa stringin: "minLon,minLat,maxLon,maxLat"
    """
    if not route_coords:
        return None

    # Erotellaan lat ja lon omiin listoihinsa
    lats = [p[0] for p in route_coords]
    lons = [p[1] for p in route_coords]

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    # Lisätään pieni puskuri (buffer), jotta reitti ei leikkaudu aivan reunasta
    buffer = 0.05 # n. 5-10 km
    
    bbox = f"{min_lon - buffer},{min_lat - buffer},{max_lon + buffer},{max_lat + buffer}"
    return bbox

def traffic_messages_near_route(route_coords):
    """
    Hakee liikennehäiriöt reitin rajaamalta alueelta.
    """
    bbox = calculate_bbox(route_coords)
    if not bbox:
        return []

    url = f"https://tie.digitraffic.fi/api/traffic-message/v1/messages?bbox={bbox}"
    
    try:
        # Lisätään headerit kuten Fintraffic toivoo
        headers = { 
            "User-Agent": "StreamlitTrafficApp/1.0 (oma.sahkoposti@example.com)",
            "Accept-Encoding": "gzip"
        }
        
        resp = requests.get(url, headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            
            messages = []
            for feat in features:
                props = feat.get("properties", {})
                announcements = props.get("announcements", [])
                
                if announcements:
                    # Otetaan talteen tärkeimmät tiedot
                    info = {
                        "otsikko": announcements[0].get("title", "Ei otsikkoa"),
                        "kuvaus": announcements[0].get("features", [{}])[0].get("name", ""),
                        "sijainti": announcements[0].get("location", {}).get("description", ""),
                        "aika": announcements[0].get("location", {}).get("beginning", "")
                    }
                    messages.append(info)
            
            return messages
        else:
            print(f"Digitraffic virhe: {resp.status_code}")
            return []

    except Exception as e:
        print(f"Virhe Digitraffic-haussa: {e}")
        return []

def tms_near_route(route_coords):
    """
    Hakee sää- ja kelitiedot (Road Weather Stations) reitin alueelta.
    """
    bbox = calculate_bbox(route_coords)
    if not bbox:
        return []

    # Huom: Sääasemille käytetään eri endpointia
    url = "https://tie.digitraffic.fi/api/v3/data/road-weather-stations"
    # Digitrafficin v3 sää-API ei tue suoraan bboxia URL-parametrina samalla tavalla,
    # joten tässä haetaan kaikki ja suodatetaan (tai käytetään metadata-hakua).
    # Yksinkertaisuuden vuoksi tässä esimerkissä palautetaan tyhjä lista tai 
    # voidaan toteuttaa hakemalla kaikki ja suodattamalla koordinaattien mukaan.
    
    # Oikea tapa olisi hakea ensin asemat (metadata) bboxilla, jos API tukee, 
    # mutta pidetään tämä yksinkertaisena ja palautetaan placeholder-tieto.
    return ["Säädata vaatii tarkemman asemasuodatuksen (To do)"]
import requests

def calculate_bbox(route_coords):
    """
    Laskee reittipisteiden ympärille laatikon (Bounding Box).
    route_coords: lista tupleja [(lat, lon), (lat, lon), ...]
    Palauttaa stringin: "minLon,minLat,maxLon,maxLat"
    """
    if not route_coords:
        return None

    # Erotellaan lat ja lon omiin listoihinsa
    lats = [p[0] for p in route_coords]
    lons = [p[1] for p in route_coords]

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    # Lisätään pieni puskuri (buffer), jotta reitti ei leikkaudu aivan reunasta
    buffer = 0.05 # n. 5-10 km
    
    bbox = f"{min_lon - buffer},{min_lat - buffer},{max_lon + buffer},{max_lat + buffer}"
    return bbox

def traffic_messages_near_route(route_coords):
    """
    Hakee liikennehäiriöt reitin rajaamalta alueelta.
    """
    bbox = calculate_bbox(route_coords)
    if not bbox:
        return []

    url = f"https://tie.digitraffic.fi/api/traffic-message/v1/messages?bbox={bbox}"
    
    try:
        # Lisätään headerit kuten Fintraffic toivoo
        headers = { 
            "User-Agent": "StreamlitTrafficApp/1.0 (oma.sahkoposti@example.com)",
            "Accept-Encoding": "gzip"
        }
        
        resp = requests.get(url, headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            
            messages = []
            for feat in features:
                props = feat.get("properties", {})
                announcements = props.get("announcements", [])
                
                if announcements:
                    # Otetaan talteen tärkeimmät tiedot
                    info = {
                        "otsikko": announcements[0].get("title", "Ei otsikkoa"),
                        "kuvaus": announcements[0].get("features", [{}])[0].get("name", ""),
                        "sijainti": announcements[0].get("location", {}).get("description", ""),
                        "aika": announcements[0].get("location", {}).get("beginning", "")
                    }
                    messages.append(info)
            
            return messages
        else:
            print(f"Digitraffic virhe: {resp.status_code}")
            return []

    except Exception as e:
        print(f"Virhe Digitraffic-haussa: {e}")
        return []

def tms_near_route(route_coords):
    """
    Hakee sää- ja kelitiedot (Road Weather Stations) reitin alueelta.
    """
    bbox = calculate_bbox(route_coords)
    if not bbox:
        return []

    # Huom: Sääasemille käytetään eri endpointia
    url = "https://tie.digitraffic.fi/api/v3/data/road-weather-stations"
    # Digitrafficin v3 sää-API ei tue suoraan bboxia URL-parametrina samalla tavalla,
    # joten tässä haetaan kaikki ja suodatetaan (tai käytetään metadata-hakua).
    # Yksinkertaisuuden vuoksi tässä esimerkissä palautetaan tyhjä lista tai 
    # voidaan toteuttaa hakemalla kaikki ja suodattamalla koordinaattien mukaan.
    
    # Oikea tapa olisi hakea ensin asemat (metadata) bboxilla, jos API tukee, 
    # mutta pidetään tämä yksinkertaisena ja palautetaan placeholder-tieto.
    return ["Säädata vaatii tarkemman asemasuodatuksen (To do)"]
import requests

def calculate_bbox(route_coords):
    """
    Laskee reittipisteiden ympärille laatikon (Bounding Box).
    route_coords: lista tupleja [(lat, lon), (lat, lon), ...]
    Palauttaa stringin: "minLon,minLat,maxLon,maxLat"
    """
    if not route_coords:
        return None

    # Erotellaan lat ja lon omiin listoihinsa
    lats = [p[0] for p in route_coords]
    lons = [p[1] for p in route_coords]

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    # Lisätään pieni puskuri (buffer), jotta reitti ei leikkaudu aivan reunasta
    buffer = 0.05 # n. 5-10 km
    
    bbox = f"{min_lon - buffer},{min_lat - buffer},{max_lon + buffer},{max_lat + buffer}"
    return bbox

def traffic_messages_near_route(route_coords):
    """
    Hakee liikennehäiriöt reitin rajaamalta alueelta.
    """
    bbox = calculate_bbox(route_coords)
    if not bbox:
        return []

    url = f"https://tie.digitraffic.fi/api/traffic-message/v1/messages?bbox={bbox}"
    
    try:
        # Lisätään headerit kuten Fintraffic toivoo
        headers = { 
            "User-Agent": "StreamlitTrafficApp/1.0 (oma.sahkoposti@example.com)",
            "Accept-Encoding": "gzip"
        }
        
        resp = requests.get(url, headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            
            messages = []
            for feat in features:
                props = feat.get("properties", {})
                announcements = props.get("announcements", [])
                
                if announcements:
                    # Otetaan talteen tärkeimmät tiedot
                    info = {
                        "otsikko": announcements[0].get("title", "Ei otsikkoa"),
                        "kuvaus": announcements[0].get("features", [{}])[0].get("name", ""),
                        "sijainti": announcements[0].get("location", {}).get("description", ""),
                        "aika": announcements[0].get("location", {}).get("beginning", "")
                    }
                    messages.append(info)
            
            return messages
        else:
            print(f"Digitraffic virhe: {resp.status_code}")
            return []

    except Exception as e:
        print(f"Virhe Digitraffic-haussa: {e}")
        return []

def tms_near_route(route_coords):
    """
    Hakee sää- ja kelitiedot (Road Weather Stations) reitin alueelta.
    """
    bbox = calculate_bbox(route_coords)
    if not bbox:
        return []

    # Huom: Sääasemille käytetään eri endpointia
    url = "https://tie.digitraffic.fi/api/v3/data/road-weather-stations"
    # Digitrafficin v3 sää-API ei tue suoraan bboxia URL-parametrina samalla tavalla,
    # joten tässä haetaan kaikki ja suodatetaan (tai käytetään metadata-hakua).
    # Yksinkertaisuuden vuoksi tässä esimerkissä palautetaan tyhjä lista tai 
    # voidaan toteuttaa hakemalla kaikki ja suodattamalla koordinaattien mukaan.
    
    # Oikea tapa olisi hakea ensin asemat (metadata) bboxilla, jos API tukee, 
    # mutta pidetään tämä yksinkertaisena ja palautetaan placeholder-tieto.
    return ["Säädata vaatii tarkemman asemasuodatuksen (To do)"]
import requests

def calculate_bbox(route_coords):
    """
    Laskee reittipisteiden ympärille laatikon (Bounding Box).
    route_coords: lista tupleja [(lat, lon), (lat, lon), ...]
    Palauttaa stringin: "minLon,minLat,maxLon,maxLat"
    """
    if not route_coords:
        return None

    # Erotellaan lat ja lon omiin listoihinsa
    lats = [p[0] for p in route_coords]
    lons = [p[1] for p in route_coords]

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    # Lisätään pieni puskuri (buffer), jotta reitti ei leikkaudu aivan reunasta
    buffer = 0.05 # n. 5-10 km
    
    bbox = f"{min_lon - buffer},{min_lat - buffer},{max_lon + buffer},{max_lat + buffer}"
    return bbox

def traffic_messages_near_route(route_coords):
    """
    Hakee liikennehäiriöt reitin rajaamalta alueelta.
    """
    bbox = calculate_bbox(route_coords)
    if not bbox:
        return []

    url = f"https://tie.digitraffic.fi/api/traffic-message/v1/messages?bbox={bbox}"
    
    try:
        # Lisätään headerit kuten Fintraffic toivoo
        headers = { 
            "User-Agent": "StreamlitTrafficApp/1.0 (oma.sahkoposti@example.com)",
            "Accept-Encoding": "gzip"
        }
        
        resp = requests.get(url, headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            
            messages = []
            for feat in features:
                props = feat.get("properties", {})
                announcements = props.get("announcements", [])
                
                if announcements:
                    # Otetaan talteen tärkeimmät tiedot
                    info = {
                        "otsikko": announcements[0].get("title", "Ei otsikkoa"),
                        "kuvaus": announcements[0].get("features", [{}])[0].get("name", ""),
                        "sijainti": announcements[0].get("location", {}).get("description", ""),
                        "aika": announcements[0].get("location", {}).get("beginning", "")
                    }
                    messages.append(info)
            
            return messages
        else:
            print(f"Digitraffic virhe: {resp.status_code}")
            return []

    except Exception as e:
        print(f"Virhe Digitraffic-haussa: {e}")
        return []

def tms_near_route(route_coords):
    """
    Hakee sää- ja kelitiedot (Road Weather Stations) reitin alueelta.
    """
    bbox = calculate_bbox(route_coords)
    if not bbox:
        return []

    # Huom: Sääasemille käytetään eri endpointia
    url = "https://tie.digitraffic.fi/api/v3/data/road-weather-stations"
    # Digitrafficin v3 sää-API ei tue suoraan bboxia URL-parametrina samalla tavalla,
    # joten tässä haetaan kaikki ja suodatetaan (tai käytetään metadata-hakua).
    # Yksinkertaisuuden vuoksi tässä esimerkissä palautetaan tyhjä lista tai 
    # voidaan toteuttaa hakemalla kaikki ja suodattamalla koordinaattien mukaan.
    
    # Oikea tapa olisi hakea ensin asemat (metadata) bboxilla, jos API tukee, 
    # mutta pidetään tämä yksinkertaisena ja palautetaan placeholder-tieto.
    return ["Säädata vaatii tarkemman asemasuodatuksen (To do)"]
import requests

def calculate_bbox(route_coords):
    """
    Laskee reittipisteiden ympärille laatikon (Bounding Box).
    route_coords: lista tupleja [(lat, lon), (lat, lon), ...]
    Palauttaa stringin: "minLon,minLat,maxLon,maxLat"
    """
    if not route_coords:
        return None

    # Erotellaan lat ja lon omiin listoihinsa
    lats = [p[0] for p in route_coords]
    lons = [p[1] for p in route_coords]

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    # Lisätään pieni puskuri (buffer), jotta reitti ei leikkaudu aivan reunasta
    buffer = 0.05 # n. 5-10 km
    
    bbox = f"{min_lon - buffer},{min_lat - buffer},{max_lon + buffer},{max_lat + buffer}"
    return bbox

def traffic_messages_near_route(route_coords):
    """
    Hakee liikennehäiriöt reitin rajaamalta alueelta.
    """
    bbox = calculate_bbox(route_coords)
    if not bbox:
        return []

    url = f"https://tie.digitraffic.fi/api/traffic-message/v1/messages?bbox={bbox}"
    
    try:
        # Lisätään headerit kuten Fintraffic toivoo
        headers = { 
            "User-Agent": "StreamlitTrafficApp/1.0 (oma.sahkoposti@example.com)",
            "Accept-Encoding": "gzip"
        }
        
        resp = requests.get(url, headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            
            messages = []
            for feat in features:
                props = feat.get("properties", {})
                announcements = props.get("announcements", [])
                
                if announcements:
                    # Otetaan talteen tärkeimmät tiedot
                    info = {
                        "otsikko": announcements[0].get("title", "Ei otsikkoa"),
                        "kuvaus": announcements[0].get("features", [{}])[0].get("name", ""),
                        "sijainti": announcements[0].get("location", {}).get("description", ""),
                        "aika": announcements[0].get("location", {}).get("beginning", "")
                    }
                    messages.append(info)
            
            return messages
        else:
            print(f"Digitraffic virhe: {resp.status_code}")
            return []

    except Exception as e:
        print(f"Virhe Digitraffic-haussa: {e}")
        return []

def tms_near_route(route_coords):
    """
    Hakee sää- ja kelitiedot (Road Weather Stations) reitin alueelta.
    """
    bbox = calculate_bbox(route_coords)
    if not bbox:
        return []

    # Huom: Sääasemille käytetään eri endpointia
    url = "https://tie.digitraffic.fi/api/v3/data/road-weather-stations"
    # Digitrafficin v3 sää-API ei tue suoraan bboxia URL-parametrina samalla tavalla,
    # joten tässä haetaan kaikki ja suodatetaan (tai käytetään metadata-hakua).
    # Yksinkertaisuuden vuoksi tässä esimerkissä palautetaan tyhjä lista tai 
    # voidaan toteuttaa hakemalla kaikki ja suodattamalla koordinaattien mukaan.
    
    # Oikea tapa olisi hakea ensin asemat (metadata) bboxilla, jos API tukee, 
    # mutta pidetään tämä yksinkertaisena ja palautetaan placeholder-tieto.
    return ["Säädata vaatii tarkemman asemasuodatuksen (To do)"]
import requests

def calculate_bbox(route_coords):
    """
    Laskee reittipisteiden ympärille laatikon (Bounding Box).
    route_coords: lista tupleja [(lat, lon), (lat, lon), ...]
    Palauttaa stringin: "minLon,minLat,maxLon,maxLat"
    """
    if not route_coords:
        return None

    # Erotellaan lat ja lon omiin listoihinsa
    lats = [p[0] for p in route_coords]
    lons = [p[1] for p in route_coords]

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    # Lisätään pieni puskuri (buffer), jotta reitti ei leikkaudu aivan reunasta
    buffer = 0.05 # n. 5-10 km
    
    bbox = f"{min_lon - buffer},{min_lat - buffer},{max_lon + buffer},{max_lat + buffer}"
    return bbox

def traffic_messages_near_route(route_coords):
    """
    Hakee liikennehäiriöt reitin rajaamalta alueelta.
    """
    bbox = calculate_bbox(route_coords)
    if not bbox:
        return []

    url = f"https://tie.digitraffic.fi/api/traffic-message/v1/messages?bbox={bbox}"
    
    try:
        # Lisätään headerit kuten Fintraffic toivoo
        headers = { 
            "User-Agent": "StreamlitTrafficApp/1.0 (oma.sahkoposti@example.com)",
            "Accept-Encoding": "gzip"
        }
        
        resp = requests.get(url, headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            
            messages = []
            for feat in features:
                props = feat.get("properties", {})
                announcements = props.get("announcements", [])
                
                if announcements:
                    # Otetaan talteen tärkeimmät tiedot
                    info = {
                        "otsikko": announcements[0].get("title", "Ei otsikkoa"),
                        "kuvaus": announcements[0].get("features", [{}])[0].get("name", ""),
                        "sijainti": announcements[0].get("location", {}).get("description", ""),
                        "aika": announcements[0].get("location", {}).get("beginning", "")
                    }
                    messages.append(info)
            
            return messages
        else:
            print(f"Digitraffic virhe: {resp.status_code}")
            return []

    except Exception as e:
        print(f"Virhe Digitraffic-haussa: {e}")
        return []

def tms_near_route(route_coords):
    """
    Hakee sää- ja kelitiedot (Road Weather Stations) reitin alueelta.
    """
    bbox = calculate_bbox(route_coords)
    if not bbox:
        return []

    # Huom: Sääasemille käytetään eri endpointia
    url = "https://tie.digitraffic.fi/api/v3/data/road-weather-stations"
    # Digitrafficin v3 sää-API ei tue suoraan bboxia URL-parametrina samalla tavalla,
    # joten tässä haetaan kaikki ja suodatetaan (tai käytetään metadata-hakua).
    # Yksinkertaisuuden vuoksi tässä esimerkissä palautetaan tyhjä lista tai 
    # voidaan toteuttaa hakemalla kaikki ja suodattamalla koordinaattien mukaan.
    
    # Oikea tapa olisi hakea ensin asemat (metadata) bboxilla, jos API tukee, 
    # mutta pidetään tämä yksinkertaisena ja palautetaan placeholder-tieto.
    return ["Säädata vaatii tarkemman asemasuodatuksen (To do)"]
import requests

def calculate_bbox(route_coords):
    """
    Laskee reittipisteiden ympärille laatikon (Bounding Box).
    route_coords: lista tupleja [(lat, lon), (lat, lon), ...]
    Palauttaa stringin: "minLon,minLat,maxLon,maxLat"
    """
    if not route_coords:
        return None

    # Erotellaan lat ja lon omiin listoihinsa
    lats = [p[0] for p in route_coords]
    lons = [p[1] for p in route_coords]

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    # Lisätään pieni puskuri (buffer), jotta reitti ei leikkaudu aivan reunasta
    buffer = 0.05 # n. 5-10 km
    
    bbox = f"{min_lon - buffer},{min_lat - buffer},{max_lon + buffer},{max_lat + buffer}"
    return bbox

def traffic_messages_near_route(route_coords):
    """
    Hakee liikennehäiriöt reitin rajaamalta alueelta.
    """
    bbox = calculate_bbox(route_coords)
    if not bbox:
        return []

    url = f"https://tie.digitraffic.fi/api/traffic-message/v1/messages?bbox={bbox}"
    
    try:
        # Lisätään headerit kuten Fintraffic toivoo
        headers = { 
            "User-Agent": "StreamlitTrafficApp/1.0 (oma.sahkoposti@example.com)",
            "Accept-Encoding": "gzip"
        }
        
        resp = requests.get(url, headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            
            messages = []
            for feat in features:
                props = feat.get("properties", {})
                announcements = props.get("announcements", [])
                
                if announcements:
                    # Otetaan talteen tärkeimmät tiedot
                    info = {
                        "otsikko": announcements[0].get("title", "Ei otsikkoa"),
                        "kuvaus": announcements[0].get("features", [{}])[0].get("name", ""),
                        "sijainti": announcements[0].get("location", {}).get("description", ""),
                        "aika": announcements[0].get("location", {}).get("beginning", "")
                    }
                    messages.append(info)
            
            return messages
        else:
            print(f"Digitraffic virhe: {resp.status_code}")
            return []

    except Exception as e:
        print(f"Virhe Digitraffic-haussa: {e}")
        return []

def tms_near_route(route_coords):
    """
    Hakee sää- ja kelitiedot (Road Weather Stations) reitin alueelta.
    """
    bbox = calculate_bbox(route_coords)
    if not bbox:
        return []

    # Huom: Sääasemille käytetään eri endpointia
    url = "https://tie.digitraffic.fi/api/v3/data/road-weather-stations"
    # Digitrafficin v3 sää-API ei tue suoraan bboxia URL-parametrina samalla tavalla,
    # joten tässä haetaan kaikki ja suodatetaan (tai käytetään metadata-hakua).
    # Yksinkertaisuuden vuoksi tässä esimerkissä palautetaan tyhjä lista tai 
    # voidaan toteuttaa hakemalla kaikki ja suodattamalla koordinaattien mukaan.
    
    # Oikea tapa olisi hakea ensin asemat (metadata) bboxilla, jos API tukee, 
    # mutta pidetään tämä yksinkertaisena ja palautetaan placeholder-tieto.
    return ["Säädata vaatii tarkemman asemasuodatuksen (To do)"]
import requests

def calculate_bbox(route_coords):
    """
    Laskee reittipisteiden ympärille laatikon (Bounding Box).
    route_coords: lista tupleja [(lat, lon), (lat, lon), ...]
    Palauttaa stringin: "minLon,minLat,maxLon,maxLat"
    """
    if not route_coords:
        return None

    # Erotellaan lat ja lon omiin listoihinsa
    lats = [p[0] for p in route_coords]
    lons = [p[1] for p in route_coords]

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    # Lisätään pieni puskuri (buffer), jotta reitti ei leikkaudu aivan reunasta
    buffer = 0.05 # n. 5-10 km
    
    bbox = f"{min_lon - buffer},{min_lat - buffer},{max_lon + buffer},{max_lat + buffer}"
    return bbox

def traffic_messages_near_route(route_coords):
    """
    Hakee liikennehäiriöt reitin rajaamalta alueelta.
    """
    bbox = calculate_bbox(route_coords)
    if not bbox:
        return []

    url = f"https://tie.digitraffic.fi/api/traffic-message/v1/messages?bbox={bbox}"
    
    try:
        # Lisätään headerit kuten Fintraffic toivoo
        headers = { 
            "User-Agent": "StreamlitTrafficApp/1.0 (oma.sahkoposti@example.com)",
            "Accept-Encoding": "gzip"
        }
        
        resp = requests.get(url, headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            
            messages = []
            for feat in features:
                props = feat.get("properties", {})
                announcements = props.get("announcements", [])
                
                if announcements:
                    # Otetaan talteen tärkeimmät tiedot
                    info = {
                        "otsikko": announcements[0].get("title", "Ei otsikkoa"),
                        "kuvaus": announcements[0].get("features", [{}])[0].get("name", ""),
                        "sijainti": announcements[0].get("location", {}).get("description", ""),
                        "aika": announcements[0].get("location", {}).get("beginning", "")
                    }
                    messages.append(info)
            
            return messages
        else:
            print(f"Digitraffic virhe: {resp.status_code}")
            return []

    except Exception as e:
        print(f"Virhe Digitraffic-haussa: {e}")
        return []

def tms_near_route(route_coords):
    """
    Hakee sää- ja kelitiedot (Road Weather Stations) reitin alueelta.
    """
    bbox = calculate_bbox(route_coords)
    if not bbox:
        return []

    # Huom: Sääasemille käytetään eri endpointia
    url = "https://tie.digitraffic.fi/api/v3/data/road-weather-stations"
    # Digitrafficin v3 sää-API ei tue suoraan bboxia URL-parametrina samalla tavalla,
    # joten tässä haetaan kaikki ja suodatetaan (tai käytetään metadata-hakua).
    # Yksinkertaisuuden vuoksi tässä esimerkissä palautetaan tyhjä lista tai 
    # voidaan toteuttaa hakemalla kaikki ja suodattamalla koordinaattien mukaan.
    
    # Oikea tapa olisi hakea ensin asemat (metadata) bboxilla, jos API tukee, 
    # mutta pidetään tämä yksinkertaisena ja palautetaan placeholder-tieto.
    return ["Säädata vaatii tarkemman asemasuodatuksen (To do)"]
import requests

def calculate_bbox(route_coords):
    """
    Laskee reittipisteiden ympärille laatikon (Bounding Box).
    route_coords: lista tupleja [(lat, lon), (lat, lon), ...]
    Palauttaa stringin: "minLon,minLat,maxLon,maxLat"
    """
    if not route_coords:
        return None

    # Erotellaan lat ja lon omiin listoihinsa
    lats = [p[0] for p in route_coords]
    lons = [p[1] for p in route_coords]

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    # Lisätään pieni puskuri (buffer), jotta reitti ei leikkaudu aivan reunasta
    buffer = 0.05 # n. 5-10 km
    
    bbox = f"{min_lon - buffer},{min_lat - buffer},{max_lon + buffer},{max_lat + buffer}"
    return bbox

def traffic_messages_near_route(route_coords):
    """
    Hakee liikennehäiriöt reitin rajaamalta alueelta.
    """
    bbox = calculate_bbox(route_coords)
    if not bbox:
        return []

    url = f"https://tie.digitraffic.fi/api/traffic-message/v1/messages?bbox={bbox}"
    
    try:
        # Lisätään headerit kuten Fintraffic toivoo
        headers = { 
            "User-Agent": "StreamlitTrafficApp/1.0 (oma.sahkoposti@example.com)",
            "Accept-Encoding": "gzip"
        }
        
        resp = requests.get(url, headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            
            messages = []
            for feat in features:
                props = feat.get("properties", {})
                announcements = props.get("announcements", [])
                
                if announcements:
                    # Otetaan talteen tärkeimmät tiedot
                    info = {
                        "otsikko": announcements[0].get("title", "Ei otsikkoa"),
                        "kuvaus": announcements[0].get("features", [{}])[0].get("name", ""),
                        "sijainti": announcements[0].get("location", {}).get("description", ""),
                        "aika": announcements[0].get("location", {}).get("beginning", "")
                    }
                    messages.append(info)
            
            return messages
        else:
            print(f"Digitraffic virhe: {resp.status_code}")
            return []

    except Exception as e:
        print(f"Virhe Digitraffic-haussa: {e}")
        return []

def tms_near_route(route_coords):
    """
    Hakee sää- ja kelitiedot (Road Weather Stations) reitin alueelta.
    """
    bbox = calculate_bbox(route_coords)
    if not bbox:
        return []

    # Huom: Sääasemille käytetään eri endpointia
    url = "https://tie.digitraffic.fi/api/v3/data/road-weather-stations"
    # Digitrafficin v3 sää-API ei tue suoraan bboxia URL-parametrina samalla tavalla,
    # joten tässä haetaan kaikki ja suodatetaan (tai käytetään metadata-hakua).
    # Yksinkertaisuuden vuoksi tässä esimerkissä palautetaan tyhjä lista tai 
    # voidaan toteuttaa hakemalla kaikki ja suodattamalla koordinaattien mukaan.
    
    # Oikea tapa olisi hakea ensin asemat (metadata) bboxilla, jos API tukee, 
    # mutta pidetään tämä yksinkertaisena ja palautetaan placeholder-tieto.
    return ["Säädata vaatii tarkemman asemasuodatuksen (To do)"]
import requests

def calculate_bbox(route_coords):
    """
    Laskee reittipisteiden ympärille laatikon (Bounding Box).
    route_coords: lista tupleja [(lat, lon), (lat, lon), ...]
    Palauttaa stringin: "minLon,minLat,maxLon,maxLat"
    """
    if not route_coords:
        return None

    # Erotellaan lat ja lon omiin listoihinsa
    lats = [p[0] for p in route_coords]
    lons = [p[1] for p in route_coords]

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    # Lisätään pieni puskuri (buffer), jotta reitti ei leikkaudu aivan reunasta
    buffer = 0.05 # n. 5-10 km
    
    bbox = f"{min_lon - buffer},{min_lat - buffer},{max_lon + buffer},{max_lat + buffer}"
    return bbox

def traffic_messages_near_route(route_coords):
    """
    Hakee liikennehäiriöt reitin rajaamalta alueelta.
    """
    bbox = calculate_bbox(route_coords)
    if not bbox:
        return []

    url = f"https://tie.digitraffic.fi/api/traffic-message/v1/messages?bbox={bbox}"
    
    try:
        # Lisätään headerit kuten Fintraffic toivoo
        headers = { 
            "User-Agent": "StreamlitTrafficApp/1.0 (oma.sahkoposti@example.com)",
            "Accept-Encoding": "gzip"
        }
        
        resp = requests.get(url, headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            
            messages = []
            for feat in features:
                props = feat.get("properties", {})
                announcements = props.get("announcements", [])
                
                if announcements:
                    # Otetaan talteen tärkeimmät tiedot
                    info = {
                        "otsikko": announcements[0].get("title", "Ei otsikkoa"),
                        "kuvaus": announcements[0].get("features", [{}])[0].get("name", ""),
                        "sijainti": announcements[0].get("location", {}).get("description", ""),
                        "aika": announcements[0].get("location", {}).get("beginning", "")
                    }
                    messages.append(info)
            
            return messages
        else:
            print(f"Digitraffic virhe: {resp.status_code}")
            return []

    except Exception as e:
        print(f"Virhe Digitraffic-haussa: {e}")
        return []

def tms_near_route(route_coords):
    """
    Hakee sää- ja kelitiedot (Road Weather Stations) reitin alueelta.
    """
    bbox = calculate_bbox(route_coords)
    if not bbox:
        return []

    # Huom: Sääasemille käytetään eri endpointia
    url = "https://tie.digitraffic.fi/api/v3/data/road-weather-stations"
    # Digitrafficin v3 sää-API ei tue suoraan bboxia URL-parametrina samalla tavalla,
    # joten tässä haetaan kaikki ja suodatetaan (tai käytetään metadata-hakua).
    # Yksinkertaisuuden vuoksi tässä esimerkissä palautetaan tyhjä lista tai 
    # voidaan toteuttaa hakemalla kaikki ja suodattamalla koordinaattien mukaan.
    
    # Oikea tapa olisi hakea ensin asemat (metadata) bboxilla, jos API tukee, 
    # mutta pidetään tämä yksinkertaisena ja palautetaan placeholder-tieto.
    return ["Säädata vaatii tarkemman asemasuodatuksen (To do)"]