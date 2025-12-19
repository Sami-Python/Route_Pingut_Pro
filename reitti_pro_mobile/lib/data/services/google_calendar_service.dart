import 'package:google_sign_in/google_sign_in.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'api_client.dart';

final googleCalendarServiceProvider = Provider<GoogleCalendarService>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return GoogleCalendarService(apiClient);
});

class CalendarEvent {
  final String title;
  final String start;
  final String end;
  final String location;

  CalendarEvent({
    required this.title,
    required this.start,
    required this.end,
    required this.location,
  });

  factory CalendarEvent.fromJson(Map<String, dynamic> json) {
    return CalendarEvent(
      title: json['title'] ?? 'No Title',
      start: json['start'] ?? '',
      end: json['end'] ?? '',
      location: json['location'] ?? '',
    );
  }
}

class GoogleCalendarService {
  // Scopes required for the API
  static const List<String> _scopes = <String>[
    'email',
    'https://www.googleapis.com/auth/calendar.readonly',
  ];

  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: _scopes,
  );

  final ApiClient _apiClient;

  GoogleCalendarService(this._apiClient);

  GoogleSignInAccount? get currentUser => _googleSignIn.currentUser;

  Future<GoogleSignInAccount?> signIn() async {
    try {
      return await _googleSignIn.signIn();
    } catch (error) {
      print('Sign in failed: $error');
      return null;
    }
  }

  Future<void> signOut() => _googleSignIn.disconnect();

  Future<List<CalendarEvent>> getEvents() async {
    final user = _googleSignIn.currentUser;
    if (user == null) {
      throw Exception('User not signed in');
    }

    // Get the authentication object (accessToken)
    final auth = await user.authentication;
    final token = auth.accessToken;

    if (token == null) {
      throw Exception('Failed to get access token');
    }

    // Send token to backend to get events
    final eventsData = await _apiClient.fetchGoogleEvents(token);
    
    return (eventsData as List)
        .map((e) => CalendarEvent.fromJson(e))
        .toList();
  }
}
