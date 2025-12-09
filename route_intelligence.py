"""
Route Intelligence Module
Kerää kaikki saatavilla oleva tieto reitiltä AI-analyysiä varten.
"""

from typing import Dict, List, Tuple, Any
import datetime
from digitraffic_client import (
    traffic_messages_near_route,
    get_road_weather_stations,
    get_lam_stations,
    get_maintenance_data
)


class RouteIntelligence:
    """Kerää ja tiivistää reittidatan AI-analyysiä varten"""
    
    def __init__(self, route_coords: List[Tuple[float, float]], departure_time: datetime.datetime):
        """
        Args:
            route_coords: Lista (lat, lon) koordinaatteja reitiltä
            departure_time: Lähtöaika
        """
        self.route_coords = route_coords
        self.departure_time = departure_time
        self.data = {}
    
    def collect_all_data(self) -> Dict[str, Any]:
        """Kerää kaikki saatavilla oleva tieto reitiltä"""
        print("🔍 Kerätään reittidataa...")
        
        try:
            # Digitraffic liikennetiedotteet
            self.data['digitraffic_messages'] = traffic_messages_near_route(self.route_coords)
            print(f"✅ Kerätty: {len(self.data['digitraffic_messages'])} liikennetiedotetta")
        except Exception as e:
            print(f"⚠️ Virhe liikennetiedotteiden haussa: {e}")
            self.data['digitraffic_messages'] = []
        
        try:
            # LAM-pisteet (liikennenopeudet)
            self.data['lam_data'] = get_lam_stations(self.route_coords)
            print(f"✅ Kerätty: {len(self.data['lam_data'])} LAM-pistettä")
        except Exception as e:
            print(f"⚠️ Virhe LAM-datan haussa: {e}")
            self.data['lam_data'] = []
        
        try:
            # Tiesääasemat
            self.data['road_weather'] = get_road_weather_stations(self.route_coords)
            print(f"✅ Kerätty: {len(self.data['road_weather'])} tiesääasemaa")
        except Exception as e:
            print(f"⚠️ Virhe tiesäädatan haussa: {e}")
            self.data['road_weather'] = []
        
        try:
            # Kunnossapito
            self.data['maintenance'] = get_maintenance_data(self.route_coords)
            print(f"✅ Kerätty: {len(self.data['maintenance'])} kunnossapitotehtävää")
        except Exception as e:
            print(f"⚠️ Virhe kunnossapitodatan haussa: {e}")
            self.data['maintenance'] = []
        
        return self.data
    
    def summarize_for_ai(self) -> str:
        """Tiivistää datan AI:lle sopivaan muotoon"""
        summary = []
        
        # Liikennetiedotteet
        if self.data.get('digitraffic_messages'):
            summary.append("LIIKENNETIEDOTTEET:")
            for msg in self.data['digitraffic_messages'][:5]:  # Max 5 tärkeintä
                msg_type = msg.get('type', 'Häiriö')
                msg_desc = msg.get('desc', 'Ei kuvausta')
                summary.append(f"- {msg_type}: {msg_desc}")
        else:
            summary.append("LIIKENNETIEDOTTEET: Ei häiriöitä reitillä")
        
        # LAM-pisteet (liikennenopeudet)
        if self.data.get('lam_data'):
            speeds = [lam.get('speed', 0) for lam in self.data['lam_data'] if lam.get('speed')]
            volumes = [lam.get('volume', 0) for lam in self.data['lam_data'] if lam.get('volume')]
            
            if speeds:
                avg_speed = sum(speeds) / len(speeds)
                min_speed = min(speeds)
                max_speed = max(speeds)
                summary.append(f"\nLIIKENNENOPEUS (LAM-mittaukset):")
                summary.append(f"- Keskiarvo: {avg_speed:.0f} km/h")
                summary.append(f"- Vaihteluväli: {min_speed:.0f} - {max_speed:.0f} km/h")
                summary.append(f"- Mittauspisteitä: {len(speeds)}")
            
            if volumes:
                avg_volume = sum(volumes) / len(volumes)
                summary.append(f"- Liikennemäärä: {avg_volume:.0f} ajoneuvoa/h")
        else:
            summary.append("\nLIIKENNENOPEUS: Ei mittaustietoa saatavilla")
        
        # Tiesää
        if self.data.get('road_weather'):
            summary.append("\nTIESÄÄ:")
            for station in self.data['road_weather'][:5]:  # Max 5 asemaa
                name = station.get('name', 'Tuntematon')
                air_temp = station.get('air_temp')
                road_temp = station.get('road_temp')
                
                temp_info = []
                if air_temp is not None:
                    temp_info.append(f"Ilma {air_temp}°C")
                if road_temp is not None:
                    temp_info.append(f"Tie {road_temp}°C")
                
                if temp_info:
                    summary.append(f"- {name}: {', '.join(temp_info)}")
        else:
            summary.append("\nTIESÄÄ: Ei tiesäätietoa saatavilla")
        
        # Kunnossapito
        if self.data.get('maintenance'):
            summary.append(f"\nKUNNOSSAPITO:")
            summary.append(f"- Aktiivisia toimenpiteitä reitillä: {len(self.data['maintenance'])}")
            
            # Ryhmittele tehtävät tyypin mukaan
            tasks = {}
            for m in self.data['maintenance']:
                task_type = m.get('task', 'Tuntematon')
                tasks[task_type] = tasks.get(task_type, 0) + 1
            
            for task_type, count in list(tasks.items())[:3]:  # Max 3 tyyppiä
                summary.append(f"  - {task_type}: {count} kpl")
        else:
            summary.append("\nKUNNOSSAPITO: Ei aktiivisia toimenpiteitä")
        
        return "\n".join(summary)
    
    def get_data_stats(self) -> Dict[str, int]:
        """Palauttaa tilastot kerätystä datasta"""
        return {
            'liikennetiedotteet': len(self.data.get('digitraffic_messages', [])),
            'lam_pisteet': len(self.data.get('lam_data', [])),
            'tiesaaasemat': len(self.data.get('road_weather', [])),
            'kunnossapito': len(self.data.get('maintenance', []))
        }
