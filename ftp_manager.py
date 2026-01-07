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

    def find_latest_date_folder(self):
        """오늘 날짜 또는 가장 최신 날짜 폴더 찾기 (YYYY-MM-DD 형식)"""
        if not self.ftp:
            return None, "Not connected"

        try:
            items = self.ftp.nlst()
        except ftplib.error_perm as resp:
            return None, str(resp)

        # YYYY-MM-DD 형식의 폴더명 찾기
        date_pattern = re.compile(r'^(\d{4})-(\d{2})-(\d{2})$')
        matched_folders = []

        for item in items:
            match = date_pattern.match(item)
            if match:
                try:
                    dt_str = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                    dt = datetime.strptime(dt_str, "%Y-%m-%d")
                    matched_folders.append((dt, item))
                except ValueError:
                    continue

        if not matched_folders:
            return None, "No date folders found"

        # 가장 최신 폴더 선택
        matched_folders.sort(key=lambda x: x[0], reverse=True)
        latest_folder = matched_folders[0][1]

        return latest_folder, "Found latest date folder"

    def get_files_in_folder(self, folder_name):
        """폴더 안의 PDF와 PNG 파일 찾기"""
        if not self.ftp:
            return None, None, "Not connected"

        try:
            # 폴더로 이동
            self.ftp.cwd(folder_name)
            files = self.ftp.nlst()

            # PDF와 PNG 파일 찾기
            pdf_file = None
            png_file = None

            for filename in files:
                if filename.lower().endswith('.pdf'):
                    pdf_file = filename
                elif filename.lower().endswith('.png'):
                    png_file = filename

            # 원래 폴더로 돌아오기
            self.ftp.cwd('..')

            if not pdf_file:
                return None, None, "No PDF file found in folder"
            if not png_file:
                return pdf_file, None, "No PNG file found (PDF only)"

            return pdf_file, png_file, "Found files"

        except Exception as e:
            try:
                self.ftp.cwd('..')
            except:
                pass
            return None, None, str(e)

    def download_file(self, filename, local_path):
        if not self.ftp:
            return False, "Not connected"

        try:
            with open(local_path, 'wb') as f:
                self.ftp.retrbinary('RETR ' + filename, f.write)
            return True, "Download successful"
        except Exception as e:
            return False, str(e)
