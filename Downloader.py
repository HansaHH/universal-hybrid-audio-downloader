import os
import sys
import threading
import time
import customtkinter as ctk
from tkinter import filedialog
import yt_dlp
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# Global UI Configuration
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def get_ffmpeg_path():
    """ 
    This function finds the actual binary file path of FFmpeg.
    Crucial for true portability.
    """
    if getattr(sys, 'frozen', False):
        # Path when running from an EXE (Bundled temporary folder)
        # BUG FIX: We now return the full path to the binary file itself
        return os.path.join(sys._MEIPASS, "ffmpeg.exe") 
    return "ffmpeg.exe" # Path when running from script (must be in the same folder)

class SuccessDialog(ctk.CTkToplevel):
    """ Custom window that appears after a successful download. """
    def __init__(self, master, folder_path, count, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Download Finished")
        self.geometry("500x230")
        self.attributes("-topmost", True)
        ctk.CTkLabel(self, text="🎉 Success !!!", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(25, 10))
        ctk.CTkLabel(self, text=f"Total {count} songs saved to:\n{folder_path}", wraplength=450).pack(pady=10, padx=25)
        ctk.CTkButton(self, text="OK", width=120, command=self.destroy).pack(pady=(15, 20))

class MusicDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Universal Music Downloader v8.0")
        self.geometry("600x520")
        self.grid_columnconfigure(0, weight=1)
        
        # Theme/Appearance Selector
        self.theme_menu = ctk.CTkOptionMenu(self, values=["System", "Light", "Dark"], command=lambda m: ctk.set_appearance_mode(m), width=100)
        self.theme_menu.grid(row=0, column=0, padx=20, pady=10, sticky="ne")
        ctk.CTkLabel(self, text="Music Downloader", font=ctk.CTkFont(size=26, weight="bold")).grid(row=1, column=0, pady=(10, 20))
        
        # URL Input Entry
        self.url_entry = ctk.CTkEntry(self, placeholder_text="Enter URL (YouTube, Sarigama, etc.)...", width=450)
        self.url_entry.grid(row=2, column=0, pady=10)

        # Progress Percentage Display
        self.percentage_label = ctk.CTkLabel(self, text="0.0%", font=ctk.CTkFont(size=16, weight="bold"))
        self.percentage_label.grid(row=3, column=0, pady=(10, 0))

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self, width=450)
        self.progress_bar.grid(row=4, column=0, pady=(5, 15))
        self.progress_bar.set(0)

        # Activity Status Label
        self.status_label = ctk.CTkLabel(self, text="Ready", font=ctk.CTkFont(size=13))
        self.status_label.grid(row=5, column=0, pady=5)

        # Control Buttons Frame
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=6, column=0, pady=20)
        
        self.download_btn = ctk.CTkButton(self.btn_frame, text="Download Now", command=self.start_thread, fg_color="#2ecc71", hover_color="#27ae60")
        self.download_btn.pack(side="left", padx=10)
        
        self.stop_btn = ctk.CTkButton(self.btn_frame, text="Stop", command=self.stop_action, fg_color="#e74c3c", hover_color="#c0392b")
        self.stop_btn.pack(side="left", padx=10)

        self.is_stopping = False

    def progress_hook(self, d):
        """ Handles real-time progress updates and immediate stopping. """
        if self.is_stopping:
            raise Exception("UserStopRequest") # Kills the download immediately
            
        if d['status'] == 'downloading':
            try:
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    percentage = (downloaded / total) * 100
                    if percentage > 99.9: percentage = 99.9
                    self.progress_bar.set(percentage / 100)
                    self.percentage_label.configure(text=f"{percentage:.1f}%")
            except: 
                pass

    def infinite_scraper(self, url):
        """ Scans a website to find all song links by scrolling to the bottom. """
        self.status_label.configure(text="Scanning all songs... Please wait.")
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
                
            elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/sinhala-song/') or contains(@href, '/song/')]")
            links = list(set([s.get_attribute('href') for s in elements]))
        except Exception as e:
            print(f"Scraper Error: {e}")
        finally:
            driver.quit()
        return links

    def download_logic(self):
        """ Core logic for processing URLs and managing the download queue. """
        url = self.url_entry.get().strip()
        if not url: return

        save_path = filedialog.askdirectory()
        if not save_path: return

        self.download_btn.configure(state="disabled")
        self.is_stopping = False
        
        target_links = [url]
        if "sarigama.lk" in url and ("/artist/" in url or "/album/" in url):
            target_links = self.infinite_scraper(url)

        if not target_links:
            self.status_label.configure(text="No songs found! Check URL.")
            self.download_btn.configure(state="normal")
            return

        total_songs = len(target_links)
        success_count = 0
        
        # FIX: The loop is now bulletproof. If one song fails, it continues to the next.
        for i, link in enumerate(target_links):
            if self.is_stopping: break
            
            self.status_label.configure(text=f"Downloading {i+1} of {total_songs}...")
            
            try:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
                    'ffmpeg_location': get_ffmpeg_path(),
                    'progress_hooks': [self.progress_hook],
                    'ignoreerrors': True, # FIX: Don't crash on bad links
                    'download_archive': os.path.join(save_path, 'download_history.txt'),
                    'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([link])
                
                success_count += 1
                
            except Exception as e:
                # If user clicked stop, break the whole loop
                if "UserStopRequest" in str(e):
                    break
                else:
                    # If it's just a broken song, skip it and continue
                    print(f"Skipping a failed song: {e}")
                    continue

        # Final UI Updates after the loop finishes or stops
        if self.is_stopping:
            self.status_label.configure(text="Download Stopped By User.")
        else:
            self.progress_bar.set(1.0)
            self.percentage_label.configure(text="100.0%")
            if success_count > 0:
                self.status_label.configure(text="Finished Successfully!")
                SuccessDialog(self, save_path, success_count)
            else:
                self.status_label.configure(text="Failed to download any songs.")
                
        self.download_btn.configure(state="normal")

    def start_thread(self):
        """ Runs the download process in a background thread. """
        threading.Thread(target=self.download_logic, daemon=True).start()

    def stop_action(self):
        """ Triggers the stop flag to kill active downloads. """
        self.is_stopping = True
        self.status_label.configure(text="Stopping immediately...")

if __name__ == "__main__":
    app = MusicDownloaderApp()
    app.mainloop()