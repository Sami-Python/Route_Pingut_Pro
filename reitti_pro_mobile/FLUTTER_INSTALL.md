# Flutter Asennus - Yksinkertainen Ohje

## Vaihtoehto 1: Automaattinen asennus (SUOSITELTU)

1. **Avaa PowerShell ADMIN-oikeuksilla:**
   - Paina `Win + X`
   - Valitse "Windows PowerShell (Admin)" tai "Terminal (Admin)"

2. **Aja asennusskripti:**
   ```powershell
   cd c:\Users\samih\code\pingut-projekti-4\reitti_pro_mobile
   .\install_flutter.ps1
   ```

3. **Jos saat virheen "execution policy":**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   .\install_flutter.ps1
   ```

4. **Käynnistä terminaali uudelleen** ja testaa:
   ```bash
   flutter doctor
   ```

---

## Vaihtoehto 2: Manuaalinen asennus

### 1. Lataa Flutter

Mene: https://docs.flutter.dev/get-started/install/windows

Lataa "flutter_windows_X.X.X-stable.zip"

### 2. Pura tiedosto

Pura zip-tiedosto esim. `C:\src\flutter`

### 3. Lisää PATH:iin (TÄMÄ ON SE VAIKEA OSA!)

**Mitä "PATH:iin lisääminen" tarkoittaa:**
- PATH on lista kansioista, joista Windows etsii ohjelmia
- Lisäämällä Flutterin PATH:iin, voit käyttää `flutter`-komentoa mistä tahansa

**Miten lisätään:**

1. **Avaa Windowsin asetukset:**
   - Paina `Win + R`
   - Kirjoita: `sysdm.cpl`
   - Paina Enter

2. **Mene "Advanced" välilehdelle**

3. **Klikkaa "Environment Variables" (Ympäristömuuttujat)**

4. **"User variables" osiossa:**
   - Etsi "Path"
   - Klikkaa "Edit"

5. **Lisää uusi rivi:**
   - Klikkaa "New"
   - Kirjoita: `C:\src\flutter\bin`
   - Klikkaa OK kaikissa ikkunoissa

6. **Käynnistä terminaali uudelleen**

### 4. Tarkista asennus

```bash
flutter doctor
```

---

## Mitä seuraavaksi?

Kun `flutter doctor` toimii:

```bash
cd c:\Users\samih\code\pingut-projekti-4\reitti_pro_mobile
flutter pub get
flutter run
```

## Ongelmia?

### "flutter: command not found"
- Käynnistä terminaali uudelleen
- Tarkista että `C:\src\flutter\bin` on PATH:issa

### "Android SDK not found"
- Asenna Android Studio: https://developer.android.com/studio
- Aja: `flutter doctor --android-licenses`

### "Visual Studio not found" (iOS)
- Tämä on OK, iOS-kehitys vaatii Macin
- Android toimii ilman tätä

---

## Nopea tarkistus

Aja PowerShellissä:
```powershell
$env:Path -split ';' | Select-String flutter
```

Jos näet `C:\src\flutter\bin`, PATH on OK! ✅
