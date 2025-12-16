import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Load environment variables
  try {
    await dotenv.load(fileName: "assets/.env");
  } catch (e) {
    debugPrint('Warning: .env file not found. Using default values. Error: $e');
    // Ensure dotenv is initialized to avoid NotInitializedError when accessing .env
    dotenv.testLoad(fileInput: '');
  }
  
  runApp(
    const ProviderScope(
      child: ReittProApp(),
    ),
  );
}

class ReittProApp extends ConsumerWidget {
  const ReittProApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);

    return MaterialApp.router(
      title: '🐧 Pingut AI Route Planner',
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.system,
      routerConfig: router,
      debugShowCheckedModeBanner: false,
    );
  }
}
