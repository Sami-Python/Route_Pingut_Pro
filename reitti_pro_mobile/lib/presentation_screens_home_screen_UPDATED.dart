import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:geolocator/geolocator.dart';
import '../../data/services/api_client.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  final _originController = TextEditingController();
  final _destController = TextEditingController();
  DateTime _selectedDate = DateTime.now();
  TimeOfDay _selectedTime = TimeOfDay.now();
  bool _isArrivalTime = false;
  bool _useCurrentLocation = false;
  Position? _currentPosition;
  bool _isLoading = false;

  @override
  void dispose() {
    _originController.dispose();
    _destController.dispose();
    super.dispose();
  }

  Future<void> _getCurrentLocation() async {
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Sijaintipalvelut eivät ole käytössä')),
          );
        }
        return;
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Sijaintilupa evätty')),
            );
          }
          return;
        }
      }

      final position = await Geolocator.getCurrentPosition();
      setState(() {
        _currentPosition = position;
        _useCurrentLocation = true;
        _originController.text = 'Nykyinen sijainti';
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Virhe sijainnin haussa: $e')),
        );
      }
    }
  }

  Future<void> _searchRoute() async {
    if (_destController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Anna määränpää')),
      );
      return;
    }

    if (!_useCurrentLocation && _originController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Anna lähtöpaikka tai käytä nykyistä sijaintia')),
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      final apiClient = ref.read(apiClientProvider);
      
      // Geocode origin
      double originLat, originLon;
      if (_useCurrentLocation && _currentPosition != null) {
        originLat = _currentPosition!.latitude;
        originLon = _currentPosition!.longitude;
      } else {
        final originGeocode = await apiClient.geocode(_originController.text);
        originLat = originGeocode['lat'];
        originLon = originGeocode['lon'];
      }

      // Geocode destination
      final destGeocode = await apiClient.geocode(_destController.text);
      final destLat = destGeocode['lat'];
      final destLon = destGeocode['lon'];

      // Search route
      final routeData = await apiClient.searchRoute(
        originLat: originLat,
        originLon: originLon,
        destLat: destLat,
        destLon: destLon,
      );

      if (mounted) {
        // Navigate to map with route data
        context.pushNamed(
          'map',
          extra: {
            'origin': _useCurrentLocation ? 'current' : _originController.text,
            'destination': _destController.text,
            'originLat': originLat,
            'originLon': originLon,
            'destLat': destLat,
            'destLon': destLon,
            'routeData': routeData,
            'date': _selectedDate,
            'time': _selectedTime,
            'isArrivalTime': _isArrivalTime,
          },
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Virhe reittihauss: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Reitti Pro'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () {
              // TODO: Navigate to settings
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header
            const Text(
              '🗺️ Reittihaku',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 24),

            // Origin
            TextField(
              controller: _originController,
              decoration: InputDecoration(
                labelText: 'Lähtöpaikka',
                hintText: 'Esim. Helsinki',
                prefixIcon: const Icon(Icons.location_on),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.my_location),
                  onPressed: _getCurrentLocation,
                ),
              ),
              enabled: !_useCurrentLocation,
            ),
            const SizedBox(height: 16),

            // Destination
            TextField(
              controller: _destController,
              decoration: const InputDecoration(
                labelText: 'Määränpää',
                hintText: 'Esim. Tampere',
                prefixIcon: Icon(Icons.flag),
              ),
            ),
            const SizedBox(height: 24),

            // Date & Time
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    icon: const Icon(Icons.calendar_today),
                    label: Text(
                      '${_selectedDate.day}.${_selectedDate.month}.${_selectedDate.year}',
                    ),
                    onPressed: () async {
                      final date = await showDatePicker(
                        context: context,
                        initialDate: _selectedDate,
                        firstDate: DateTime.now(),
                        lastDate: DateTime.now().add(const Duration(days: 365)),
                      );
                      if (date != null) {
                        setState(() => _selectedDate = date);
                      }
                    },
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: OutlinedButton.icon(
                    icon: const Icon(Icons.access_time),
                    label: Text(_selectedTime.format(context)),
                    onPressed: () async {
                      final time = await showTimePicker(
                        context: context,
                        initialTime: _selectedTime,
                      );
                      if (time != null) {
                        setState(() => _selectedTime = time);
                      }
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Arrival/Departure toggle
            SwitchListTile(
              title: const Text('Saapumisaika'),
              subtitle: Text(
                _isArrivalTime ? 'Perillä valittuna aikana' : 'Lähtö valittuna aikana',
              ),
              value: _isArrivalTime,
              onChanged: (value) => setState(() => _isArrivalTime = value),
            ),
            const SizedBox(height: 24),

            // Search button
            ElevatedButton.icon(
              icon: _isLoading 
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : const Icon(Icons.search),
              label: Text(_isLoading ? 'Haetaan...' : 'Hae reitti'),
              onPressed: _isLoading ? null : _searchRoute,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.all(16),
              ),
            ),
            const SizedBox(height: 32),

            // Quick info
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Ominaisuudet:',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 12),
                    _buildFeatureItem(Icons.map, 'Interaktiivinen kartta'),
                    _buildFeatureItem(Icons.camera_alt, 'Kelikamerat'),
                    _buildFeatureItem(Icons.thermostat, 'Tiesää'),
                    _buildFeatureItem(Icons.warning, 'Liikennetiedotteet'),
                    _buildFeatureItem(Icons.cloud, 'Sääennusteet'),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFeatureItem(IconData icon, String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(icon, size: 20, color: Theme.of(context).primaryColor),
          const SizedBox(width: 12),
          Text(text),
        ],
      ),
    );
  }
}
