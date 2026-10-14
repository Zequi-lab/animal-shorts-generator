import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailNotifier:
    def __init__(self, config_file="email_config.json"):
        self.config_file = config_file
        self.sender_email = None
        self.app_password = None
        self.receiver_email = "ezekuiel.egp@gmail.com"
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.sender_email = config.get("sender_email")
                    self.app_password = config.get("app_password")
                    if config.get("receiver_email"):
                        self.receiver_email = config.get("receiver_email")
            except Exception as e:
                print(f"[EmailNotifier] Error reading config: {e}")
        else:
            print(f"[EmailNotifier] Alert: '{self.config_file}' not found. Emails will not be sent.")
            self.create_template()

    def create_template(self):
        """Creates a default template for the user to fill."""
        template = {
            "sender_email": "TU_CORREO_AQUI@gmail.com",
            "app_password": "TU_CONTRASEÑA_DE_APLICACION_AQUI",
            "receiver_email": self.receiver_email
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(template, f, indent=4)
            print(f"[EmailNotifier] Created {self.config_file} template. Fill it in to enable alerts.")
        except Exception as e:
            pass

    def send_alert(self, subject, message_body):
        """Sende an email alert if configuration is present."""
        if not self.sender_email or not self.app_password or "TU_CORREO" in self.sender_email:
            print("[EmailNotifier] Cannot send email. Missing or default credentials in config.")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.receiver_email
            msg['Subject'] = f"⚠️ Animal Shorts Generator - {subject}"

            msg.attach(MIMEText(message_body, 'plain', 'utf-8'))

            # Setup SMTP server for Gmail
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            
            # Login using the app password
            server.login(self.sender_email, self.app_password)
            server.send_message(msg)
            server.quit()
            
            print(f"[EmailNotifier] ✅ Alert email sent to {self.receiver_email}")
            return True
        except Exception as e:
            print(f"[EmailNotifier] ❌ Failed to send email: {e}")
            return False
