import 'package:dio/dio.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: dotenv.env['API_URL'] ?? 'http://192.168.1.130:8000',
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      headers: {
        'Content-Type': 'application/json',
      },
    ),
  );

  // Add logging interceptor
  dio.interceptors.add(
    LogInterceptor(
      requestBody: true,
      responseBody: true,
    ),
  );

  print('📱 [ApiClient] Configured Base URL: ${dio.options.baseUrl}');
  
  return dio;
});

final apiClientProvider = Provider<ApiClient>((ref) {
  final dio = ref.watch(dioProvider);
  return ApiClient(dio);
});

class ApiClient {
  final Dio _dio;

  ApiClient(this._dio);

  // Route search
  Future<Map<String, dynamic>> searchRoute({
    required double originLat,
    required double originLon,
    required double destLat,
    required double destLon,
    String? departureTime,
    String? arrivalTime,
    int alternatives = 2, // Request 2 alternatives (total 3 routes)
  }) async {
    try {
      final response = await _dio.post(
        '/maps/route',
        data: {
          'origin_lat': originLat,
          'origin_lon': originLon,
          'dest_lat': destLat,
          'dest_lon': destLon,
          'alternatives': alternatives,
          if (departureTime != null) 'departure_time': departureTime,
          // 'arrival_time': arrivalTime,
        },
      );
      return response.data;
    } catch (e) {
      throw Exception('Failed to search route: $e');
    }
  }

  // Geocoding
  Future<Map<String, dynamic>> geocode(String query) async {
    try {
      final response = await _dio.get(
        '/maps/geocode',
        queryParameters: {'address': query},
      );
      return response.data;
    } catch (e) {
      throw Exception('Failed to geocode: $e');
    }
  }

  // Weather cameras
  Future<List<dynamic>> getWeatherCameras({
    double? lat,
    double? lon,
    String? polyline,
    double radius = 50.0,
  }) async {
    try {
      final queryParams = <String, dynamic>{'radius': radius};
      if (polyline != null) {
        queryParams['polyline'] = polyline;
      } else if (lat != null && lon != null) {
        queryParams['lat'] = lat;
        queryParams['lon'] = lon;
      }

      final response = await _dio.get(
        '/maps/digitraffic/cameras',
        queryParameters: queryParams,
      );
      return response.data['cameras'];
    } catch (e) {
      throw Exception('Failed to get weather cameras: $e');
    }
  }

  // Road weather stations
  Future<List<dynamic>> getRoadWeather({
    double? lat,
    double? lon,
    String? polyline,
    double radius = 50.0,
  }) async {
    try {
      final queryParams = <String, dynamic>{'radius': radius};
      if (polyline != null) {
        queryParams['polyline'] = polyline;
      } else if (lat != null && lon != null) {
        queryParams['lat'] = lat;
        queryParams['lon'] = lon;
      }

      final response = await _dio.get(
        '/maps/digitraffic/road-weather',
        queryParameters: queryParams,
      );
      return response.data['stations'];
    } catch (e) {
      throw Exception('Failed to get road weather: $e');
    }
  }

  // Traffic messages
  Future<List<dynamic>> getTrafficMessages({
    double? lat,
    double? lon,
    String? polyline,
    double radius = 50.0,
  }) async {
    try {
      final queryParams = <String, dynamic>{'radius': radius};
      if (polyline != null) {
        queryParams['polyline'] = polyline;
      } else if (lat != null && lon != null) {
        queryParams['lat'] = lat;
        queryParams['lon'] = lon;
      }
      
      final response = await _dio.get(
        '/maps/digitraffic/messages',
        queryParameters: queryParams,
      );
      return response.data['messages'];
    } catch (e) {
      throw Exception('Failed to get traffic messages: $e');
    }
  }

  // LAM Stations (Traffic Volume)
  Future<List<dynamic>> getLAMStations({
    double? lat,
    double? lon,
    String? polyline,
    double radius = 50.0,
  }) async {
    try {
      final queryParams = <String, dynamic>{'radius': radius};
      if (polyline != null) {
        queryParams['polyline'] = polyline;
      } else if (lat != null && lon != null) {
        queryParams['lat'] = lat;
        queryParams['lon'] = lon;
      }
      
      final response = await _dio.get(
        '/maps/digitraffic/lam',
        queryParameters: queryParams,
      );
      return response.data['stations'];
    } catch (e) {
      throw Exception('Failed to get LAM stations: $e');
    }
  }

  // Traffic Tile URL Template
  String getTrafficTileUrlTemplate() {
    // Returns full URL template including base URL
    final baseUrl = _dio.options.baseUrl;
    // Ensure no double slash if baseUrl ends with /
    final cleanBase = baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl;
    return '$cleanBase/maps/tiles/here_traffic/{z}/{x}/{y}';
  }

  // AI Route Analysis
  Future<String> analyzeRoute(Map<String, dynamic> routeData) async {
    try {
      final response = await _dio.post(
        '/maps/analyze/route',
        data: routeData,
      );
      return response.data['analysis'] as String;
    } catch (e) {
      // Don't crash app on AI failure
      print('AI Analysis failed: $e');
      return "Analyysi epäonnistui. Tarkista internet-yhteys tai palvelimen tila.";
    }
  }

  // Route Weather (Start & End)
  Future<Map<String, dynamic>> getRouteWeather({
    required double fromLat,
    required double fromLon,
    required double toLat,
    required double toLon,
    String? departureTime,
  }) async {
    try {
      print('📡 [ApiClient] Requesting weather for route...');
      final response = await _dio.get(
        '/weather/route-coords',
        queryParameters: {
          'from_lat': fromLat,
          'from_lon': fromLon,
          'to_lat': toLat,
          'to_lon': toLon,
          if (departureTime != null) 'start_time': departureTime,
        },
      );
      print('📡 [ApiClient] Response status: ${response.statusCode}');
      return response.data;
    } catch (e) {
      print('❌ [ApiClient] Weather fetch failed: $e');
      return {}; // Return empty map on failure to not block UI
    }
  }

  // Rain Radar Config
  Future<Map<String, dynamic>> getRadarConfig() async {
    try {
      final response = await _dio.get('/weather/radar/config');
      return response.data;
    } catch (e) {
      print('Failed to get radar config: $e');
      return {};
    }
  }

  // Batch Route Weather (Intervals)
  Future<List<dynamic>> getBatchWeather(List<Map<String, dynamic>> points) async {
    try {
      final response = await _dio.post(
        '/weather/batch',
        data: points,
      );
      return response.data;
    } catch (e) {
      print('Failed to get batch weather: $e');
      return [];
    }
  }
}
