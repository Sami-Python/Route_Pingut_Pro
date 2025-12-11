# Reitti Pro Mobile - Flutter Setup Guide

## 1. Asenna Flutter

### Windows

1. **Lataa Flutter SDK:**
   - Mene: https://docs.flutter.dev/get-started/install/windows
   - Lataa Flutter SDK (zip)

2. **Pura ja asenna:**
   ```powershell
   # Pura zip esim. C:\src\flutter
   # Lisää PATH-muuttujaan: C:\src\flutter\bin
   ```

3. **Asenna riippuvuudet:**
   ```powershell
   # Android Studio (suositeltu)
   # Visual Studio Code + Flutter extension
   # Git for Windows
   ```

4. **Tarkista asennus:**
   ```bash
   flutter doctor
   ```

## 2. Luo projekti

Kun Flutter on asennettu, aja:

```bash
cd c:\Users\samih\code\pingut-projekti-4
flutter create reitti_pro_mobile
cd reitti_pro_mobile
```

## 3. Korvaa tiedostot

Kopioi tämän kansion tiedostot Flutter-projektin päälle:
- `pubspec.yaml` → projektin juureen
- `lib/` -kansio → projektin juureen

## 4. Asenna riippuvuudet

```bash
flutter pub get
```

## 5. Käynnistä sovellus

**Android-emulaattorilla:**
```bash
flutter run
```

**Omalla laitteella (Android):**
1. Kytke puhelin USB:llä
2. Ota kehittäjätila käyttöön
3. Salli USB-debugging
4. `flutter run`

**iOS (Mac vaaditaan):**
```bash
flutter run
```

## 6. Rakenna APK (Android)

```bash
flutter build apk --release
# APK: build/app/outputs/flutter-apk/app-release.apk
```

## Seuraavat vaiheet

Kun projekti on luotu ja käynnissä:
1. Testaa että sovellus käynnistyy
2. Tarkista että backend-yhteys toimii
3. Kokeile reittihakua
4. Raportoi mahdolliset ongelmat

## Tuki

Jos kohtaat ongelmia:
- `flutter doctor` - Tarkista asennus
- `flutter clean` - Puhdista projekti
- `flutter pub get` - Päivitä riippuvuudet
