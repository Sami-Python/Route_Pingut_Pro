import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:go_router/go_router.dart';
import 'package:latlong2/latlong.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:reitti_pro_mobile/data/services/api_client.dart';
import 'package:reitti_pro_mobile/data/services/share_service.dart';
import 'package:reitti_pro_mobile/presentation/widgets/route_info_card.dart';

class RoutePreview {
  final List<LatLng> coordinates;
  final double distanceKm;
  final double durationHours;
  
  RoutePreview({required this.coordinates, required this.distanceKm, required this.durationHours});
}

class MapScreen extends ConsumerStatefulWidget {
  final Map<String, dynamic>? routeData;

  const MapScreen({super.key, this.routeData});

  @override
  ConsumerState<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends ConsumerState<MapScreen> {
  // Route State
  final MapController _mapController = MapController();
  List<RoutePreview> _allRoutes = []; // Changed from List<List<LatLng>>
  int _selectedRouteIndex = 0;
  
  LatLng? _origin;
  LatLng? _destination;
  List<Marker> _baseMarkers = [];
  
  // Layers State
  bool _showCameras = false;
  bool _showRoadWeather = false;
  bool _showLam = false;
  bool _showRainRadar = false; // New state
  int? _radarTimestamp;        // New state
  bool _showRouteWeather = true; // Default ON for new feature
  
  List<Marker> _cameraMarkers = [];
  List<Marker> _weatherMarkers = [];
  List<Marker> _lamMarkers = [];
  List<Marker> _routeWeatherMarkers = [];
  
  // New Layers
  bool _showTrafficMessages = false;
  bool _showTrafficIncidents = false;
  List<Marker> _trafficMessageMarkers = [];
  List<Marker> _trafficIncidentMarkers = [];

  // Warnings
  List<String> _activeWarnings = [];


  @override
  void initState() {
    super.initState();
    _loadRoute();
    // Delay fetch to ensure widget is built
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _fetchLayers(); // Existing layers
      _fetchRouteWeather(); // New Route Weather
    });
  }

  void _loadRoute() {
    if (widget.routeData == null) return;

    final data = widget.routeData!;
    
    // Parse alternatives if available, otherwise just use the main coordinates
    List<RoutePreview> parsedRoutes = [];
    
    if (data['alternatives'] != null) {
      final List<dynamic> alts = data['alternatives'];
      for (var alt in alts) {
        if (alt['coordinates'] != null) {
          final List<dynamic> coords = alt['coordinates'];
          final points = coords.map((c) => LatLng(c[0] as double, c[1] as double)).toList();
          parsedRoutes.add(RoutePreview(
            coordinates: points,
            distanceKm: (alt['distance_km'] ?? 0).toDouble(),
            durationHours: (alt['duration_hours'] ?? 0).toDouble(),
          ));
        }
      }
    } else if (data['coordinates'] != null) {
      // Fallback for single route
      final List<dynamic> coords = data['coordinates'];
      final points = coords.map((c) => LatLng(c[0] as double, c[1] as double)).toList();
      parsedRoutes.add(RoutePreview(
            coordinates: points,
            distanceKm: (data['distance_km'] ?? 0).toDouble(),
            durationHours: (data['duration_hours'] ?? 0).toDouble(),
      ));
    }

    if (parsedRoutes.isNotEmpty) {
      setState(() {
        _allRoutes = parsedRoutes;
        _selectedRouteIndex = 0; // Default to first (best) route
        
        // Origin/Dest from the first route
        if (_allRoutes[0].coordinates.isNotEmpty) {
           _origin = _allRoutes[0].coordinates.first;
           _destination = _allRoutes[0].coordinates.last;
        }
          
          _baseMarkers = [
            Marker(
              point: _origin!,
              width: 40,
              height: 40,
              child: const Icon(
                Icons.location_on,
                color: Colors.green,
                size: 40,
              ),
            ),
            Marker(
              point: _destination!,
              width: 40,
              height: 40,
              child: const Icon(
                Icons.flag,
                color: Colors.red,
                size: 40,
              ),
            ),
          ];
        });
        
        // Fit bounds after build
        WidgetsBinding.instance.addPostFrameCallback((_) {
          _fitBounds();
        });
    }
  }

  void _fitBounds() {
    if (_allRoutes.isEmpty || _allRoutes[_selectedRouteIndex].coordinates.isEmpty) return;
    
    final bounds = LatLngBounds.fromPoints(_allRoutes[_selectedRouteIndex].coordinates);
    _mapController.fitCamera(
      CameraFit.bounds(
        bounds: bounds,
        padding: const EdgeInsets.all(50),
      ),
    );
  }

  Future<void> _fetchLayers() async {
    final center = _mapController.camera.center;
    final apiClient = ref.read(apiClientProvider);
    
    // Check if we have a route polyline
    final String? routePolyline = widget.routeData?['polyline'];

    if (_showCameras) {
      try {
        final cameras = await apiClient.getWeatherCameras(
          lat: center.latitude,
          lon: center.longitude,
          polyline: routePolyline,
          radius: 50.0,
        );
        
        setState(() {
          _cameraMarkers = cameras.map((c) {
            return Marker(
              point: LatLng(c['lat'], c['lon']),
              width: 30,
              height: 30,
              child: GestureDetector(
                onTap: () => _showCameraDialog(c),
                child: const Icon(Icons.camera_alt, color: Colors.orange, size: 24),
              ),
            );
          }).toList();
        });
      } catch (e) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Virhe kameroiden haussa: $e')));
      }
    } else {
      setState(() => _cameraMarkers = []);
    }

    if (_showRoadWeather) {
      try {
        final stations = await apiClient.getRoadWeather(
          lat: center.latitude,
          lon: center.longitude,
          polyline: routePolyline,
          radius: 50.0,
        );

        setState(() {
          _weatherMarkers = stations.map((s) {
            return Marker(
              point: LatLng(s['lat'], s['lon']),
              width: 30,
              height: 30,
              child: GestureDetector(
                onTap: () => _showWeatherDialog(s),
                child: const Icon(Icons.thermostat, color: Colors.blue, size: 24),
              ),
            );
          }).toList();
        });
      } catch (e) {
         if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Virhe tiesään haussa: $e')));
      }
    } else {
      setState(() => _weatherMarkers = []);
    }

    if (_showLam) {
       try {
        final lams = await apiClient.getLAMStations(
          lat: center.latitude,
          lon: center.longitude,
          polyline: routePolyline,
          radius: 50.0,
        );

        setState(() {
          _lamMarkers = lams.map((l) {
            return Marker(
              point: LatLng(l['lat'], l['lon']),
              width: 30,
              height: 30,
              child: GestureDetector(
                onTap: () => _showLamDialog(l),
                child: const Icon(Icons.directions_car, color: Colors.purple, size: 24),
              ),
            );
          }).toList();
        });
      } catch (e) {
         if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Virhe LAM-pisteiden haussa: $e')));
      }
    } else {
      setState(() => _lamMarkers = []);
    }

    // Rain Radar Timestamp
    if (_showRainRadar && _radarTimestamp == null) {
      try {
        print('🌧️ [MapScreen] Fetching RainViewer config...');
        final config = await apiClient.getRadarConfig();
        print('🌧️ [MapScreen] RainViewer config: $config');
        
        if (config.containsKey('radar') && config['radar']['past'] != null) {
           final List<dynamic> past = config['radar']['past'];
           if (past.isNotEmpty) {
             final latest = past.last;
             print('🌧️ [MapScreen] Latest radar timestamp: ${latest['time']}');
             setState(() {
               _radarTimestamp = latest['time'];
             });
           } else {
             print('⚠️ [MapScreen] No past radar data found.');
           }
        } else {
           print('⚠️ [MapScreen] Invalid radar config structure.');
        }
      } catch (e) {
        print('❌ [MapScreen] Error fetching radar config: $e');
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Virhe tutkakuvan haussa: $e')));
      }
    }
    
    // Traffic Messages (Digitraffic)
    if (_showTrafficMessages) {
      try {
        final messages = await apiClient.getTrafficMessages(
          lat: center.latitude, 
          lon: center.longitude, 
          polyline: routePolyline,
          radius: 50.0
        );
        
        setState(() {
          _trafficMessageMarkers = messages.map((m) {
            return Marker(
              point: LatLng(m['lat'], m['lon']),
              width: 30,
              height: 30,
              child: GestureDetector(
                onTap: () => _showTrafficMessageDialog(m),
                child: const Icon(Icons.warning_amber_rounded, color: Colors.orangeAccent, size: 28),
              ),
            );
          }).toList();
        });
      } catch (e) {
         if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Virhe viestien haussa: $e')));
      }
      setState(() => _trafficMessageMarkers = []);
    }

    // Traffic Incidents (HERE Route Data)
    if (_showTrafficIncidents && widget.routeData != null && widget.routeData!['incidents'] != null) {
      final List<dynamic> incidents = widget.routeData!['incidents'];
      
      setState(() {
        _trafficIncidentMarkers = incidents.map((i) {
           return Marker(
              point: LatLng(i['lat'], i['lon']),
              width: 30,
              height: 30,
              child: GestureDetector(
                onTap: () => _showIncidentDialog(i),
                child: const Icon(Icons.error, color: Colors.redAccent, size: 28),
              ),
            );
        }).toList();
      });
    } else {
       setState(() => _trafficIncidentMarkers = []);
    }
  }

  Future<void> _fetchRouteWeather() async {
    if (!_showRouteWeather || _allRoutes.isEmpty) {
      setState(() => _routeWeatherMarkers = []);
      return;
    }

    try {
      final route = _allRoutes[_selectedRouteIndex];
      final points = route.coordinates;
      final distKm = route.distanceKm;
      final durationHours = route.durationHours;
      
      if (points.isEmpty) return;
      
      // Determine sample points
      List<LatLng> samples = [];
      List<double> progress = []; // 0.0 to 1.0

      if (durationHours < 1.0) {
        // Short trip: Only Start (0%) and End (100%)
        samples = [points.first, points.last];
        progress = [0.0, 1.0];
      } else {
        // Long trip: Start, 25%, 50%, 75%, End
        samples = [points.first];
        progress = [0.0];
        
        // Simple sampling by index (assuming roughly uniform distribution of points)
        // A better way would be by distance, but index is fast approximation for now.
        final int len = points.length;
        if (len > 4) {
          samples.add(points[(len * 0.25).round()]);
          progress.add(0.25);
          samples.add(points[(len * 0.50).round()]);
          progress.add(0.50);
          samples.add(points[(len * 0.75).round()]);
          progress.add(0.75);
        }
        
        samples.add(points.last);
        progress.add(1.0);
      }
      
      // Calculate times and build request
      final startTimeStr = widget.routeData?['departureTime'] ?? DateTime.now().toIso8601String();
      final startTime = DateTime.tryParse(startTimeStr) ?? DateTime.now();
      
      List<Map<String, dynamic>> requests = [];
      for (int i = 0; i < samples.length; i++) {
        final double p = progress[i];
        
        // Calculate estimated time at this point
        // T = Start + (Duration * Progress)
        final timeOffsetSeconds = (durationHours * 3600 * p).round();
        final pointTime = startTime.add(Duration(seconds: timeOffsetSeconds));
        
        requests.add({
          'lat': samples[i].latitude,
          'lon': samples[i].longitude,
          'time': pointTime.toIso8601String(),
        });
      }
      
      // Fetch batch weather
      final apiClient = ref.read(apiClientProvider);
      final results = await apiClient.getBatchWeather(requests);
      
      // Create Markers
      List<Marker> newMarkers = [];
      List<String> currentWarnings = [];

      for (var result in results) {
        final data = result['data'];
        final lat = result['coordinates']['lat'];
        final lon = result['coordinates']['lon'];
        
        if (data != null && data['weather'] != 'virhe') {
           newMarkers.add(Marker(
             point: LatLng(lat, lon),
             width: 60, // Wide for icon + text
             height: 60,
             child: GestureDetector(
               onTap: () => _showRouteWeatherDialog(data, result['time']),
               child: Column(
                 mainAxisSize: MainAxisSize.min,
                 children: [
                   Container(
                     padding: const EdgeInsets.all(4),
                     decoration: BoxDecoration(
                       color: Colors.white.withOpacity(0.9),
                       borderRadius: BorderRadius.circular(8),
                       boxShadow: const [BoxShadow(blurRadius: 4, color: Colors.black26)],
                     ),
                     child: Column(
                       children: [
                         // Weather Icon (approximation based on description/precip)
                         Icon(
                           _getWeatherIcon(data['precipitation'] ?? 0, data['temperature'] ?? 0),
                           size: 20,
                           color: Colors.blueGrey,
                         ),
                         Text(
                           "${data['temperature']}°",
                           style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 10),
                         )
                       ],
                     ),
                   ),
                   // Triangle pointer (optional simple styling)
                   // Icon(Icons.arrow_drop_down, size: 16, color: Colors.white),
                 ],
               ),
             ),
           ));
         
           // Check for Warnings
           // 1. Heavy Rain
           if ((data['precipitation'] ?? 0) > 2.0 && !currentWarnings.contains('rankkasade')) {
             currentWarnings.add('rankkasade');
           }
           // 2. Slippery/Ice (Temp < 1 and precipitating)
           if ((data['temperature'] ?? 0) < 1 && (data['precipitation'] ?? 0) > 0 && !currentWarnings.contains('liukas')) {
             currentWarnings.add('liukas');
           }
           // 3. High Wind
           if ((data['wind_speed'] ?? 0) > 15 && !currentWarnings.contains('tuuli')) {
             currentWarnings.add('tuuli');
           }
        }
      }
      
      setState(() {
        _routeWeatherMarkers = newMarkers;
        _activeWarnings = currentWarnings;
      });
    } catch (e) {
      print('Failed to calculate route weather: $e');
    }
  }

  IconData _getWeatherIcon(num precipitation, num temperature) {
    if (precipitation > 0.5) return Icons.umbrella; // Rain
    if (precipitation > 0.1) return Icons.grain;    // Drizzle
    if (temperature > 20) return Icons.wb_sunny;    // Sunny/Hot
    if (temperature > 5) return Icons.cloud;        // Cloudy
    return Icons.ac_unit;                           // Cold/Snow
  }

  void _showRouteWeatherDialog(Map<String, dynamic> data, String? timeIso) {
    String timeStr = "Arvioitu aika";
    if (timeIso != null) {
      try {
        final dt = DateTime.parse(timeIso);
        // Add 2 hours for basic timezone fix if needed, or rely on local
        // Here we just format cleanly
        timeStr = "${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}";
      } catch (e) {
        // keep default
      }
    }

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(
               _getWeatherIcon(data['precipitation'] ?? 0, data['temperature'] ?? 0),
               color: Colors.blue,
            ),
            const SizedBox(width: 8),
            const Text("Sää reitillä"),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
             Text("📍 Arvioitu aika: $timeStr", style: const TextStyle(fontWeight: FontWeight.bold)),
             const SizedBox(height: 8),
             Text("🌡️ Lämpötila: ${data['temperature']} °C"),
             Text("🌧️ Sademäärä: ${data['precipitation']} mm"),
             Text("💨 Tuuli: ${data['wind_speed'] ?? '-'} m/s"),
             Text("📝 Kuvaus: ${data['weather']}"),
          ],
        ),
        actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Sulje'))],
      ),
    );
  }



  void _showWarningLegend() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Row(children: [Icon(Icons.info_outline, color: Colors.blue), SizedBox(width: 8), Text("Varoitusten selite")]),
        content: const Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ListTile(leading: Icon(Icons.umbrella, color: Colors.blue), title: Text("Rankkasade"), subtitle: Text("> 2.0 mm/h")),
            ListTile(leading: Icon(Icons.ac_unit, color: Colors.cyan), title: Text("Liukas keli"), subtitle: Text("Lämpötila < 1°C ja sadetta")),
            ListTile(leading: Icon(Icons.air, color: Colors.grey), title: Text("Kova tuuli"), subtitle: Text("> 15 m/s")),
          ],
        ),
        actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Sulje'))],
      ),
    );
  }

  void _showCameraDialog(Map<String, dynamic> camera) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(camera['name'] ?? 'Kelikamera'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (camera['imageUrl'] != null) ...[
                Image.network(
                  camera['imageUrl'],
                  loadingBuilder: (context, child, loadingProgress) {
                    if (loadingProgress == null) return child;
                    return Center(
                      child: CircularProgressIndicator(
                        value: loadingProgress.expectedTotalBytes != null
                            ? loadingProgress.cumulativeBytesLoaded / loadingProgress.expectedTotalBytes!
                            : null,
                      ),
                    );
                  },
                  errorBuilder: (context, error, stackTrace) {
                    return const Column(
                      children: [
                        Icon(Icons.error, color: Colors.red, size: 48),
                        SizedBox(height: 8),
                        Text('Kuvan lataus epäonnistui'),
                      ],
                    );
                  },
                ),
                const SizedBox(height: 8),
              ] else
                const Text('Ei kuvaa saatavilla'),
              Text('Sijainti: ${camera['lat']?.toStringAsFixed(4)}, ${camera['lon']?.toStringAsFixed(4)}',
                  style: const TextStyle(fontSize: 12, color: Colors.grey)),
            ],
          ),
        ),
        actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Sulje'))],
      ),
    );
  }

  void _showWeatherDialog(Map<String, dynamic> station) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(station['name'] ?? 'Sääasema'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Ilma: ${station['air_temp']} °C'),
            Text('Tie: ${station['road_temp']} °C'),
          ],
        ),
        actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Sulje'))],
      ),
    );
  }

  void _showLamDialog(Map<String, dynamic> lam) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(lam['name'] ?? 'Liikennemäärä'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Nopeus: ${lam['speed']} km/h'),
            Text('Määrä: ${lam['volume']} ajon/h'),
          ],
        ),
        actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Sulje'))],
      ),
    );
  }

  void _showTrafficMessageDialog(Map<String, dynamic> msg) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(msg['otsikko'] ?? 'Liikennetiedote'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(msg['kuvaus'] ?? ''),
            const SizedBox(height: 8),
            Text('Alue: ${msg['sijainti']}', style: const TextStyle(fontWeight: FontWeight.bold)),
            Text('Aika: ${msg['aika']}', style: const TextStyle(fontSize: 12, color: Colors.grey)),
          ],
        ),
        actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Sulje'))],
      ),
    );
  }

  void _showIncidentDialog(Map<String, dynamic> incident) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(incident['tyyppi'] ?? 'Liikennehäiriö'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(incident['kuvaus'] ?? 'Ei kuvausta'),
            const SizedBox(height: 8),
            Text('Vakavuus: ${incident['taso']}', style: const TextStyle(fontWeight: FontWeight.bold)),
          ],
        ),
        actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Sulje'))],
      ),
    );
  }

  Future<void> _analyzeRoute() async {
    if (widget.routeData == null) return;
    
    // Show loading
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => const Center(child: CircularProgressIndicator()),
    );

    try {
      final analysis = await ref.read(apiClientProvider).analyzeRoute(widget.routeData!);
      if (!mounted) return;
      Navigator.pop(context); // Close loading

      // Show result
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Row(
            children: [
               Icon(Icons.auto_awesome, color: Colors.orangeAccent),
               SizedBox(width: 8),
               Text("AI Analyysi"),
            ],
          ),
          content: SingleChildScrollView(
            child: Text(analysis, style: const TextStyle(fontSize: 16, height: 1.5)),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Sulje")),
          ],
        ),
      );
    } catch (e) {
      if (mounted) Navigator.pop(context); // Close loading
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Virhe: $e")));
    }
  }

  Future<void> _shareRoute() async {
    if (widget.routeData == null) return;

    try {
      final data = widget.routeData!;
      final distKm = (data['distance_km'] ?? 0).toDouble();
      final durHours = (data['duration_hours'] ?? 0).toDouble();
      
      // Try to get origin and destination names from route data
      final origin = data['origin'] ?? 'Lähtöpaikka';
      final destination = data['destination'] ?? 'Määränpää';
      
      await ShareService.shareRoute(
        origin: origin,
        destination: destination,
        distanceKm: distKm,
        durationHours: durHours,
        departureTime: DateTime.now(), // Use current time as default
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Jakaminen epäonnistui: $e")),
        );
      }
    }
  }

  void _showLayerMenu() {
    showModalBottomSheet(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setModalState) => Container(
          padding: const EdgeInsets.all(16),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text("Karttatasot", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                SwitchListTile(
                  title: const Text("Kelikamerat"),
                  value: _showCameras,
                  onChanged: (val) {
                    setModalState(() => _showCameras = val);
                    setState(() => _showCameras = val);
                    _fetchLayers();
                  },
                ),
                SwitchListTile(
                  title: const Text("Tiesää"),
                  value: _showRoadWeather,
                  onChanged: (val) {
                    setModalState(() => _showRoadWeather = val);
                    setState(() => _showRoadWeather = val);
                    _fetchLayers();
                  },
                ),
                SwitchListTile(
                  title: const Text("LAM / Liikennemäärät"),
                  value: _showLam,
                  onChanged: (val) {
                    setModalState(() => _showLam = val);
                    setState(() => _showLam = val);
                    _fetchLayers();
                  },
                ),
                SwitchListTile(
                  title: const Text("Saderintama (RainViewer)"),
                  value: _showRainRadar,
                  onChanged: (val) {
                    setModalState(() => _showRainRadar = val);
                    setState(() => _showRainRadar = val);
                    _fetchLayers();
                  },
                ),
                SwitchListTile(
                  title: const Text("Matkan sää (Ikonit)"),
                  secondary: const Icon(Icons.wb_sunny),
                  value: _showRouteWeather,
                  onChanged: (val) {
                    setModalState(() => _showRouteWeather = val);
                    setState(() => _showRouteWeather = val);
                    _fetchRouteWeather();
                  },
                ),
                const Divider(),
                const Text("Liikenne", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                SwitchListTile(
                  title: const Text("Liikennetiedotteet"),
                  value: _showTrafficMessages,
                  onChanged: (val) {
                    setModalState(() => _showTrafficMessages = val);
                    setState(() => _showTrafficMessages = val);
                    _fetchLayers();
                  },
                ),
                SwitchListTile(
                  title: const Text("Liikennehäiriöt (HERE)"),
                  value: _showTrafficIncidents,
                  onChanged: (val) {
                    setModalState(() => _showTrafficIncidents = val);
                    setState(() => _showTrafficIncidents = val);
                    _fetchLayers(); // Add this line to load incidents
                  },
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final hasRoute = widget.routeData != null;
    double distKm = 0;
    double durHours = 0;
    DateTime depTime = DateTime.now();

    if (hasRoute) {
      // Use selected route metadata if available, otherwise fallback (initially 0 mostly)
      if (_allRoutes.isNotEmpty && _selectedRouteIndex < _allRoutes.length) {
         distKm = _allRoutes[_selectedRouteIndex].distanceKm;
         durHours = _allRoutes[_selectedRouteIndex].durationHours;
      } else {
         distKm = (widget.routeData!['distance_km'] ?? 0).toDouble();
         durHours = (widget.routeData!['duration_hours'] ?? 0).toDouble();
      }
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('🐧 Pingut - Kartta'),
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            tooltip: 'Merkkien selite',
            onPressed: _showWarningLegend,
          ),
          IconButton(
            icon: const Icon(Icons.layers),
            onPressed: _showLayerMenu,
          ),
        ],
      ),
      body: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: _origin ?? const LatLng(60.1699, 24.9384),
              initialZoom: 7.0,
              minZoom: 5.0,
              maxZoom: 18.0,
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.example.reitti_pro_mobile',
              ),
                if (_showRainRadar && _radarTimestamp != null)
                Opacity(
                  opacity: 0.7,
                  child: TileLayer(
                    urlTemplate: 'https://tilecache.rainviewer.com/v2/radar/$_radarTimestamp/256/{z}/{x}/{y}/2/1_1.png',
                    userAgentPackageName: 'com.example.reitti_pro_mobile',
                    backgroundColor: Colors.transparent,
                  ),
                ),
              if (_showTrafficIncidents)
                 TileLayer(
                   urlTemplate: ref.read(apiClientProvider).getTrafficTileUrlTemplate(),
                   userAgentPackageName: 'com.example.reitti_pro_mobile',
                   backgroundColor: Colors.transparent,
                 ),
              PolylineLayer(
                polylines: [
                  // Draw alternative routes first (background)
                  for (int i = 0; i < _allRoutes.length; i++)
                    if (i != _selectedRouteIndex)
                      Polyline(
                        points: _allRoutes[i].coordinates,
                        color: Colors.grey.withOpacity(0.8),
                        strokeWidth: 5.0,
                        isDotted: true, // Optional: make alternatives dotted
                      ),
                      
                  // Draw selected route (foreground)
                  if (_allRoutes.isNotEmpty && _allRoutes[_selectedRouteIndex].coordinates.isNotEmpty)
                    Polyline(
                      points: _allRoutes[_selectedRouteIndex].coordinates,
                      color: Colors.blue,
                      strokeWidth: 5.0,
                    ),
                ],
              ),
              MarkerLayer(markers: [
                ..._baseMarkers,
                ..._cameraMarkers,
                ..._weatherMarkers,
                ..._lamMarkers,
                ..._trafficMessageMarkers,
                ..._trafficIncidentMarkers,
                ..._routeWeatherMarkers,
              ]),
            ],
          ),
          
          // Route Selector Chips (Top Center)
          if (_allRoutes.length > 1)
            Positioned(
              top: 10,
              left: 0,
              right: 0,
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: List.generate(_allRoutes.length, (index) {
                    final isSelected = index == _selectedRouteIndex;
                    return Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 4),
                      child: FilterChip(
                        label: Text('Reitti ${index + 1}'),
                        selected: isSelected,
                        onSelected: (bool selected) {
                          if (selected) {
                            setState(() {
                              _selectedRouteIndex = index;
                              _fitBounds();
                              _fetchLayers(); // Refresh layers for new route path (cameras etc.)
                            });
                          }
                        },
                        selectedColor: Colors.blue.shade100,
                        checkmarkColor: Colors.blue,
                      ),
                    );
                  }),
                ),
              ),
            ),

          // Custom FAB Column Positioned
          Positioned(
            right: 16,
            bottom: hasRoute ? 220 : 16, // Lift up if card is showing
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                FloatingActionButton(
                  heroTag: 'refresh_layers',
                  mini: true,
                  child: const Icon(Icons.refresh),
                  onPressed: _fetchLayers,
                  tooltip: 'Päivitä alueen tiedot',
                ),
                const SizedBox(height: 8),
                FloatingActionButton(
                  heroTag: 'zoom_in',
                  mini: true,
                  child: const Icon(Icons.add),
                  onPressed: () {
                    _mapController.move(
                      _mapController.camera.center,
                      _mapController.camera.zoom + 1,
                    );
                  },
                ),
                const SizedBox(height: 8),
                FloatingActionButton(
                  heroTag: 'zoom_out',
                  mini: true,
                  child: const Icon(Icons.remove),
                  onPressed: () {
                    _mapController.move(
                      _mapController.camera.center,
                      _mapController.camera.zoom - 1,
                    );
                  },
                ),
                const SizedBox(height: 8),
                if (_allRoutes.isNotEmpty)
                  FloatingActionButton(
                    heroTag: 'fit_bounds',
                    child: const Icon(Icons.crop_free),
                    onPressed: _fitBounds,
                  ),
              ],
            ),
          ),

          // Warnings Pill (Floating above card)
          if (_activeWarnings.isNotEmpty && hasRoute)
            Positioned(
              left: 16,
              bottom: 220, 
              child: GestureDetector(
                onTap: () {
                   showDialog(
                     context: context,
                     builder: (ctx) => AlertDialog(
                       title: const Text("⚠️ Reittivaroitukset"),
                       content: Column(
                         mainAxisSize: MainAxisSize.min,
                         crossAxisAlignment: CrossAxisAlignment.start,
                         children: _activeWarnings.map((w) {
                           String text = w;
                           IconData icon = Icons.warning;
                           if (w == 'rankkasade') { text = "Rankkasadetta (>2mm/h)"; icon = Icons.umbrella; }
                           if (w == 'liukas') { text = "Liukasta (sade + pakkanen)"; icon = Icons.ac_unit; }
                           if (w == 'tuuli') { text = "Kovaa tuulta (>15m/s)"; icon = Icons.air; }
                           return ListTile(leading: Icon(icon, color: Colors.orange), title: Text(text));
                         }).toList(),
                       ),
                       actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("OK"))],
                     )
                   );
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: Colors.redAccent,
                    borderRadius: BorderRadius.circular(20),
                    boxShadow: const [BoxShadow(blurRadius: 4, color: Colors.black26)],
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.warning_amber_rounded, color: Colors.white),
                      const SizedBox(width: 8),
                      Text(
                        "${_activeWarnings.length} Varoitusta",
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ),
              ),
            ),

          // Route Info Card Overlay
          if (hasRoute)
            Positioned(
              left: 0,
              right: 0,
              bottom: 0,
              child: SafeArea( // Ensure it doesn't hit home bar
                child: RouteInfoCard(
                  key: ValueKey(_selectedRouteIndex), // Force rebuild when route changes
                  distanceKm: distKm,
                  durationHours: durHours,
                  departureTime: depTime,
                  onAnalyzePressed: _analyzeRoute,
                  onSharePressed: _shareRoute,
                  onDetailsPressed: () {
                    if (widget.routeData != null) {
                      context.pushNamed('route-details', extra: widget.routeData);
                    }
                  },
                ),
              ),
            ),
        ],
      ),
    );
  }
}
