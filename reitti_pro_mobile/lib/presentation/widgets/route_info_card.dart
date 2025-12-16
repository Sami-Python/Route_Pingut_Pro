
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

class RouteInfoCard extends StatefulWidget {
  final double distanceKm;
  final double durationHours;
  final DateTime departureTime;
  final VoidCallback onAnalyzePressed;
  final VoidCallback onSharePressed;

  const RouteInfoCard({
    super.key,
    required this.distanceKm,
    required this.durationHours,
    required this.departureTime,
    required this.onAnalyzePressed,
    required this.onSharePressed,
  });

  @override
  State<RouteInfoCard> createState() => _RouteInfoCardState();
}

class _RouteInfoCardState extends State<RouteInfoCard> {
  bool _isExpanded = false;

  @override
  Widget build(BuildContext context) {
    final arrivalTime = widget.departureTime.add(Duration(seconds: (widget.durationHours * 3600).round()));
    final timeFormat = DateFormat('HH:mm');

    return Card(
      elevation: 8,
      margin: const EdgeInsets.all(16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        onTap: () => setState(() => _isExpanded = !_isExpanded),
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [

              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _buildInfoColumn(
                    context, 
                    'Lähtö', 
                    timeFormat.format(widget.departureTime),
                    Icons.departure_board
                  ),
                  _buildInfoColumn(
                    context, 
                    'Perillä', 
                    timeFormat.format(arrivalTime),
                    Icons.flag
                  ),
                   _buildInfoColumn(
                    context, 
                    'Kesto', 
                    _formatDuration(widget.durationHours),
                    Icons.timer
                  ),
                   _buildInfoColumn(
                    context, 
                    'Matka', 
                    '${widget.distanceKm.toStringAsFixed(1)} km',
                    Icons.route
                  ),
                ],
              ),
              if (_isExpanded) ...[
                const Divider(height: 24),
                FilledButton.icon(
                  onPressed: widget.onAnalyzePressed,
                  icon: const Icon(Icons.auto_awesome, color: Colors.yellowAccent),
                  label: const Text("AI Analysoi Matka"),
                  style: FilledButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    backgroundColor: Theme.of(context).colorScheme.primary,
                    foregroundColor: Theme.of(context).colorScheme.onPrimary,
                  ),
                ),
                const SizedBox(height: 8),
                OutlinedButton.icon(
                  onPressed: widget.onSharePressed,
                  icon: const Icon(Icons.share),
                  label: const Text("📤 Jaa reitti"),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoColumn(BuildContext context, String label, String value, IconData icon) {
    return Column(
      children: [
        Icon(icon, size: 20, color: Theme.of(context).colorScheme.secondary),
        const SizedBox(height: 4),
        Text(
          value,
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
        ),
        Text(
          label,
          style: TextStyle(fontSize: 12, color: Colors.grey[600]),
        ),
      ],
    );
  }

  String _formatDuration(double hours) {
    final int h = hours.floor();
    final int m = ((hours - h) * 60).round();
    if (h > 0) {
      return '${h}h ${m}min';
    }
    return '${m}min';
  }
}
