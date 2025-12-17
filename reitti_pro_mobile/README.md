# Flutter Reitti Pro Mobile - Asennusohje

## 📋 Tiedostorakenne

Kaikki lähdetiedostot on luotu kansioon `flutter_source_files/`. Ne täytyy kopioida oikeisiin paikkoihin Flutter-projektin luomisen jälkeen.

### Tiedostojen sijoitus:

```
flutter_source_files/
├── main.dart                                    → lib/main.dart
├── core_theme_app_theme.dart                    → lib/core/theme/app_theme.dart
├── core_router_app_router.dart                  → lib/core/router/app_router.dart
├── data_services_api_client.dart                → lib/data/services/api_client.dart
├── presentation_screens_home_screen.dart        → lib/presentation/screens/home_screen.dart
├── presentation_screens_map_screen.dart         → lib/presentation/screens/map_screen.dart
└── presentation_screens_route_details_screen.dart → lib/presentation/screens/route_details_screen.dart
```

## 🚀 Asennusvaiheet

### 1. Asenna Flutter

**Windows:**
1. Lataa Flutter SDK: https://docs.flutter.dev/get-started/install/windows
2. Pura zip-tiedosto (esim. `C:\src\flutter`)
3. Lisää PATH: `C:\src\flutter\bin`
4. Asenna Android Studio tai VS Code + Flutter extension
5. Tarkista: `flutter doctor`

### 2. Luo Flutter-projekti

```bash
cd c:\Users\samih\code\pingut-projekti-4
flutter create reitti_pro_mobile
cd reitti_pro_mobile
```

### 3. Korvaa pubspec.yaml

```bash
# Kopioi flutter_source_files/../pubspec.yaml projektin juureen
copy ..\pubspec.yaml pubspec.yaml
```

### 4. Luo kansiorakenne

```bash
mkdir lib\core\theme
mkdir lib\core\router
mkdir lib\data\services
mkdir lib\presentation\screens
mkdir lib\presentation\widgets
```

### 5. Kopioi lähdetiedostot

**PowerShell:**
```powershell
# Main
copy flutter_source_files\main.dart lib\main.dart

# Core
copy flutter_source_files\core_theme_app_theme.dart lib\core\theme\app_theme.dart
copy flutter_source_files\core_router_app_router.dart lib\core\router\app_router.dart

# Data
copy flutter_source_files\data_services_api_client.dart lib\data\services\api_client.dart

# Screens
copy flutter_source_files\presentation_screens_home_screen.dart lib\presentation\screens\home_screen.dart
copy flutter_source_files\presentation_screens_map_screen.dart lib\presentation\screens\map_screen.dart
copy flutter_source_files\presentation_screens_route_details_screen.dart lib\presentation\screens\route_details_screen.dart
```

### 6. Luo .env tiedosto

Luo projektin juureen `.env` tiedosto:

```
API_URL=http://10.0.2.2:8000
HERE_API_KEY=<kopioi_olemassa_olevasta_.env>
MAPBOX_TOKEN=<kopioi_olemassa_olevasta_.env>
GEMINI_API_KEY=<kopioi_olemassa_olevasta_.env>
```

**Huom:** `10.0.2.2` on Android-emulaattorin localhost-osoite

### 7. Asenna riippuvuudet

```bash
flutter pub get
```

### 8. Käynnistä sovellus

**Android-emulaattorilla:**
```bash
flutter run
```

**Omalla laitteella:**
1. Kytke puhelin USB:llä
2. Ota kehittäjätila käyttöön (Asetukset → Tietoja puhelimesta → Napauta "Build number" 7 kertaa)
3. Salli USB-debugging
4. `flutter run`

## 🔧 Vianmääritys

### "flutter: command not found"
- Tarkista että Flutter on PATH:ssa
- Käynnistä terminaali uudelleen

### "No devices found"
- Android: Käynnistä emulaattori Android Studiossa
- iOS: Avaa Simulator (Mac)
- Fyysinen laite: Tarkista USB-yhteys ja debugging-oikeudet

### Riippuvuusvirheet
```bash
flutter clean
flutter pub get
```

### Backend-yhteysongelmat
- Tarkista että backend on käynnissä (`http://localhost:8000`)
- Android-emulaattorilla käytä `10.0.2.2:8000`
- iOS-simulaattorilla käytä `localhost:8000`

## 📱 Rakenna APK (Android)

```bash
flutter build apk --release
```

APK löytyy: `build/app/outputs/flutter-apk/app-release.apk`

Siirrä se puhelimeen ja asenna!

## 🎯 Seuraavat vaiheet

1. ✅ Asenna Flutter
2. ✅ Luo projekti
3. ✅ Kopioi tiedostot
4. ✅ Testaa sovellus
5. ✅ Lisää HERE API -integraatio
6. ✅ Lisää karttaominaisuudet
7. ✅ Lisää Digitraffic-data
8. ✅ Testaa oikealla laitteella

## 💡 Vinkit

- Käytä `flutter run --hot-reload` kehityksessä
- `r` = hot reload, `R` = hot restart
- `q` = quit
- Android Studio / VS Code tarjoavat paremman kehityskokemuksen

## 🆘 Tuki

Jos kohtaat ongelmia, tarkista:
1. `flutter doctor` - Näyttää puuttuvat riippuvuudet
2. `flutter clean` - Puhdistaa buildin
3. `flutter pub get` - Päivittää riippuvuudet
4. Backend-logit - Tarkista että API vastaa

Onnea matkaan! 🚀
