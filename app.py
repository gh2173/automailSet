from flask import Flask, render_template, request, jsonify
import json
import os
import threading
import time
import schedule
from ftp_manager import FTPManager
from email_manager import EmailManager
from datetime import datetime

app = Flask(__name__)
CONFIG_FILE = 'config.json'
LOG_FILE = 'execution_log.txt'

# Job execution (thread-safe lock if needed, but simple boolean for now)
is_running = False

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(new_config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(new_config, f, indent=4)
    # Reload schedule if time changed
    update_schedule()

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {message}\n"
    print(entry.strip())
    with open(LOG_FILE, 'a') as f:
        f.write(entry)

def run_automation_job():
    global is_running
    if is_running:
        log_message("Job already running. Skipping.")
        return

    is_running = True
    log_message("Starting automation job...")

    config = load_config()
    ftp_cfg = config.get('ftp', {})
    email_cfg = config.get('email', {})

    ftp_mgr = FTPManager(ftp_cfg['host'], ftp_cfg['port'], ftp_cfg['user'], ftp_cfg['password'], ftp_cfg['target_dir'])

    # 1. Connect to FTP
    success, msg = ftp_mgr.connect()
    if not success:
        log_message(f"FTP Connect Failed: {msg}")
        is_running = False
        return

    # 2. Find latest date folder (YYYY-MM-DD format)
    latest_folder, msg = ftp_mgr.find_latest_date_folder()
    if not latest_folder:
        log_message(f"Find Folder Failed: {msg}")
        ftp_mgr.disconnect()
        is_running = False
        return

    log_message(f"Found latest folder: {latest_folder}")

    # 3. Get PDF and PNG files from the folder
    pdf_file, png_file, msg = ftp_mgr.get_files_in_folder(latest_folder)
    if not pdf_file:
        log_message(f"Get Files Failed: {msg}")
        ftp_mgr.disconnect()
        is_running = False
        return

    log_message(f"Found PDF: {pdf_file}, PNG: {png_file}")

    # 4. Download PDF and PNG files
    local_pdf_path = os.path.join(os.getcwd(), pdf_file)
    local_png_path = os.path.join(os.getcwd(), png_file) if png_file else None

    # Download PDF - need to be in the folder
    try:
        ftp_mgr.ftp.cwd(latest_folder)
        success, msg = ftp_mgr.download_file(pdf_file, local_pdf_path)
        if not success:
            log_message(f"Download PDF Failed: {msg}")
            ftp_mgr.disconnect()
            is_running = False
            return

        log_message(f"Downloaded PDF: {local_pdf_path}")

        # Download PNG if it exists
        if png_file:
            success, msg = ftp_mgr.download_file(png_file, local_png_path)
            if not success:
                log_message(f"Download PNG Failed: {msg}")
                local_png_path = None
            else:
                log_message(f"Downloaded PNG: {local_png_path}")

        # Return to parent folder
        ftp_mgr.ftp.cwd('..')

    except Exception as e:
        log_message(f"FTP Navigation Error: {str(e)}")
        ftp_mgr.disconnect()
        is_running = False
        return

    ftp_mgr.disconnect()

    # 5. Email File
    email_mgr = EmailManager(email_cfg['smtp_server'], email_cfg['smtp_port'], email_cfg['sender_email'], email_cfg['sender_password'])
    subject = f"[Automail] RPA 관제시스템 자동 리포트 ({latest_folder})"
    body = "해당 메일은 RPA 관제시스템에서 자동 송부되는 Automail입니다. -> http://192.168.195.23.5000/public/OperationRate.html"

    # Send email with PNG inline and PDF attached
    if local_png_path and os.path.exists(local_png_path):
        success, msg = email_mgr.send_email_with_image_and_pdf(email_cfg['recipients'], subject, body, local_pdf_path, local_png_path)
    else:
        # Fallback to PDF only if PNG is not available
        success, msg = email_mgr.send_email_with_attachment(email_cfg['recipients'], subject, body, local_pdf_path)

    if success:
        log_message("Email sent successfully.")
    else:
        log_message(f"Email Failed: {msg}")

    # Cleanup downloaded files
    if os.path.exists(local_pdf_path):
        os.remove(local_pdf_path)
        log_message(f"Cleaned up: {local_pdf_path}")

    if local_png_path and os.path.exists(local_png_path):
        os.remove(local_png_path)
        log_message(f"Cleaned up: {local_png_path}")

    is_running = False
    log_message("Job finished.")

# Scheduler Thread
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

def update_schedule():
    config = load_config()
    run_time = config.get('schedule', {}).get('run_time', '09:00')
    schedule.clear()
    schedule.every().day.at(run_time).do(run_automation_job)
    log_message(f"Schedule updated. Will run daily at {run_time}")

# Initial Schedule Setup
update_schedule()
# Start background thread
schedule_thread = threading.Thread(target=run_schedule, daemon=True)
schedule_thread.start()

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    if request.method == 'POST':
        new_config = request.json
        save_config(new_config)
        return jsonify({"status": "success", "message": "Configuration saved"})
    else:
        return jsonify(load_config())

@app.route('/api/run_now', methods=['POST'])
def run_now():
    # Run in a separate thread to avoid blocking response
    threading.Thread(target=run_automation_job).start()
    return jsonify({"status": "success", "message": "Job triggered manually"})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    if not os.path.exists(LOG_FILE):
        return jsonify({"logs": []})
    
    # Return last 50 lines
    with open(LOG_FILE, 'r') as f:
        lines = f.readlines()
        return jsonify({"logs": lines[-50:]})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
