# 🌌 NovaPulse – SteelSeries GG Battery Monitor

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Release](https://img.shields.io/badge/Version-v0.1.0-blueviolet)](https://github.com/devjenjen/NovaPulse/releases)

NovaPulse is a lightweight, high-performance background monitor for **SteelSeries Nova Pro Wireless** headsets. It bridges the gap between the SteelSeries GG Engine and your Windows desktop, providing smart notifications and a modern settings interface.

---

## ✨ Key Features

*   **🎯 2-Tier Alert System:** Get notified at 25% (Warning) and 12% (Critical) – precisely tuned to the discrete battery steps of the SteelSeries GG API.
*   **🔋 Charger Monitoring:** Know exactly when your spare battery in the base station is fully charged and ready to swap.
*   **📟 GameSense OLED Support:** Displays a flashing **"!!! SWAP AKKU !!!"** alert directly on your base station's OLED screen when critical.
*   **🎨 Modern Settings GUI:** A beautiful, High-DPI responsive interface built with `customtkinter`, matching the SteelSeries aesthetic.
*   **🔊 Custom Sounds:** Optional .wav support for each alert type (or stick to Windows defaults).
*   **📊 History & Stats:** (Coming soon) Track your battery health and drain cycles over time.

---

## 📸 Impressions

*(Placeholder: Add a screenshot of the new GUI here)*

The new settings interface features:
*   **Visual API Steps:** A custom diagram showing how the GG Engine reports battery levels.
*   **Integrated Testing:** Test your toast notifications and OLED alerts directly from the settings.
*   **Advanced Tuning:** Control poll intervals, startup grace periods, and standby retry logic.

---

## 🚀 Quick Start

### 📦 Download (Recommended)
The easiest way to use NovaPulse is to download the latest pre-compiled executable:
1. Go to the **[Latest Release](https://github.com/devjenjen/NovaPulse/releases/latest)**.
2. Download `NovaPulse.exe`.
3. Run the file. No Python installation required!

---

### 🐍 Run from Source (Advanced)
If you prefer to run the script manually:
1. **Requirements:**
   * **SteelSeries GG Engine** installed and running.
   * **Python 3.10+**
   * Dependencies:
     ```bash
     pip install requests windows-toasts pystray pillow customtkinter
     ```

2. **Installation:**
   Clone the repository and run the script:
   ```bash
   git clone https://github.com/devjenjen/NovaPulse.git
   cd NovaPulse
   python novapulse.pyw
   ```

### 3. Usage
*   **Tray Icon:** Right-click the headset icon in the system tray to open settings, logs, or toggle autostart.
*   **Autostart:** Enable "Start with Windows" in the tray menu or settings to keep NovaPulse running in the background.

---

## 🛠 Advanced Configuration

NovaPulse creates a `config.json` in your `%LOCALAPPDATA%\NovaPulse` folder. While most settings are available in the GUI, you can manually tune:
*   `startup_grace`: Seconds to wait for GG to boot before the first poll.
*   `standby_retry_slow`: How often to check for the headset if GG is offline.

---

## 🤝 Contributing

Contributions are welcome! Whether it's a bug fix, a new feature, or a translation update, feel free to open a Pull Request or Issue.

---

## 🔒 Sicherheit & Technische Details

NovaPulse kommuniziert lokal mit der SteelSeries GG Engine über die Adresse `127.0.0.1` (Localhost). 

*   **Zertifikatswarnungen:** Im Quellcode wird `urllib3.disable_warnings()` verwendet. Dies ist notwendig, da die GG Engine für ihre lokale API ein selbstsigniertes Zertifikat nutzt.
*   **Kein Sicherheitsrisiko:** Da die gesamte Kommunikation ausschließlich innerhalb deines eigenen Rechners stattfindet, besteht kein Risiko für Man-in-the-Middle-Angriffe aus dem Internet. Es werden keine Daten nach außen gesendet.

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for more information.

*Developed with ❤️ for the SteelSeries community.*
