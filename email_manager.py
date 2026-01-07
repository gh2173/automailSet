import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
import os
from email.header import Header


class EmailManager:
    def __init__(self, smtp_server, smtp_port, sender_email, sender_password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password

    def _generate_html_body(self, body_text, filename):
        """Generate professional HTML email body with file information"""
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; border-bottom: 3px solid #0066cc; padding-bottom: 20px; margin-bottom: 30px; }}
                .header h1 {{ color: #0066cc; margin: 0; font-size: 24px; }}
                .content {{ color: #333; line-height: 1.8; margin-bottom: 30px; }}
                .file-info {{ background-color: #e8f4f8; padding: 20px; border-left: 4px solid #0066cc; border-radius: 4px; margin: 20px 0; }}
                .file-info h3 {{ color: #0066cc; margin-top: 0; }}
                .file-info p {{ margin: 10px 0; color: #555; }}
                .file-name {{ font-weight: bold; color: #0066cc; word-break: break-all; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; border-top: 1px solid #ddd; padding-top: 20px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 RPA Daily Report</h1>
                </div>

                <div class="content">
                    <p>{body_text}</p>
                </div>

                <div class="file-info">
                    <h3>📎 Attached File</h3>
                    <p><strong>File Name:</strong> <span class="file-name">{filename}</span></p>
                    <p><strong>Type:</strong> PDF Document</p>
                    <p><strong>Status:</strong> ✅ Successfully attached</p>
                    <p style="margin-top: 15px; color: #0066cc;"><strong>👉 Please download and open the attached PDF file to view the full report.</strong></p>
                </div>

                <div class="footer">
                    <p>This is an automated email. Please do not reply to this message.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html_body

    def _generate_html_body_with_image(self, body_text, pdf_filename):
        """Generate professional HTML email body with inline image"""
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; border-bottom: 3px solid #0066cc; padding-bottom: 20px; margin-bottom: 30px; }}
                .header h1 {{ color: #0066cc; margin: 0; font-size: 24px; }}
                .content {{ color: #333; line-height: 1.8; margin-bottom: 30px; }}
                .image-section {{ text-align: center; margin: 30px 0; }}
                .image-section img {{ max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
                .file-info {{ background-color: #e8f4f8; padding: 20px; border-left: 4px solid #0066cc; border-radius: 4px; margin: 20px 0; }}
                .file-info h3 {{ color: #0066cc; margin-top: 0; }}
                .file-info p {{ margin: 10px 0; color: #555; }}
                .file-name {{ font-weight: bold; color: #0066cc; word-break: break-all; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; border-top: 1px solid #ddd; padding-top: 20px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 RPA Daily Report</h1>
                </div>

                <div class="content">
                    <p>{body_text}</p>
                </div>

                <div class="image-section">
                    <img src="cid:report_image" alt="RPA Report Image" style="max-width: 100%; height: auto;">
                </div>

                <div class="file-info">
                    <h3>📎 Attached File</h3>
                    <p><strong>File Name:</strong> <span class="file-name">{pdf_filename}</span></p>
                    <p><strong>Type:</strong> PDF Document</p>
                    <p><strong>Status:</strong> ✅ Successfully attached</p>
                    <p style="margin-top: 15px; color: #0066cc;"><strong>👉 Please download and open the attached PDF file for detailed information.</strong></p>
                </div>

                <div class="footer">
                    <p>This is an automated email. Please do not reply to this message.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html_body

    def send_email_with_attachment(self, recipients, subject, body, file_path):
        msg = MIMEMultipart('alternative')
        msg['From'] = self.sender_email
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject

        # Plain text version for fallback
        msg.attach(MIMEText(body, 'plain'))

        # HTML version (primary)
        if file_path and os.path.exists(file_path):
            filename = os.path.basename(file_path)
            html_body = self._generate_html_body(body, filename)
            msg.attach(MIMEText(html_body, 'html'))

        # Attach PDF file
        if file_path and os.path.exists(file_path):
            filename = os.path.basename(file_path)
            attachment = open(file_path, "rb")

            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)

            # RFC 2231 형식으로 파일명 인코딩 (특수문자 및 한글 포함)
            encoded_filename = Header(filename, 'utf-8').encode()
            part.add_header('Content-Disposition', 'attachment', filename=encoded_filename)

            msg.attach(part)
            attachment.close()

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, recipients, msg.as_string())
            server.quit()
            return True, "Email sent successfully"
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"

    def send_email_with_image_and_pdf(self, recipients, subject, body, pdf_path, png_path):
        """PNG는 본문에 inline embed, PDF는 첨부하는 방식"""
        msg = MIMEMultipart('related')
        msg['From'] = self.sender_email
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject

        # HTML 본문 생성 (PNG는 cid:report_image로 참조)
        if pdf_path and os.path.exists(pdf_path):
            pdf_filename = os.path.basename(pdf_path)
        else:
            pdf_filename = "Report"

        html_body = self._generate_html_body_with_image(body, pdf_filename)
        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)

        # Plain text version for fallback
        msg_alternative.attach(MIMEText(body, 'plain'))

        # HTML version (primary)
        msg_alternative.attach(MIMEText(html_body, 'html'))

        # PNG 파일을 inline 이미지로 embed
        if png_path and os.path.exists(png_path):
            with open(png_path, 'rb') as img:
                image_data = img.read()

            image_part = MIMEImage(image_data)
            image_part.add_header('Content-ID', '<report_image>')
            image_part.add_header('Content-Disposition', 'inline', filename=os.path.basename(png_path))
            msg.attach(image_part)

        # PDF 파일을 첨부
        if pdf_path and os.path.exists(pdf_path):
            pdf_filename = os.path.basename(pdf_path)
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()

            pdf_part = MIMEBase('application', 'octet-stream')
            pdf_part.set_payload(pdf_data)
            encoders.encode_base64(pdf_part)

            # RFC 2231 형식으로 파일명 인코딩 (특수문자 및 한글 포함)
            encoded_filename = Header(pdf_filename, 'utf-8').encode()
            pdf_part.add_header('Content-Disposition', 'attachment', filename=encoded_filename)

            msg.attach(pdf_part)

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, recipients, msg.as_string())
            server.quit()
            return True, "Email sent successfully"
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"
