import ftplib
import re
import os
from datetime import datetime

class FTPManager:
    def __init__(self, host, port, user, password, target_dir):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.target_dir = target_dir
        self.ftp = None

    def connect(self):
        try:
            self.ftp = ftplib.FTP()
            self.ftp.connect(self.host, self.port)
            self.ftp.login(self.user, self.password)
            self.ftp.cwd(self.target_dir)
            return True, "Connected successfully"
        except Exception as e:
            error_msg = str(e)
            if "550" in error_msg and self.ftp:
                try:
                    # If CWD fails, try to list current directories to help debugging
                    current_dirs = self.ftp.nlst()
                    error_msg += f". Available directories: {current_dirs}"
                except:
                    pass
            return False, error_msg

    def disconnect(self):
        if self.ftp:
            try:
                self.ftp.quit()
            except:
                self.ftp.close()

    def find_latest_pdf(self):
        if not self.ftp:
            return None, "Not connected"

        try:
            files = self.ftp.nlst()
        except ftplib.error_perm as resp:
            if str(resp) == "550 No files found":
                 files = []
            else:
                 return None, str(resp)

        # Pattern: RPA-성공률-YYYY-MM-dd-hh-mm.pdf
        # Regex to capture the date parts: (\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})
        pattern = re.compile(r'RPA-성공률-(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})\.pdf')
        
        matched_files = []
        for filename in files:
            match = pattern.match(filename)
            if match:
                # Create a datetime object for comparison
                dt_str = f"{match.group(1)}-{match.group(2)}-{match.group(3)} {match.group(4)}:{match.group(5)}"
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                matched_files.append((dt, filename))

        if not matched_files:
            return None, "No matching files found"

        # Sort by datetime descending
        matched_files.sort(key=lambda x: x[0], reverse=True)
        latest_file = matched_files[0][1]
        
        return latest_file, "Found latest file"

    def download_file(self, filename, local_path):
        if not self.ftp:
            return False, "Not connected"

        try:
            with open(local_path, 'wb') as f:
                self.ftp.retrbinary('RETR ' + filename, f.write)
            return True, "Download successful"
        except Exception as e:
            return False, str(e)
