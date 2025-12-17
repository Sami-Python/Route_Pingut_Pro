import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../data/services/storage_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _storageService = StorageService();
  final _homeAddressController = TextEditingController();
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final homeAddress = await _storageService.getHomeAddress();
    if (homeAddress != null) {
      _homeAddressController.text = homeAddress;
    }
    setState(() {
      _isLoading = false;
    });
  }

  Future<void> _saveSettings() async {
    setState(() => _isLoading = true);
    await _storageService.saveHomeAddress(_homeAddressController.text);
    if (!mounted) return;
    
    setState(() => _isLoading = false);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Asetukset tallennettu! ✅')),
    );
  }

  @override
  void dispose() {
    _homeAddressController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Asetukset ⚙️'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Osoitteet',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _homeAddressController,
                    decoration: const InputDecoration(
                      labelText: 'Kotiosoite 🏠',
                      hintText: 'Esim. Mannerheimintie 1, Helsinki',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.home),
                    ),
                  ),
                  const SizedBox(height: 24),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.icon(
                      onPressed: _saveSettings,
                      icon: const Icon(Icons.save),
                      label: const Text('Tallenna'),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}
