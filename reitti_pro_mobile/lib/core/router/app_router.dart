import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../presentation/screens/home_screen.dart';
import '../../presentation/screens/map_screen.dart';
import '../../presentation/screens/route_details_screen.dart';
import '../../presentation/screens/settings_screen.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/',
    routes: [
      GoRoute(
        path: '/',
        name: 'home',
        builder: (context, state) => const HomeScreen(),
      ),
      GoRoute(
        path: '/settings',
        name: 'settings',
        builder: (context, state) => const SettingsScreen(),
      ),
      GoRoute(
        path: '/map',
        name: 'map',
        builder: (context, state) {
          final routeData = state.extra as Map<String, dynamic>?;
          return MapScreen(routeData: routeData);
        },
      ),
      GoRoute(
        path: '/route-details',
        name: 'route-details',
        builder: (context, state) {
          final routeData = state.extra as Map<String, dynamic>;
          return RouteDetailsScreen(routeData: routeData);
        },
      ),
    ],
  );
});
