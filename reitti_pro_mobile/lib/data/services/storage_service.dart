import 'package:shared_preferences/shared_preferences.dart';

class StorageService {
  static const String keyHomeAddress = 'home_address';

  Future<void> saveHomeAddress(String address) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(keyHomeAddress, address);
  }

  Future<String?> getHomeAddress() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(keyHomeAddress);
  }
}
