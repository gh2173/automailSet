import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
import os
from email.header import Header
import fitz  # PyMuPDF for PDF to image conversion
import tempfile

class EmailManager:
    def __init__(self, smtp_server, smtp_port, sender_email, sender_password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password

    def send_email_with_attachment(self, recipients, subject, body, file_path):
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

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

    def _convert_pdf_to_images(self, pdf_path, dpi=150):
        """
        Convert all PDF pages to PNG images.

        Args:
            pdf_path: Path to the PDF file
            dpi: DPI for image conversion (default 150)

        Returns:
            list: List of temporary image file paths

        Raises:
            Exception: If PDF cannot be opened or converted
        """
        temp_image_paths = []

        try:
            pdf_document = fitz.open(pdf_path)
            page_count = pdf_document.page_count

            for page_num in range(page_count):
                page = pdf_document[page_num]

                # Calculate zoom factor for desired DPI
                # Default PDF DPI is 72, so zoom = desired_dpi / 72
                zoom = dpi / 72.0
                matrix = fitz.Matrix(zoom, zoom)

                # Render page to pixmap
                pix = page.get_pixmap(matrix=matrix)

                # Create temporary file with descriptive name
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=f'_page_{page_num+1}.png',
                    dir=os.getcwd(),
                    prefix='pdf_preview_'
                )

                # Save image
                pix.save(temp_file.name)
                temp_image_paths.append(temp_file.name)
                temp_file.close()

                # Free memory
                pix = None

            pdf_document.close()
            return temp_image_paths

        except Exception as e:
            # Clean up any created files on error
            for path in temp_image_paths:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass
            raise Exception(f"PDF conversion failed: {str(e)}")

    def _generate_html_body(self, intro_text, page_count):
        """
        Generate HTML email body with embedded image references.

        Args:
            intro_text: Introduction text at top of email
            page_count: Number of PDF pages

        Returns:
            str: HTML email body
        """
        html_parts = [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '<style>',
            'body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }',
            '.container { max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }',
            '.header { margin-bottom: 20px; color: #333; }',
            '.header p { margin: 10px 0; line-height: 1.6; }',
            '.pdf-table { width: 100%; border-collapse: collapse; margin: 20px 0; }',
            '.pdf-table td { padding: 15px; text-align: center; border: 1px solid #ddd; background-color: #fafafa; }',
            '.pdf-table img { max-width: 100%; height: auto; display: block; margin: 0 auto; border: 1px solid #ccc; border-radius: 4px; }',
            '.page-label { font-size: 14px; font-weight: bold; color: #666; margin-bottom: 10px; }',
            '</style>',
            '</head>',
            '<body>',
            '<div class="container">',
            '<div class="header">',
            f'<p>{intro_text}</p>',
            '<p>The PDF pages are displayed below for quick preview:</p>',
            '</div>',
            '<table class="pdf-table">',
        ]

        # Add row for each page
        for page_num in range(1, page_count + 1):
            html_parts.extend([
                '<tr>',
                '<td>',
                f'<div class="page-label">Page {page_num}</div>',
                f'<img src="cid:page_{page_num}" alt="Page {page_num}">',
                '</td>',
                '</tr>',
            ])

        html_parts.extend([
            '</table>',
            '</div>',
            '</body>',
            '</html>',
        ])

        return '\n'.join(html_parts)

    def send_email_with_pdf_preview(self, recipients, subject, body, pdf_path, dpi=150):
        """
        Send email with PDF attachment and inline page preview images.

        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            body: Plain text body (used as intro text in HTML)
            pdf_path: Path to PDF file
            dpi: DPI for image conversion (default 150)

        Returns:
            tuple: (success: bool, message: str)
        """
        temp_image_paths = []

        try:
            # Step 1: Convert PDF to images
            temp_image_paths = self._convert_pdf_to_images(pdf_path, dpi)
            page_count = len(temp_image_paths)

            # Step 2: Create MIME message structure for inline images
            msg = MIMEMultipart('related')
            msg['From'] = self.sender_email
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = subject

            # Step 3: Generate and attach HTML body
            html_body = self._generate_html_body(body, page_count)
            msg.attach(MIMEText(html_body, 'html'))

            # Step 4: Attach inline images
            for i, image_path in enumerate(temp_image_paths):
                with open(image_path, 'rb') as img_file:
                    img_data = img_file.read()
                    img = MIMEImage(img_data, _subtype='png')
                    img.add_header('Content-ID', f'<page_{i+1}>')
                    img.add_header('Content-Disposition', 'inline',
                                 filename=f'page_{i+1}.png')
                    msg.attach(img)

            # Step 5: Attach original PDF as traditional attachment
            if pdf_path and os.path.exists(pdf_path):
                filename = os.path.basename(pdf_path)
                with open(pdf_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)

                    # RFC 2231 encoding for UTF-8 filenames
                    encoded_filename = Header(filename, 'utf-8').encode()
                    part.add_header('Content-Disposition', 'attachment',
                                  filename=encoded_filename)
                    msg.attach(part)

            # Step 6: Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, recipients, msg.as_string())
            server.quit()

            return True, f"Email sent successfully with {page_count} page preview(s)"

        except FileNotFoundError:
            return False, "PDF file not found"

        except MemoryError:
            return False, "Insufficient memory to process PDF"

        except Exception as e:
            error_msg = str(e)
            # Check if error is related to PDF corruption
            if "corrupted" in error_msg.lower() or "invalid" in error_msg.lower():
                return False, "Invalid or corrupted PDF file"
            return False, f"Failed to send email: {error_msg}"

        finally:
            # Step 7: Cleanup temporary image files
            for path in temp_image_paths:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass  # Ignore cleanup errors
