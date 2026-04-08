import os
import sys
import threading
import time
import re
import subprocess
import urllib.request
import customtkinter as ctk
from tkinter import filedialog
import yt_dlp
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# --- PORTABLE RUNTIME SETUP ---
# Ensures binaries like ffmpeg and node are found by the app
if getattr(sys, 'frozen', False):
    os.environ["PATH"] = sys._MEIPASS + os.pathsep + os.environ["PATH"]
else:
    os.environ["PATH"] = os.path.dirname(os.path.abspath(__file__)) + os.pathsep + os.environ["PATH"]

# Global UI Theme Settings
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def get_ffmpeg_path():
    """ Returns the path to the ffmpeg binary """
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, "ffmpeg.exe") 
    return "ffmpeg.exe"

class SuccessDialog(ctk.CTkToplevel):
    """ Completion popup notification """
    def __init__(self, master, folder_path, count, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Finished")
        self.geometry("500x230")
        self.attributes("-topmost", True)
        ctk.CTkLabel(self, text="🎉 Success !!!", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(25, 10))
        ctk.CTkLabel(self, text=f"Total {count} songs saved to:\n{folder_path}", 
                     wraplength=450, font=ctk.CTkFont(size=13, weight="bold")).pack(pady=10, padx=25)
        ctk.CTkButton(self, text="OK", width=120, command=self.destroy, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 20))

class MusicDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Universal Music Downloader v11.0") 
        self.geometry("600x780") 
        self.grid_columnconfigure(0, weight=1)
        
        # --- HEADER SECTION ---
        ctk.CTkLabel(self, text="Music Downloader", font=ctk.CTkFont(size=30, weight="bold")).grid(row=0, column=0, pady=(50, 60))
        
        # --- INPUT SECTION (Classic Style Restored) ---
        self.input_container = ctk.CTkFrame(self, fg_color="transparent")
        self.input_container.grid(row=1, column=0, pady=(0, 10))

        # The 'Enter URL:' label above the input box
        self.url_label = ctk.CTkLabel(self.input_container, text="Enter URL:", font=ctk.CTkFont(size=15, weight="bold"))
        self.url_label.pack(anchor="w") 

        # Input box with placeholder text
        self.url_entry = ctk.CTkEntry(self.input_container, placeholder_text="Enter URL (YouTube, Sarigama, etc.)...", 
                                      width=460, height=35, font=ctk.CTkFont(size=13))
        self.url_entry.pack(pady=(5, 0))

        # --- PROGRESS SECTION ---
        self.percentage_label = ctk.CTkLabel(self, text="0.0%", font=ctk.CTkFont(size=18, weight="bold"))
        self.percentage_label.grid(row=2, column=0, pady=(20, 5))

        self.progress_bar = ctk.CTkProgressBar(self, width=460)
        self.progress_bar.grid(row=3, column=0, pady=(5, 15))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self, text="Ready", font=ctk.CTkFont(size=13))
        self.status_label.grid(row=4, column=0, pady=5)

        # --- ACTION BUTTONS ---
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=5, column=0, pady=(35, 20))
        
        self.download_btn = ctk.CTkButton(self.btn_frame, text="Download Now", command=self.start_thread, 
                                          fg_color="#2ecc71", hover_color="#27ae60", width=140, height=42, font=ctk.CTkFont(weight="bold"))
        self.download_btn.pack(side="left", padx=10)
        
        self.stop_btn = ctk.CTkButton(self.btn_frame, text="Stop", command=self.stop_action, 
                                      fg_color="#e74c3c", hover_color="#c0392b", width=120, height=42, font=ctk.CTkFont(weight="bold"))
        self.stop_btn.pack(side="left", padx=10)

        self.refresh_btn = ctk.CTkButton(self.btn_frame, text="🔄 Refresh UI", command=self.refresh_ui, 
                                         fg_color="#555555", width=120, height=42, font=ctk.CTkFont(weight="bold"))
        self.refresh_btn.pack(side="left", padx=10)

        # --- SECURITY UPDATE SECTION (Always visible) ---
        self.separator = ctk.CTkFrame(self, height=2, width=500, fg_color="gray")
        self.separator.grid(row=6, column=0, pady=(40, 5))

        # Static instruction note
        self.instruction_note = ctk.CTkLabel(self, text="Note: If YouTube downloads fail, click below to update the security engine.", 
                                             font=ctk.CTkFont(size=11, slant="italic"), text_color="gray")
        self.instruction_note.grid(row=7, column=0, pady=(5, 0))

        # Dynamic solution label (Appears only on error)
        self.solution_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12, weight="bold"), text_color="#e67e22")
        self.solution_label.grid(row=8, column=0, pady=(2, 0))

        # Update button
        self.update_btn = ctk.CTkButton(self, text="🚀 UPDATE SECURITY ENGINE", command=self.start_update_thread, 
                                         fg_color="#3498db", hover_color="#2980b9", width=300, height=40, font=ctk.CTkFont(weight="bold"))
        self.update_btn.grid(row=9, column=0, pady=(10, 30))

        self.is_stopping = False

    def clean_filename(self, filename):
        """ Sanitize filename by removing illegal characters """
        return re.sub(r'[\\/*?:"<>|]', "", filename)

    def progress_hook(self, d):
        """ Updates download progress on UI """
        if self.is_stopping: raise Exception("UserStopRequest")
        if d['status'] == 'downloading':
            try:
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                if total > 0:
                    perc = (d.get('downloaded_bytes', 0) / total) * 100
                    self.progress_bar.set(perc / 100)
                    self.percentage_label.configure(text=f"{perc:.1f}%")
            except: pass

    def update_engine(self):
        """ Downloads latest engine to fix security blocks in chunks to allow stopping """
        try:
            # Disable Download and Update buttons, but keep Stop active!
            self.download_btn.configure(state="disabled")
            self.update_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            
            self.status_label.configure(text="Updating engine... Please wait.")
            
            # Use chunked download so it can be stopped anytime
            self.is_stopping = False
            req = urllib.request.urlopen("https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe")
            with open("yt-dlp.tmp", 'wb') as f:
                while True:
                    if self.is_stopping:
                        raise Exception("UserStopRequest") # Break download if stopped
                    chunk = req.read(8192) # Download in small 8KB chunks
                    if not chunk:
                        break
                    f.write(chunk)
            
            # If download completes safely, replace the old engine
            if os.path.exists("yt-dlp.exe"):
                try: os.remove("yt-dlp.exe")
                except: pass
            os.rename("yt-dlp.tmp", "yt-dlp.exe")
            
            self.status_label.configure(text="Engine Updated! Click 'Download Now' button.")
            self.solution_label.configure(text="") # Clear error message if successful
            
        except Exception as e:
            if "UserStopRequest" in str(e):
                self.status_label.configure(text="Update stopped. Incomplete files removed.")
            else:
                self.status_label.configure(text="Update failed!")
        finally:
            # Always clean up temp file if update was stopped or failed
            if os.path.exists("yt-dlp.tmp"):
                try: os.remove("yt-dlp.tmp")
                except: pass
                
            self.update_btn.configure(state="normal")
            self.download_btn.configure(state="normal")

    def infinite_scraper(self, url):
        """ Scrapes music links from Sarigama pages extremely fast """
        self.status_label.configure(text="Scanning Sarigama...")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        
        # Block images and unnecessary data to speed up loading
        options.add_argument("--blink-settings=imagesEnabled=false")
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        links = []
        try:
            driver.get(url)
            time.sleep(2) # Reduced initial wait time
            last_h = driver.execute_script("return document.body.scrollHeight")
            while True:
                if self.is_stopping: break
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.2) # Reduced scroll wait time (Fast scroll)
                new_h = driver.execute_script("return document.body.scrollHeight")
                if new_h == last_h: break
                last_h = new_h
            elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/sinhala-song/') or contains(@href, '/song/')]")
            links = list(set([s.get_attribute('href') for s in elements]))
        except: pass
        finally: driver.quit()
        return links

    def download_logic(self):
        """ Main download process orchestration """
        url = self.url_entry.get().strip()
        if not url: return
        save_path = filedialog.askdirectory()
        if not save_path: return

        self.download_btn.configure(state="disabled")
        # Disable update button while downloading
        self.update_btn.configure(state="disabled")
        self.solution_label.configure(text="")
        self.is_stopping = False
        success_count = 0
        failed = False

        # --- YOUTUBE LOGIC ---
        if "youtube.com" in url or "youtu.be" in url:
            browsers = ['chrome', 'edge', 'brave', 'firefox', 'opera']
            download_success = False

            # Try browsers first
            for browser in browsers:
                if self.is_stopping or download_success: break
                self.status_label.configure(text=f"Bypassing with {browser.title()}...")
                try:
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
                        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
                        'ffmpeg_location': get_ffmpeg_path(),
                        'quiet': True, 
                        'progress_hooks': [self.progress_hook],
                        'cookiesfrombrowser': (browser,),
                        'js_runtimes': {'node': {}},
                        'extractor_args': {'youtube': ['player_client=ios,web']},
                        'download_archive': os.path.join(save_path, 'youtube_history.txt')
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        error_code = ydl.download([url])
                        if error_code == 0:
                            download_success = True
                            success_count += 1
                except: continue

            # Fallback to Node.js Safe Mode (No Cookies) if browsers are busy/failed
            if not download_success and not self.is_stopping:
                self.status_label.configure(text="Safe Mode (Node.js) active...")
                try:
                    ydl_opts_safe = {
                        'format': 'bestaudio/best',
                        'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
                        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
                        'ffmpeg_location': get_ffmpeg_path(),
                        'quiet': True, 
                        'progress_hooks': [self.progress_hook],
                        'js_runtimes': {'node': {}}, # Use bundled node.exe for bypass
                        'extractor_args': {'youtube': ['player_client=android,web']}, # Android client often bypasses cookie requirements
                        'download_archive': os.path.join(save_path, 'youtube_history.txt')
                    }
                    with yt_dlp.YoutubeDL(ydl_opts_safe) as ydl:
                        error_code = ydl.download([url])
                        if error_code == 0:
                            download_success = True
                            success_count += 1
                except:
                    failed = True
                
                if not download_success: failed = True

        # --- SARIGAMA & GENERIC LOGIC ---
        else:
            target_links = [url]
            if "sarigama.lk" in url and ("/artist/" in url or "/album/" in url):
                target_links = self.infinite_scraper(url)

            for i, link in enumerate(target_links):
                if self.is_stopping: break
                self.status_label.configure(text=f"Downloading {i+1} of {len(target_links)}...")
                
                try:
                    # Duplicate check for Sarigama links
                    ydl_info_opts = {'quiet': True, 'noplaylist': True}
                    with yt_dlp.YoutubeDL(ydl_info_opts) as ydl:
                        info = ydl.extract_info(link, download=False)
                        title = info.get('title', f"Song_{i}")
                        clean_title = self.clean_filename(title)
                        final_mp3 = os.path.join(save_path, f"{clean_title}.mp3")

                        if os.path.exists(final_mp3):
                            success_count += 1
                            continue # Skip the actual download process
                    
                    ydl_opts_other = {
                        'format': 'bestaudio/best',
                        'outtmpl': os.path.join(save_path, f"{clean_title}.%(ext)s"),
                        'progress_hooks': [self.progress_hook],
                        'quiet': True,
                        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]
                    }
                    with yt_dlp.YoutubeDL(ydl_opts_other) as ydl:
                        ydl.download([link])
                        success_count += 1
                except: failed = True; continue

        if not self.is_stopping:
            if success_count > 0:
                self.progress_bar.set(1.0)
                self.percentage_label.configure(text="100%")
                self.status_label.configure(text="Task Completed!")
                SuccessDialog(self, save_path, success_count)
            elif failed:
                self.status_label.configure(text="Download failed!")
                self.solution_label.configure(text="Solution: Close browsers, install Chrome/Edge, log into YouTube, or Update Engine.")
        else:
            # --- CLEANUP LOGIC FOR INCOMPLETE SONGS ---
            self.status_label.configure(text="Cleaning up incomplete files...")
            time.sleep(1) # Give Windows a second to release file locks
            try:
                for file in os.listdir(save_path):
                    if file.endswith(".part") or file.endswith(".ytdl"):
                        try:
                            os.remove(os.path.join(save_path, file))
                        except: pass
            except: pass
            self.status_label.configure(text="Stopped. Incomplete files removed.")

        self.download_btn.configure(state="normal")
        # Re-enable update button after downloading
        self.update_btn.configure(state="normal")

    def start_thread(self): threading.Thread(target=self.download_logic, daemon=True).start()
    def start_update_thread(self): threading.Thread(target=self.update_engine, daemon=True).start()
    
    def refresh_ui(self): 
        """ Full reset of UI and placeholder text """
        self.is_stopping = True
        self.url_entry.delete(0, 'end')
        self.status_label.configure(text="Ready")
        self.progress_bar.set(0)
        self.percentage_label.configure(text="0.0%")
        self.solution_label.configure(text="")
        
        # Reset all buttons
        self.download_btn.configure(state="normal")
        self.update_btn.configure(state="normal")
        self.stop_btn.configure(state="normal")
        self.focus_set()

    def stop_action(self): 
        self.is_stopping = True
        self.status_label.configure(text="Stopping process...")
        self.update_btn.configure(state="normal")

if __name__ == "__main__":
    app = MusicDownloaderApp()
    app.mainloop()