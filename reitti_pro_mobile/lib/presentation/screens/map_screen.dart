import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
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
  List<Marker> _cameraMarkers = [];
  List<Marker> _weatherMarkers = [];
  List<Marker> _lamMarkers = [];
  
  // New Layers
  bool _showTrafficMessages = false;
  bool _showTrafficIncidents = false;
  List<Marker> _trafficMessageMarkers = [];
  List<Marker> _trafficIncidentMarkers = [];

  @override
  void initState() {
    super.initState();
    _loadRoute();
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
    } else {
      setState(() => _trafficMessageMarkers = []);
    }

    // Traffic Incidents (HERE Route Data)
    if (_showTrafficIncidents && widget.routeData != null && widget.routeData!['incidents'] != null) {
      final List<dynamic> incidents = widget.routeData!['incidents'];
      
      setState(() {
        // We reuse _trafficMessageMarkers list or create a new one? 
        // Let's allow both Digitraffic AND HERE markers if both toggles are on.
        // Wait, _trafficMessageMarkers is for Digitraffic. We need a list for HERE incidents.
        // But in build method we only have _trafficMessageMarkers.
        // Let's add _trafficIncidentMarkers to state.
        
        // Actually, let's just create the markers and add them to a new list _trafficIncidentMarkers
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
                ),
              ),
            ),
        ],
      ),
    );
  }
}
