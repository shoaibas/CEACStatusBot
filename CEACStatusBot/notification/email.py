import os
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

from .handle import NotificationHandle

class EmailNotificationHandle(NotificationHandle):
    def __init__(self, fromEmail: str, toEmail: str, apiKey: str = None, domain: str = None) -> None:
        super().__init__()
        self.__fromEmail = fromEmail
        self.__toEmail = toEmail.split("|")
        # API key comes from parameter or environment variable
        self.__apiKey = apiKey or os.getenv("API")
        # Mailgun domain (e.g., sandbox123.mailgun.org)
        self.__domain = domain or fromEmail.split("@")[1]

    def send(self, result):
        # Mail subject and body
        mail_title = '[CEACStatusBot] {} : {}'.format(result["application_num_origin"], result['status'])
        mail_content = str(result)

        msg = MIMEMultipart()
        msg["Subject"] = Header(mail_title, 'utf-8')
        msg["From"] = self.__fromEmail
        msg['To'] = ";".join(self.__toEmail)
        msg.attach(MIMEText(mail_content, 'plain', 'utf-8'))

        # Send via Mailgun API
        url = f"https://api.mailgun.net/v3/{self.__domain}/messages"
        data = {
            "from": self.__fromEmail,
            "to": self.__toEmail,
            "subject": mail_title,
            "text": mail_content
        }

        response = requests.post(url, auth=("api", self.__apiKey), data=data)
        if response.status_code != 200:
            print(f"Mailgun send failed: {response.status_code} - {response.text}")
        else:
            print("Mail sent successfully via Mailgun.")
