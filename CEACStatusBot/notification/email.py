from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import requests

from .handle import NotificationHandle

class EmailNotificationHandle(NotificationHandle):
    def __init__(self, fromEmail: str, toEmail: str, emailPassword: str = '', hostAddress: str = '') -> None:
        super().__init__()
        self.__fromEmail = fromEmail
        self.__toEmail = toEmail.split("|")
        self.__emailPassword = emailPassword
        self.__hostAddress = hostAddress or "smtp." + fromEmail.split("@")[1]
        if ':' in self.__hostAddress:
            [addr, port] = self.__hostAddress.split(':')
            self.__hostAddress = addr
            self.__hostPort = int(port)
        else:
            self.__hostPort = 0
        # Hardcoded Mailgun API key
        self.__apiKey = "060e5aedcc85e7e3601a95120940ff0e-1c7f8751-0fe27147"

    def send(self, result):
        # Build email content as before
        mail_title = '[CEACStatusBot] {} : {}'.format(result["application_num_origin"], result['status'])
        mail_content = str(result)

        msg = MIMEMultipart()
        msg["Subject"] = Header(mail_title, 'utf-8')
        msg["From"] = self.__fromEmail
        msg['To'] = ";".join(self.__toEmail)
        msg.attach(MIMEText(mail_content, 'plain', 'utf-8'))

        # --- Mailgun send ---
        # The "from" address must be a verified sender in your Mailgun account
        response = requests.post(
            f"https://api.mailgun.net/v3/{self.__hostAddress}/messages",
            auth=("api", self.__apiKey),
            data={
                "from": self.__fromEmail,
                "to": self.__toEmail,
                "subject": mail_title,
                "text": mail_content
            }
        )

        if response.status_code != 200:
            print(f"Mailgun send failed: {response.status_code} - {response.text}")
        else:
            print(f"Mailgun email sent successfully to {self.__toEmail}")
