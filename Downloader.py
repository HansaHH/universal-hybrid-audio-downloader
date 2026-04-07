import os
import sys
import threading
import time
import re
import customtkinter as ctk
from tkinter import filedialog
import yt_dlp
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# --- PORTABLE RUNTIME SETUP (FFmpeg & Node.js) ---
# Adds the current directory to System PATH so yt-dlp can find bundled node.exe and ffmpeg.exe
if getattr(sys, 'frozen', False):
    # If running as a bundled EXE
    os.environ["PATH"] = sys._MEIPASS + os.pathsep + os.environ["PATH"]
else:
    # If running as a script
    os.environ["PATH"] = os.path.dirname(os.path.abspath(__file__)) + os.pathsep + os.environ["PATH"]
# ------------------------------------------------

# UI Appearance Settings
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def get_ffmpeg_path():
    """ Returns the path to FFmpeg binary based on execution context. """
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, "ffmpeg.exe") 
    return "ffmpeg.exe"

class SuccessDialog(ctk.CTkToplevel):
    """ Custom popup for download completion notification. """
    def __init__(self, master, folder_path, count, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Download Finished")
        self.geometry("500x230")
        self.attributes("-topmost", True)
        
        ctk.CTkLabel(self, text="🎉 Success !!!", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(25, 10))
        ctk.CTkLabel(self, text=f"Total {count} songs saved to:\n{folder_path}", 
                     wraplength=450, font=ctk.CTkFont(size=13, weight="bold")).pack(pady=10, padx=25)
        ctk.CTkButton(self, text="OK", width=120, command=self.destroy, 
                      font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 20))

class MusicDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Universal Music Downloader v11.0") 
        self.geometry("600x600") 
        self.grid_columnconfigure(0, weight=1)
        
        # Theme Selector
        self.theme_menu = ctk.CTkOptionMenu(self, values=["System", "Light", "Dark"], 
                                            command=lambda m: ctk.set_appearance_mode(m), width=100)
        self.theme_menu.grid(row=0, column=0, padx=20, pady=10, sticky="ne")
        
        # Main Title
        ctk.CTkLabel(self, text="Music Downloader", font=ctk.CTkFont(size=30, weight="bold")).grid(row=1, column=0, pady=(10, 45))
        
        # URL Input Section
        self.input_container = ctk.CTkFrame(self, fg_color="transparent")
        self.input_container.grid(row=2, column=0, pady=(0, 10))

        self.url_label = ctk.CTkLabel(self.input_container, text="Enter URL:", font=ctk.CTkFont(size=15, weight="bold"))
        self.url_label.pack(anchor="w") 

        self.url_entry = ctk.CTkEntry(self.input_container, placeholder_text="Enter URL (YouTube, Sarigama, etc.)...", 
                                      width=450, font=ctk.CTkFont(size=13))
        self.url_entry.pack(pady=(5, 0))

        # Progress Percentage
        self.percentage_label = ctk.CTkLabel(self, text="0.0%", font=ctk.CTkFont(size=18, weight="bold"))
        self.percentage_label.grid(row=3, column=0, pady=(5, 0))

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self, width=450)
        self.progress_bar.grid(row=4, column=0, pady=(5, 15))
        self.progress_bar.set(0)

        # Status Display
        self.status_label = ctk.CTkLabel(self, text="Ready", font=ctk.CTkFont(size=13))
        self.status_label.grid(row=5, column=0, pady=5)

        # Control Buttons
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=6, column=0, pady=(50, 20))
        
        self.download_btn = ctk.CTkButton(self.btn_frame, text="Download Now", command=self.start_thread, 
                                          fg_color="#2ecc71", hover_color="#27ae60", width=130, 
                                          font=ctk.CTkFont(size=13, weight="bold"))
        self.download_btn.pack(side="left", padx=10)
        
        self.stop_btn = ctk.CTkButton(self.btn_frame, text="Stop", command=self.stop_action, 
                                      fg_color="#e74c3c", hover_color="#c0392b", width=120, 
                                      font=ctk.CTkFont(size=13, weight="bold"))
        self.stop_btn.pack(side="left", padx=10)

        self.refresh_btn = ctk.CTkButton(self.btn_frame, text="🔄 Refresh", command=self.refresh_ui, 
                                         fg_color="#555555", hover_color="#333333", width=120, 
                                         font=ctk.CTkFont(size=13, weight="bold"))
        self.refresh_btn.pack(side="left", padx=10)

        self.is_stopping = False

    def clean_filename(self, filename):
        """ Sanitize filename by removing illegal characters. """
        return re.sub(r'[\\/*?:"<>|]', "", filename)

    def refresh_ui(self):
        """ Resets the application state and UI. """
        self.is_stopping = True 
        self.url_entry.delete(0, 'end') 
        self.focus_set() 
        self.status_label.configure(text="Ready")
        self.progress_bar.set(0)
        self.percentage_label.configure(text="0.0%")
        self.download_btn.configure(state="normal")

    def progress_hook(self, d):
        """ Callback function to update download progress in real-time. """
        if self.is_stopping:
            raise Exception("UserStopRequest")
        if d['status'] == 'downloading':
            try:
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    percentage = (downloaded / total) * 100
                    if percentage > 99.9: percentage = 99.9
                    self.progress_bar.set(percentage / 100)
                    self.percentage_label.configure(text=f"{percentage:.1f}%")
            except: pass

    def infinite_scraper(self, url):
        """ Scrapes all individual song links from artist/album pages. """
        self.status_label.configure(text="Scanning source... Please wait.")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        links = []
        try:
            driver.get(url)
            time.sleep(5)
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                if self.is_stopping: break
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height: break
                last_height = new_height
            # XPath specifically for Sarigama song patterns
            elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/sinhala-song/') or contains(@href, '/song/')]")
            links = list(set([s.get_attribute('href') for s in elements]))
        except Exception as e: print(f"Scraper Error: {e}")
        finally: driver.quit()
        return links

    def download_logic(self):
        """ Main processing loop for YouTube and Sarigama downloads. """
        url = self.url_entry.get().strip()
        if not url: return
        
        save_path = filedialog.askdirectory()
        if not save_path: return

        self.download_btn.configure(state="disabled")
        self.is_stopping = False
        success_count = 0

        # --- YOUTUBE DOWNLOAD ENGINE ---
        if "youtube.com" in url or "youtu.be" in url:
            self.status_label.configure(text="Processing YouTube link...")
            try:
                ydl_opts_yt = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
                    'ffmpeg_location': get_ffmpeg_path(),
                    'progress_hooks': [self.progress_hook],
                    'ignoreerrors': False, 
                    'download_archive': os.path.join(save_path, 'youtube_history.txt'),
                    'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
                    'quiet': True,
                    'noplaylist': True,
                    'extractor_args': {'youtube': ['player_client=android,web']}
                }
                
                with yt_dlp.YoutubeDL(ydl_opts_yt) as ydl:
                    error_code = ydl.download([url])
                    if error_code == 0: 
                        success_count += 1
                        
            except Exception as e:
                print(f"YouTube Error: {e}")
                if not self.is_stopping:
                    self.status_label.configure(text="Download failed. Security bypass required.")

        # --- SARIGAMA & GENERIC ENGINE ---
        else:
            target_links = [url]
            if "sarigama.lk" in url and ("/artist/" in url or "/album/" in url):
                target_links = self.infinite_scraper(url)

            if not target_links:
                self.status_label.configure(text="No valid songs found!")
                self.download_btn.configure(state="normal")
                return

            total_songs = len(target_links)

            for i, link in enumerate(target_links):
                if self.is_stopping: break
                self.status_label.configure(text=f"Checking song {i+1} of {total_songs}...")

                try:
                    # Duplicate check to skip existing files
                    ydl_info_opts = {'quiet': True, 'noplaylist': True}
                    with yt_dlp.YoutubeDL(ydl_info_opts) as ydl:
                        info = ydl.extract_info(link, download=False)
                        title = info.get('title', f"Song_{i}")
                        clean_title = self.clean_filename(title)
                        final_mp3 = os.path.join(save_path, f"{clean_title}.mp3")

                        if os.path.exists(final_mp3):
                            success_count += 1
                            continue

                    ydl_opts_other = {
                        'format': 'bestaudio/best',
                        'outtmpl': os.path.join(save_path, f"{clean_title}.%(ext)s"), 
                        'ffmpeg_location': get_ffmpeg_path(),
                        'progress_hooks': [self.progress_hook],
                        'ignoreerrors': True,
                        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
                        'quiet': True,
                        'noplaylist': True
                    }
                    self.status_label.configure(text=f"Downloading {i+1} of {total_songs}...")
                    with yt_dlp.YoutubeDL(ydl_opts_other) as ydl:
                        ydl.download([link])
                    success_count += 1

                except Exception as e:
                    if "UserStopRequest" in str(e): break
                    continue

        # Final Status Update
        if not self.is_stopping:
            if success_count > 0:
                self.progress_bar.set(1.0)
                self.percentage_label.configure(text="100.0%")
                self.status_label.configure(text="Task Completed!")
                SuccessDialog(self, save_path, success_count)
            else:
                self.status_label.configure(text="Process failed.")
        else:
            self.status_label.configure(text="Operation stopped.")
            
        self.download_btn.configure(state="normal")

    def start_thread(self):
        """ Background thread to keep the GUI responsive. """
        threading.Thread(target=self.download_logic, daemon=True).start()

    def stop_action(self):
        """ Immediate kill switch for active downloads. """
        self.is_stopping = True
        self.status_label.configure(text="Stopping process...")

if __name__ == "__main__":
    app = MusicDownloaderApp()
    app.mainloop()