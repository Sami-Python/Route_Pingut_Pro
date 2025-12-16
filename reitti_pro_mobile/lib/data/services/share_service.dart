import 'package:share_plus/share_plus.dart';
import 'package:intl/intl.dart';

class ShareService {
  /// Share route information as formatted text
  static Future<void> shareRoute({
    required String origin,
    required String destination,
    required double distanceKm,
    required double durationHours,
    required DateTime departureTime,
  }) async {
    final dateFormat = DateFormat('dd.MM.yyyy');
    final timeFormat = DateFormat('HH:mm');
    
    final hours = durationHours.floor();
    final minutes = ((durationHours - hours) * 60).round();
    final durationText = hours > 0 ? '${hours}h ${minutes}min' : '${minutes}min';
    
    final arrivalTime = departureTime.add(Duration(seconds: (durationHours * 3600).round()));
    
    final message = '''
🐧 Pingut AI Route Planner

📍 Lähtö: $origin
🏁 Määränpää: $destination
📏 Matka: ${distanceKm.toStringAsFixed(1)} km
⏱️ Kesto: $durationText
🕐 Lähtö: ${dateFormat.format(departureTime)} klo ${timeFormat.format(departureTime)}
🏁 Perillä: ${dateFormat.format(arrivalTime)} klo ${timeFormat.format(arrivalTime)}

Suunnittele reittisi: https://pingut.app
''';

    try {
      await Share.share(
        message.trim(),
        subject: 'Reitti: $origin → $destination',
      );
    } catch (e) {
      print('Error sharing route: $e');
      rethrow;
    }
  }
}
