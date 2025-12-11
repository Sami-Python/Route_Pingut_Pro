import 'package:flutter/material.dart';

class RouteDetailsScreen extends StatelessWidget {
  final Map<String, dynamic> routeData;

  const RouteDetailsScreen({super.key, required this.routeData});

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
                      '${routeData['distance'] ?? 'N/A'} km',
                    ),
                    _buildInfoRow(
                      Icons.access_time,
                      'Ajoaika',
                      '${routeData['duration'] ?? 'N/A'} min',
                    ),
                    _buildInfoRow(
                      Icons.schedule,
                      'Lähtö',
                      routeData['departure'] ?? 'N/A',
                    ),
                    _buildInfoRow(
                      Icons.flag,
                      'Perillä',
                      routeData['arrival'] ?? 'N/A',
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
                    const Text('Ladataan säätietoja...'),
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
