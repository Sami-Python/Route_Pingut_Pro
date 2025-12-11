import 'package:dio/dio.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: dotenv.env['API_URL'] ?? 'http://localhost:8000',
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
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
  }) async {
    try {
      final response = await _dio.get(
        '/maps/route',
        queryParameters: {
          'origin_lat': originLat,
          'origin_lon': originLon,
          'dest_lat': destLat,
          'dest_lon': destLon,
          if (departureTime != null) 'departure_time': departureTime,
          if (arrivalTime != null) 'arrival_time': arrivalTime,
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
        queryParameters: {'query': query},
      );
      return response.data;
    } catch (e) {
      throw Exception('Failed to geocode: $e');
    }
  }

  // Weather cameras
  Future<List<dynamic>> getWeatherCameras({
    required double lat,
    required double lon,
    double radius = 50.0,
  }) async {
    try {
      final response = await _dio.get(
        '/maps/weather-cameras',
        queryParameters: {
          'lat': lat,
          'lon': lon,
          'radius': radius,
        },
      );
      return response.data;
    } catch (e) {
      throw Exception('Failed to get weather cameras: $e');
    }
  }

  // Road weather stations
  Future<List<dynamic>> getRoadWeather({
    required double lat,
    required double lon,
    double radius = 50.0,
  }) async {
    try {
      final response = await _dio.get(
        '/maps/road-weather',
        queryParameters: {
          'lat': lat,
          'lon': lon,
          'radius': radius,
        },
      );
      return response.data;
    } catch (e) {
      throw Exception('Failed to get road weather: $e');
    }
  }

  // Traffic messages
  Future<List<dynamic>> getTrafficMessages({
    required double lat,
    required double lon,
    double radius = 50.0,
  }) async {
    try {
      final response = await _dio.get(
        '/maps/traffic-messages',
        queryParameters: {
          'lat': lat,
          'lon': lon,
          'radius': radius,
        },
      );
      return response.data;
    } catch (e) {
      throw Exception('Failed to get traffic messages: $e');
    }
  }
}
