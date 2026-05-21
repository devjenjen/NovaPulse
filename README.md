# 🌌 NovaPulse – SteelSeries GG Battery Monitor

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Release](https://img.shields.io/badge/Version-v0.1.0-blueviolet)](https://github.com/devjenjen/NovaPulse/releases)

🌍 **[English](#english)** | 🇩🇪 **[Deutsch](#deutsch)** | 📝 **[Changelog](CHANGELOG.md)**

---

<a id="english"></a>
## 🇬🇧 English

### ❓ What is NovaPulse?

If you own a **SteelSeries Nova Pro Wireless** headset, you know the problem: the official "SteelSeries GG" software often warns you too late or too quietly when your battery is running low. This leads to sudden disconnects in the middle of a game or a meeting.

**NovaPulse** solves this problem. It runs lightweight in the background and provides:

*   **🚨 Smart Warnings:** Get a timely Windows notification at 25% (Warning) and 12% (Critical).
*   **🔋 Charger Monitor for Spare Battery:** NovaPulse notifies you as soon as the battery in your base station is fully charged!
*   **📟 OLED Warning:** When things get critical, a **"!!! SWAP AKKU !!!"** message flashes directly on the display of your base station.
*   **📊 Live Status:** Use the shortcut `Ctrl + Shift + B` at any time to open a small info window with the current battery level.

> [!TIP]
> NovaPulse only communicates locally with your SteelSeries Engine (on your own PC). **No data** is sent to the internet.

### 🚀 Quick Start (For Beginners)

Installation takes just a minute. You don't need any coding skills!

1.  **Download:** Go to the **[Releases Page](https://github.com/devjenjen/NovaPulse/releases/latest)**.
2.  **Choose Setup:** Click on the file `NovaPulse-Setup-0.1.0.exe` to download it.
3.  **Install:** Run the downloaded file with a double-click. Follow the instructions.
4.  **Start:** After installation, you will find "NovaPulse" in your Start Menu or in the Windows system tray at the bottom right (as a small icon).

*Note: Please make sure that the "SteelSeries GG Engine" software is running in the background.*

### ⚙️ Settings & Features

Right-click the NovaPulse icon in the system tray (bottom right near the clock) and select **"Settings"**.

Here you can:
*   **Enable Autostart:** Let NovaPulse start automatically with Windows.
*   **Set Custom Sounds:** Play your own `.wav` files when the battery is low.
*   **Test Notifications:** Click on "Test Notification" to see what a warning looks like.
*   **View Exact API Steps:** A chart shows exactly how the SteelSeries API reports battery levels.

### 🐍 For Developers (Run from Source)

If you want to run the code yourself or modify it:

1. **Requirements:** Python 3.10+ and the SteelSeries GG Engine.
2. **Install Dependencies:**
   ```bash
   pip install requests windows-toasts pystray pillow customtkinter
   ```
3. **Run:**
   ```bash
   git clone https://github.com/devjenjen/NovaPulse.git
   cd NovaPulse
   python novapulse.pyw
   ```

### 🔒 Security & Technical Details

NovaPulse communicates locally with the SteelSeries GG Engine via `127.0.0.1` (Localhost). 

*   **Certificate Warnings:** The source code uses `urllib3.disable_warnings()`. This is necessary because the GG Engine uses a self-signed certificate for its local API.
*   **No Security Risk:** Since all communication happens exclusively within your own machine, there is no risk of Man-in-the-Middle attacks from the internet. No data is sent to external servers.

### 🤝 Contributing & Feedback

Do you like NovaPulse? I welcome feedback, bug reports, or pull requests (code improvements)!

### 📜 License

Released under the **MIT License**. See the `LICENSE` file for details.

*Developed with ❤️ for the SteelSeries community.*

---

<a id="deutsch"></a>
## 🇩🇪 Deutsch

### ❓ Was ist NovaPulse?

Wenn du ein **SteelSeries Nova Pro Wireless** Headset hast, kennst du das Problem: Die offizielle "SteelSeries GG" Software warnt dich oft zu spät oder unauffällig, wenn dein Akku leer wird. Das führt zu plötzlichen Abbrüchen mitten im Spiel oder Meeting.

**NovaPulse** löst dieses Problem. Es läuft leichtgewichtig im Hintergrund und bietet dir:

*   **🚨 Smarte Warnungen:** Bekomme rechtzeitig eine Windows-Benachrichtigung bei 25% (Warnung) und 12% (Kritisch).
*   **🔋 Lade-Monitor für den Ersatzakku:** NovaPulse sagt dir Bescheid, sobald der Akku in deiner Basisstation wieder voll ist!
*   **📟 OLED-Warnung:** Wenn es kritisch wird, blinkt eine **"!!! SWAP AKKU !!!"**-Meldung direkt auf dem Display deiner Basisstation.
*   **📊 Live-Status:** Mit der Tastenkombination `Strg + Umschalt + B` öffnest du jederzeit ein kleines Info-Fenster mit dem aktuellen Batteriestand.

> [!TIP]
> NovaPulse kommuniziert nur lokal mit deiner SteelSeries Engine (auf deinem eigenen PC). Es werden **keine Daten** ins Internet gesendet.

### 🚀 Installation für Einsteiger (Quick Start)

Die Installation dauert nur eine Minute. Du musst nicht programmieren können!

1.  **Herunterladen:** Gehe auf die **[Releases-Seite](https://github.com/devjenjen/NovaPulse/releases/latest)**.
2.  **Setup wählen:** Klicke dort auf die Datei `NovaPulse-Setup-0.1.0.exe`, um sie herunterzuladen.
3.  **Installieren:** Führe die heruntergeladene Datei mit einem Doppelklick aus. Folge den Anweisungen.
4.  **Starten:** Nach der Installation findest du "NovaPulse" in deinem Startmenü oder unten rechts in der Windows-Taskleiste (als kleines Symbol).

*Hinweis: Bitte stelle sicher, dass die "SteelSeries GG Engine" Software im Hintergrund läuft.*

### ⚙️ Einstellungen & Features

Klicke mit der rechten Maustaste auf das NovaPulse-Symbol in der Taskleiste unten rechts bei der Uhr und wähle **"Settings"**. 

Hier kannst du:
*   **Autostart aktivieren:** Lass NovaPulse automatisch mit Windows starten.
*   **Eigene Sounds einstellen:** Du kannst eigene `.wav`-Dateien abspielen lassen, wenn der Akku leer wird.
*   **Benachrichtigungen testen:** Klicke auf "Test Notification", um zu sehen, wie eine Warnung aussieht.
*   **Genaue API-Stufen sehen:** Eine Grafik zeigt dir genau, wie die SteelSeries API die Akkustände meldet.

### 🐍 Für Entwickler (Run from Source)

Wenn du den Code selbst ausführen oder anpassen möchtest:

1. **Voraussetzungen:** Python 3.10+ und die SteelSeries GG Engine.
2. **Abhängigkeiten installieren:**
   ```bash
   pip install requests windows-toasts pystray pillow customtkinter
   ```
3. **Starten:**
   ```bash
   git clone https://github.com/devjenjen/NovaPulse.git
   cd NovaPulse
   python novapulse.pyw
   ```

### 🔒 Sicherheit & Technische Details

NovaPulse kommuniziert ausschließlich lokal mit der SteelSeries GG Engine über `127.0.0.1` (Localhost).

*   **Zertifikatswarnungen:** Im Quellcode wird `urllib3.disable_warnings()` verwendet. Das ist nötig, da die GG Engine für ihre lokale API ein selbstsigniertes Zertifikat verwendet.
*   **Kein Sicherheitsrisiko:** Da die gesamte Kommunikation nur intern auf deinem eigenen PC stattfindet, besteht keine Gefahr von Man-in-the-Middle-Angriffen aus dem Internet. Es werden keine Daten an externe Server gesendet.

### 🤝 Mitmachen & Feedback

Gefällt dir NovaPulse? Ich freue mich über Feedback, Bug-Reports oder Pull-Requests (Verbesserungen am Code)!

### 📜 Lizenz

Veröffentlicht unter der **MIT License**. Details findest du in der Datei `LICENSE`.

*Entwickelt mit ❤️ für die SteelSeries-Community.*
