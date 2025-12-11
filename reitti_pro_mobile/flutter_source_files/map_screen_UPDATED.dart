import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

class MapScreen extends StatefulWidget {
  final Map<String, dynamic>? routeData;

  const MapScreen({super.key, this.routeData});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  final MapController _mapController = MapController();
  List<LatLng> _routePoints = [];
  LatLng? _origin;
  LatLng? _destination;
  String _originName = '';
  String _destName = '';
  double _distance = 0;
  double _duration = 0;

  @override
  void initState() {
    super.initState();
    _loadRoute();
  }

  void _loadRoute() {
    if (widget.routeData != null) {
      final data = widget.routeData!;
      
      // Get coordinates
      final originLat = data['originLat'] ?? 60.1699;
      final originLon = data['originLon'] ?? 24.9384;
      final destLat = data['destLat'] ?? 61.4978;
      final destLon = data['destLon'] ?? 23.7610;
      
      setState(() {
        _origin = LatLng(originLat, originLon);
        _destination = LatLng(destLat, destLon);
        _routePoints = [_origin!, _destination!];
        _originName = data['origin'] ?? 'Lähtö';
        _destName = data['destination'] ?? 'Määränpää';
        _distance = data['distance'] ?? 179.0;
        _duration = data['duration'] ?? 120.0;
      });

      // Center map between origin and destination
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_origin != null && _destination != null) {
          final bounds = LatLngBounds.fromPoints([_origin!, _destination!]);
          _mapController.fitCamera(
            CameraFit.bounds(
              bounds: bounds,
              padding: const EdgeInsets.all(50),
            ),
          );
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Kartta'),
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: () {
              showDialog(
                context: context,
                builder: (context) => AlertDialog(
                  title: const Text('Reitin tiedot'),
                  content: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('📍 Lähtö: $_originName'),
                      Text('🏁 Määränpää: $_destName'),
                      const SizedBox(height: 12),
                      Text('📏 Matka: ${_distance.toStringAsFixed(1)} km'),
                      Text('⏱️ Aika: ${(_duration / 60).toStringAsFixed(0)} min'),
                    ],
                  ),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('Sulje'),
                    ),
                  ],
                ),
              );
            },
          ),
        ],
      ),
      body: _routePoints.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : Stack(
              children: [
                FlutterMap(
                  mapController: _mapController,
                  options: MapOptions(
                    initialCenter: _origin ?? LatLng(60.1699, 24.9384),
                    initialZoom: 7.0,
                    minZoom: 5.0,
                    maxZoom: 18.0,
                  ),
                  children: [
                    TileLayer(
                      urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                      userAgentPackageName: 'com.example.reitti_pro_mobile',
                    ),
                    if (_routePoints.isNotEmpty)
                      PolylineLayer(
                        polylines: [
                          Polyline(
                            points: _routePoints,
                            color: Colors.blue,
                            strokeWidth: 4.0,
                          ),
                        ],
                      ),
                    MarkerLayer(
                      markers: [
                        if (_origin != null)
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
                        if (_destination != null)
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
                      ],
                    ),
                  ],
                ),
                // Route info card
                Positioned(
                  top: 16,
                  left: 16,
                  right: 16,
                  child: Card(
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Row(
                            children: [
                              const Icon(Icons.route, size: 20),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  '$_originName → $_destName',
                                  style: const TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 16,
                                  ),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Row(
                            children: [
                              Icon(Icons.straighten, size: 16, color: Colors.grey[600]),
                              const SizedBox(width: 4),
                              Text('${_distance.toStringAsFixed(1)} km'),
                              const SizedBox(width: 16),
                              Icon(Icons.access_time, size: 16, color: Colors.grey[600]),
                              const SizedBox(width: 4),
                              Text('${(_duration / 60).toStringAsFixed(0)} min'),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
      floatingActionButton: Column(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
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
          FloatingActionButton(
            heroTag: 'fit_bounds',
            child: const Icon(Icons.fit_screen),
            onPressed: () {
              if (_origin != null && _destination != null) {
                final bounds = LatLngBounds.fromPoints([_origin!, _destination!]);
                _mapController.fitCamera(
                  CameraFit.bounds(
                    bounds: bounds,
                    padding: const EdgeInsets.all(50),
                  ),
                );
              }
            },
          ),
        ],
      ),
    );
  }
}
