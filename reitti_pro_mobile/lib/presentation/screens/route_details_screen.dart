import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/services/api_client.dart';

class RouteDetailsScreen extends ConsumerStatefulWidget {
  final Map<String, dynamic> routeData;

  const RouteDetailsScreen({super.key, required this.routeData});

  @override
  ConsumerState<RouteDetailsScreen> createState() => _RouteDetailsScreenState();
}

class _RouteDetailsScreenState extends ConsumerState<RouteDetailsScreen> {
  bool _isLoadingWeather = true;
  Map<String, dynamic>? _weatherData;

  @override
  void initState() {
    super.initState();
    _fetchWeather();
  }

  Future<void> _fetchWeather() async {
    try {
      print('❄️ [RouteDetailsScreen] Fetching weather...');
      print('📦 [RouteDetailsScreen] Route Data: ${widget.routeData}');
      
      final coordinates = widget.routeData['coordinates'] as List;
      if (coordinates.isEmpty) {
        print('❌ [RouteDetailsScreen] No coordinates found!');
        return;
      }

      final fromPoint = coordinates.first;
      final toPoint = coordinates.last;
      
      // Use injected departureTime or default to now
      final String departureTime = widget.routeData['departureTime'] ?? DateTime.now().toIso8601String();
      print('🕒 [RouteDetailsScreen] Departure Time: $departureTime');

      final client = ref.read(apiClientProvider);
      final weather = await client.getRouteWeather(
        fromLat: fromPoint[0],
        fromLon: fromPoint[1],
        toLat: toPoint[0],
        toLon: toPoint[1],
        departureTime: departureTime,
      );

      print('✅ [RouteDetailsScreen] Weather fetched: $weather');

      if (mounted) {
        setState(() {
          _weatherData = weather;
          _isLoadingWeather = false;
        });
      }
    } catch (e) {
      print('❌ [RouteDetailsScreen] Error fetching weather: $e');
      if (mounted) {
        setState(() => _isLoadingWeather = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Reitin tiedot'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Route summary card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Yhteenveto',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),
                    _buildInfoRow(
                      Icons.straighten,
                      'Matka',
                      '${widget.routeData['distance_km']?.toStringAsFixed(1) ?? widget.routeData['distance'] ?? 'N/A'} km',
                    ),
                    _buildInfoRow(
                      Icons.access_time,
                      'Ajoaika',
                      '${widget.routeData['duration_hours']?.toStringAsFixed(1) ?? widget.routeData['duration'] ?? 'N/A'} h',
                    ),
                    _buildInfoRow(
                      Icons.schedule,
                      'Lähtö',
                      widget.routeData['departure'] ?? 'N/A',
                    ),
                    _buildInfoRow(
                      Icons.flag,
                      'Perillä',
                      widget.routeData['arrival'] ?? 'N/A',
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Weather info
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      '🌤️ Sää reitillä',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 12),
                    if (_isLoadingWeather)
                       const Padding(
                         padding: EdgeInsets.all(8.0),
                         child: Center(child: CircularProgressIndicator()),
                       )
                    else if (_weatherData == null || _weatherData!.isEmpty)
                      const Text('Säätietoja ei saatavilla')
                    else
                      Column(
                        children: [
                          _buildWeatherRow(
                            'Lähtö', 
                            _weatherData!['departure']['city'] ?? 'Lähtöpiste',
                            _weatherData!['departure']['current']
                          ),
                          const Divider(),
                          _buildWeatherRow(
                            'Perillä', 
                            _weatherData!['arrival']['city'] ?? 'Määränpää',
                            _weatherData!['arrival']['current'] // Note: Ideally should pick from forecast based on arrival time
                          ),
                          const SizedBox(height: 8),
                          if (_weatherData!['departure']['forecast'] != null)
                             Text(
                               'Ennuste tarkempiin aikoihin viittaa API-vastaukseen.', 
                               style: TextStyle(fontSize: 12, color: Colors.grey[600])
                             ),
                        ],
                      ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Traffic info
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      '⚠️ Liikennetiedotteet',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 12),
                    const Text('Ei aktiivisia tiedotteita'),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Start navigation button
            ElevatedButton.icon(
              icon: const Icon(Icons.navigation),
              label: const Text('Aloita navigointi'),
              onPressed: () {
                // TODO: Start navigation
              },
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.all(16),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildWeatherRow(String label, String location, Map<String, dynamic>? data) {
    if (data == null) return const SizedBox.shrink();
    
    final temp = data['temperature'];
    final desc = data['weather'];
    // Simple mapping for icon based on description or data
    // For now just use cloud
    IconData icon = Icons.cloud;
    if (desc.toString().contains('aurinko')) icon = Icons.wb_sunny;
    if (desc.toString().contains('sade')) icon = Icons.umbrella;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.grey)),
                Text(location, style: const TextStyle(fontSize: 16)),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Row(
                children: [
                  Icon(icon, size: 20, color: Colors.blue),
                  const SizedBox(width: 8),
                  Text('$temp°C', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                ],
              ),
              Text(desc.toString(), style: const TextStyle(fontSize: 14)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Icon(icon, size: 20),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              label,
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
          Text(
            value,
            style: const TextStyle(fontSize: 16),
          ),
        ],
      ),
    );
  }
}
