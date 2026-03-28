# 🎵 Universal Hybrid Audio Downloader (Portable)

[![GitHub Release](https://img.shields.io/github/v/release/HansaHH/universal-hybrid-audio-downloader?include_prereleases&style=flat-square)](https://github.com/HansaHH/universal-hybrid-audio-downloader/releases)
[![Python Version](https://img.shields.io/badge/python-3.x-blue.svg?style=flat-square)](https://www.python.org/)

A powerful and user-friendly desktop application to download high-quality audio from various platforms, including **YouTube**, **Sarigama.lk**, and more. 

Built with Python, this tool combines the power of `yt-dlp` and `Selenium` to provide a seamless downloading experience.

---

## ✨ Key Features

- **🚀 True Portability:** No need to install Python or FFmpeg manually. Everything is bundled into a single `.exe` file.
- **🔗 Hybrid Engine:** Automatically switches between `yt-dlp` and `Selenium` based on the source site to bypass restrictions.
- **🎧 High Quality:** Extracts and converts audio directly to **192kbps MP3** format.
- **🤖 Smart Multi-Song Automation:** - If a page contains a list of songs (e.g., a category or album on Sarigama.lk), the app **automatically navigates** through each song link.
  - It downloads the tracks **one by one** without any manual intervention. Just paste the main link and let the app do the work!
- **🎨 Simple UI:** Minimalist interface with real-time status updates.

---

## 🛠 How to Use

1. **Download:** Go to the [Releases](https://github.com/HansaHH/universal-hybrid-audio-downloader/releases) section and download the latest `MusicDownloader.exe`.
2. **Run:** Double-click the executable (No installation required).
3. **Paste Link:** Enter the URL of the song or the page containing multiple songs.
4. **Download:** Click "Download Now" and wait for the "Ready" status. Your music will be saved in the same folder as the app.

---

## 💻 Tech Stack

- **Language:** Python 3.x
- **Libraries:** Tkinter (GUI), Selenium (Web Automation), yt-dlp (Audio Extraction)
- **Bundler:** PyInstaller
- **Dependencies:** Bundled FFmpeg for audio conversion.

---

## 📝 Note on Automation Logic
The app includes specialized logic for complex platforms. When a "List" or "Album" URL is detected, the automation engine:
1. Scans the page for all valid song links.
2. Visits each link sequentially using a headless browser.
3. Triggers the download and conversion process for every single track.

---

## 🤝 Contributing
Feel free to fork this repository and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

**Developed with ❤️ by [Hasindu Hemal](https://github.com/HansaHH)**