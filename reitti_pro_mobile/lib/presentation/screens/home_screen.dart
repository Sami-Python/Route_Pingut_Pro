import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:geolocator/geolocator.dart';
import '../../data/services/api_client.dart';
import '../../data/services/favorites_service.dart';
import '../widgets/mini_map_widget.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  final _originController = TextEditingController();
  final _destController = TextEditingController();
  final _favoritesService = FavoritesService();
  DateTime _selectedDate = DateTime.now();
  TimeOfDay _selectedTime = TimeOfDay.now();
  bool _isArrivalTime = false;
  bool _useCurrentLocation = false;
  Position? _currentPosition;
  bool _isLoading = false;
  List<FavoritePlace> _favorites = [];

  @override
  void initState() {
    super.initState();
    _loadFavorites();
  }

  Future<void> _loadFavorites() async {
    final favorites = await _favoritesService.getFavorites();
    setState(() => _favorites = favorites);
  }

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

  Future<Map<String, dynamic>?> _geocode(String address) async {
    try {
      final client = ref.read(apiClientProvider);
      final response = await client.geocode(address);
      if (response['success'] == true) {
        return response;
      }
    } catch (e) {
      print('Geocode error: $e');
      throw Exception("Yhteysvirhe: $e");
    }
    return null;
  }

  Future<void> _searchRoute() async {
    if (_destController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Anna määränpää')),
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      final client = ref.read(apiClientProvider);
      double? originLat, originLon;
      
      // 1. Resolve Origin
      if (_useCurrentLocation && _currentPosition != null) {
        originLat = _currentPosition!.latitude;
        originLon = _currentPosition!.longitude;
      } else {
        if (_originController.text.isEmpty) {
          throw Exception("Lähtöpaikka puuttuu");
        }
        final originGeo = await _geocode(_originController.text);
        if (originGeo == null) throw Exception("Lähtöpaikkaa ei löytynyt");
        originLat = originGeo['latitude'];
        originLon = originGeo['longitude'];
      }

      // 2. Resolve Destination
      final destGeo = await _geocode(_destController.text);
      if (destGeo == null) throw Exception("Määränpäätä ei löytynyt");
      final destLat = destGeo['latitude'];
      final destLon = destGeo['longitude'];

      // 3. Fetch Route
      // Format time ISO8601 if needed, or null
      String? depTime;
      if (!_isArrivalTime) {
         final dt = DateTime(
           _selectedDate.year, 
           _selectedDate.month, 
           _selectedDate.day, 
           _selectedTime.hour, 
           _selectedTime.minute
         );
         depTime = dt.toIso8601String();
      }

      final routeData = await client.searchRoute(
        originLat: originLat!, 
        originLon: originLon!, 
        destLat: destLat, 
        destLon: destLon,
        departureTime: depTime
      );

      // Inject names for ShareService
      routeData['origin'] = _useCurrentLocation && _currentPosition != null 
          ? "Oma sijainti" 
          : _originController.text;
      routeData['destination'] = _destController.text;

      if (mounted) {
        context.pushNamed(
          'map',
          extra: routeData, // Pass the API response directly
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Virhe: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _saveFavorite() async {
    if (_destController.text.isEmpty) return;

    final nameController = TextEditingController(text: _destController.text);
    
    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('💾 Tallenna suosikiksi'),
        content: TextField(
          controller: nameController,
          decoration: const InputDecoration(
            labelText: 'Nimi',
            hintText: 'Esim. Koti, Työ, Mökki',
          ),
          autofocus: true,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Peruuta'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Tallenna'),
          ),
        ],
      ),
    );

    if (result == true && mounted) {
      // Get coordinates for destination
      final destGeo = await _geocode(_destController.text);
      if (destGeo == null) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Paikkaa ei löytynyt')),
          );
        }
        return;
      }

      final success = await _favoritesService.saveFavorite(
        nameController.text,
        destGeo['latitude'],
        destGeo['longitude'],
      );

      if (mounted) {
        if (success) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('✅ ${nameController.text} tallennettu')),
          );
          _loadFavorites();
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Suosikki on jo olemassa')),
          );
        }
      }
    }
  }

  void _showFavoritesDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('⭐ Suosikit'),
        content: _favorites.isEmpty
            ? const Text('Ei tallennettuja suosikkeja')
            : SizedBox(
                width: double.maxFinite,
                child: ListView.builder(
                  shrinkWrap: true,
                  itemCount: _favorites.length,
                  itemBuilder: (context, index) {
                    final fav = _favorites[index];
                    return ListTile(
                      leading: const Icon(Icons.place),
                      title: Text(fav.name),
                      subtitle: Text('${fav.lat.toStringAsFixed(4)}, ${fav.lon.toStringAsFixed(4)}'),
                      trailing: IconButton(
                        icon: const Icon(Icons.delete, color: Colors.red),
                        onPressed: () async {
                          await _favoritesService.deleteFavorite(fav.name);
                          _loadFavorites();
                          Navigator.pop(context);
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('🗑️ ${fav.name} poistettu')),
                            );
                          }
                        },
                      ),
                    );
                  },
                ),
              ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Sulje'),
          ),
        ],
      ),
    );
  }

  void _showFavoritePicker({required bool isOrigin}) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(isOrigin ? '⭐ Valitse lähtöpaikka' : '⭐ Valitse määränpää'),
        content: SizedBox(
          width: double.maxFinite,
          child: ListView.builder(
            shrinkWrap: true,
            itemCount: _favorites.length,
            itemBuilder: (context, index) {
              final fav = _favorites[index];
              return ListTile(
                leading: const Icon(Icons.place, color: Colors.amber),
                title: Text(fav.name),
                subtitle: Text('${fav.lat.toStringAsFixed(4)}, ${fav.lon.toStringAsFixed(4)}'),
                onTap: () {
                  setState(() {
                    if (isOrigin) {
                      _originController.text = fav.name;
                      _useCurrentLocation = false;
                    } else {
                      _destController.text = fav.name;
                    }
                  });
                  Navigator.pop(context);
                },
              );
            },
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Peruuta'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🐧 Pingut AI Route Planner'),
        actions: [
          IconButton(
            icon: const Icon(Icons.star),
            onPressed: _showFavoritesDialog,
            tooltip: 'Suosikit',
          ),
          IconButton(
            icon: const Icon(Icons.save),
            onPressed: _saveFavorite,
            tooltip: 'Tallenna suosikiksi',
          ),
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
            const MiniMapWidget(),
            const SizedBox(height: 24),

            // Origin
            TextField(
              controller: _originController,
              decoration: InputDecoration(
                labelText: 'Lähtöpaikka',
                hintText: 'Esim. Helsinki',
                prefixIcon: const Icon(Icons.location_on),
                suffixIcon: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (_favorites.isNotEmpty)
                      IconButton(
                        icon: const Icon(Icons.star, color: Colors.amber),
                        tooltip: 'Valitse suosikki',
                        onPressed: () => _showFavoritePicker(isOrigin: true),
                      ),
                    IconButton(
                      icon: const Icon(Icons.my_location),
                      tooltip: 'Nykyinen sijainti',
                      onPressed: _getCurrentLocation,
                    ),
                  ],
                ),
              ),
              enabled: !_useCurrentLocation,
            ),
            const SizedBox(height: 16),

            // Destination
            TextField(
              controller: _destController,
              decoration: InputDecoration(
                labelText: 'Määränpää',
                hintText: 'Esim. Tampere',
                prefixIcon: const Icon(Icons.flag),
                suffixIcon: _favorites.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.star, color: Colors.amber),
                        tooltip: 'Valitse suosikki',
                        onPressed: () => _showFavoritePicker(isOrigin: false),
                      )
                    : null,
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
                    _buildFeatureItem(Icons.auto_awesome, 'AI reittinalyysi'),
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
