import tkinter as tk
from tkinter import messagebox, filedialog
import yt_dlp
import os
import sys
import threading
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# --- FFmpeg Path Resolution ---
# PyInstaller eken hadana temporary path eka (MEIPASS) hoyaganna logic eka
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# Global variables
stop_requested = False

def sarigama_logic(target_url, save_path):
    global stop_requested
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless') # Browser eka penne nathi wenna meka danna puluwan
    prefs = {"download.default_directory": save_path, "download.prompt_for_download": False}
    options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    try:
        driver.get(target_url)
        time.sleep(5)
        songs = driver.find_elements(By.XPATH, "//a[contains(@href, '/sinhala-song/')]")
        links = list(set([s.get_attribute('href') for s in songs]))

        for index, link in enumerate(links, 1):
            if stop_requested: break
            
            driver.get(link)
            time.sleep(2)
            try:
                download_btn = driver.find_element(By.PARTIAL_LINK_TEXT, "Download")
                download_btn.click()
                time.sleep(3)
            except:
                continue
    finally:
        driver.quit()

def download_media():
    global stop_requested
    stop_requested = False 
    
    url = url_entry.get().strip()
    if not url or url == "Paste your URL here...":
        messagebox.showwarning("Warning", "Please enter a valid URL!")
        return

    save_path = filedialog.askdirectory()
    if not save_path: return

    status_label.config(text="Processing... please wait.", fg="blue")
    download_btn.config(state="disabled")
    stop_btn.config(state="normal")
    
    def run_process():
        try:
            if "sarigama.lk" in url:
                sarigama_logic(url, save_path.replace("/", "\\"))
            else:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': f'{save_path}/%(title)s.%(ext)s',
                    'ffmpeg_location': application_path,  # <--- Bundled FFmpeg path eka methanata denawa
                    'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            
            if stop_requested:
                status_label.config(text="Stopped by User", fg="orange")
            else:
                status_label.config(text="Process Finished!", fg="green")
                messagebox.showinfo("Success", "Task completed!")
                
        except Exception as e:
            status_label.config(text="Error!", fg="red")
            messagebox.showerror("Error", str(e))
        finally:
            download_btn.config(state="normal")
            stop_btn.config(state="disabled")

    threading.Thread(target=run_process).start()

def request_stop():
    global stop_requested
    stop_requested = True
    status_label.config(text="Stopping... please wait.", fg="orange")
    stop_btn.config(state="disabled")

# --- UI Placeholder Logic ---
def on_entry_click(event):
    if url_entry.get() == 'Paste your URL here...':
       url_entry.delete(0, "end") 
       url_entry.insert(0, '') 
       url_entry.config(fg = 'black')

def on_focusout(event):
    if url_entry.get() == '':
        url_entry.insert(0, 'Paste your URL here...')
        url_entry.config(fg = 'grey')

# --- UI Setup ---
root = tk.Tk()
root.title("Universal Music Downloader v3.0 (Portable)")
root.geometry("550x320")
root.configure(bg="#f0f0f0")

tk.Label(root, text="Universal Music Downloader", font=("Segoe UI", 18, "bold"), bg="#f0f0f0").pack(pady=15)

# Label for Input
tk.Label(root, text="Enter URL (YouTube, Sarigama, etc.):", font=("Segoe UI", 10), bg="#f0f0f0").pack()

# URL Entry with Placeholder
url_entry = tk.Entry(root, width=60, font=("Segoe UI", 10), fg='grey', bd=2, relief="groove")
url_entry.insert(0, 'Paste your URL here...')
url_entry.bind('<FocusIn>', on_entry_click)
url_entry.bind('<FocusOut>', on_focusout)
url_entry.pack(pady=10, padx=20)

# Buttons Frame
btn_frame = tk.Frame(root, bg="#f0f0f0")
btn_frame.pack(pady=20)

download_btn = tk.Button(btn_frame, text="Download Now", command=download_media, bg="#28a745", fg="white", width=15, height=2, font=("Segoe UI", 10, "bold"), relief="flat")
download_btn.grid(row=0, column=0, padx=10)

stop_btn = tk.Button(btn_frame, text="Stop", command=request_stop, bg="#dc3545", fg="white", width=15, height=2, font=("Segoe UI", 10, "bold"), relief="flat", state="disabled")
stop_btn.grid(row=0, column=1, padx=10)

status_label = tk.Label(root, text="Ready", font=("Segoe UI", 10), fg="gray", bg="#f0f0f0")
status_label.pack(pady=5)

root.mainloop()