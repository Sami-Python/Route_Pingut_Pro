import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class FavoritePlace {
  final String name;
  final double lat;
  final double lon;

  FavoritePlace({
    required this.name,
    required this.lat,
    required this.lon,
  });

  Map<String, dynamic> toJson() => {
        'name': name,
        'lat': lat,
        'lon': lon,
      };

  factory FavoritePlace.fromJson(Map<String, dynamic> json) => FavoritePlace(
        name: json['name'] as String,
        lat: (json['lat'] as num).toDouble(),
        lon: (json['lon'] as num).toDouble(),
      );
}

class FavoritesService {
  static const String _key = 'favorite_places';

  Future<List<FavoritePlace>> getFavorites() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final String? jsonString = prefs.getString(_key);
      
      if (jsonString == null) return [];
      
      final List<dynamic> jsonList = json.decode(jsonString);
      return jsonList.map((json) => FavoritePlace.fromJson(json)).toList();
    } catch (e) {
      print('Error loading favorites: $e');
      return [];
    }
  }

  Future<bool> saveFavorite(String name, double lat, double lon) async {
    try {
      final favorites = await getFavorites();
      
      // Check if already exists
      if (favorites.any((f) => f.name.toLowerCase() == name.toLowerCase())) {
        return false; // Already exists
      }
      
      favorites.add(FavoritePlace(name: name, lat: lat, lon: lon));
      
      final prefs = await SharedPreferences.getInstance();
      final jsonString = json.encode(favorites.map((f) => f.toJson()).toList());
      return await prefs.setString(_key, jsonString);
    } catch (e) {
      print('Error saving favorite: $e');
      return false;
    }
  }

  Future<bool> deleteFavorite(String name) async {
    try {
      final favorites = await getFavorites();
      favorites.removeWhere((f) => f.name == name);
      
      final prefs = await SharedPreferences.getInstance();
      final jsonString = json.encode(favorites.map((f) => f.toJson()).toList());
      return await prefs.setString(_key, jsonString);
    } catch (e) {
      print('Error deleting favorite: $e');
      return false;
    }
  }

  Future<bool> hasFavorite(String name) async {
    final favorites = await getFavorites();
    return favorites.any((f) => f.name.toLowerCase() == name.toLowerCase());
  }

  Future<FavoritePlace?> getFavoriteByName(String name) async {
    final favorites = await getFavorites();
    try {
      return favorites.firstWhere((f) => f.name.toLowerCase() == name.toLowerCase());
    } catch (e) {
      return null;
    }
  }
}
