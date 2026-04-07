# 🎵 Universal Hybrid Audio Downloader (Portable)

[![GitHub Release](https://img.shields.io/github/v/release/HansaHH/universal-hybrid-audio-downloader?include_prereleases&style=flat-square)](https://github.com/HansaHH/universal-hybrid-audio-downloader/releases)
[![Python Version](https://img.shields.io/badge/python-3.x-blue.svg?style=flat-square)](https://www.python.org/)
[![UI CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-green.svg?style=flat-square)](https://github.com/TomSchimansky/CustomTkinter)

A powerful, modern, and fully portable desktop application to download high-quality music from **YouTube**, **Sarigama.lk**, and many other platforms. 

Built with Python, this tool combines the power of `yt-dlp` and `Selenium` with a sleek `CustomTkinter` interface to provide a seamless downloading experience.

---

## ✨ Key Features

- **🚀 True Portability (Upgraded):** No installation required! Everything—including Python, FFmpeg, and **Node.js**—is bundled into a single, ready-to-use `.exe` file.
- **🤖 YouTube Anti-Bot Bypass (NEW in v11.0):** Features an embedded Node.js runtime to automatically solve YouTube's new JavaScript security challenges. No external cookies or Node.js installations required!
- **🕸️ Infinite Scraper Engine:** Automatically scrolls and scrapes all valid song links from an entire artist, category, or album page on complex platforms like Sarigama.lk.
- **🧠 Smart Download Tracker:** Remembers previously downloaded songs and skips them automatically to save your data and time!
- **🛡️ Bulletproof Downloading:** Automatically skips broken or restricted links (`ignoreerrors: True`) and continues downloading the rest of the playlist without crashing.
- **🛑 Immediate Stop:** Instantly halt the entire download process at any time with a single click.
- **🎨 Modern UI:** A clean, dark/light mode compatible user interface built with CustomTkinter, featuring real-time status updates and smooth animations.
- **🔗 Hybrid Engine:** Automatically switches between `yt-dlp` and `Selenium` based on the source site to bypass restrictions.
- **🎧 High Quality:** Extracts and converts audio directly to crystal-clear **192kbps MP3** format.

---

## 🚀 How to Use (For Users)

1. **Download:** Go to the [Releases](https://github.com/HansaHH/universal-hybrid-audio-downloader/releases) section and download the latest `.exe` file.
2. **Run:** Double-click the executable (No Python, FFmpeg, or Node.js installation needed!).
3. **Paste Link:** Enter the URL of the song, YouTube playlist, or a full artist/album page.
4. **Download:** Click "Download" and let the app do the work! *(A `download_history.txt` file will automatically track your downloads so you never download duplicates).*

---

## 💻 Tech Stack

- **Core Language:** Python 3.x
- **GUI:** CustomTkinter (Modern, hardware-accelerated UI)
- **Web Automation:** Selenium & WebDriver Manager (For headless web scraping)
- **Audio Extraction:** yt-dlp
- **Anti-Bot Engine:** Node.js (Embedded)
- **Dependencies:** Bundled FFmpeg & FFprobe for seamless audio conversion
- **Bundler:** PyInstaller

---

## 🤝 Contributing
Feel free to fork this repository and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

---

*Built with ❤️ for true music lovers.*

**Developed by [Hasindu Hemal](https://github.com/HansaHH)**