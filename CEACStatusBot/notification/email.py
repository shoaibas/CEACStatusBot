import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from .handle import NotificationHandle

class EmailNotificationHandle(NotificationHandle):
    def __init__(self, fromEmail: str, toEmail: str, password: str, smtp: str = "smtp.office365.com", port: int = 587) -> None:
        super().__init__()
        self.__fromEmail = fromEmail
        self.__toEmail = toEmail.split("|")
        self.__password = password
        self.__smtp = smtp
        self.__port = port

    def send(self, result):
        # Mail subject and body
        mail_title = '[CEACStatusBot] {} : {}'.format(result["application_num_origin"], result['status'])
        mail_content = str(result)

        msg = MIMEMultipart()
        msg["Subject"] = Header(mail_title, 'utf-8')
        msg["From"] = self.__fromEmail
        msg['To'] = ";".join(self.__toEmail)
        msg.attach(MIMEText(mail_content, 'plain', 'utf-8'))

        try:
            # Connect to Outlook SMTP
            with smtplib.SMTP(self.__smtp, self.__port) as server:
                server.starttls()  # TLS is required
                server.login(self.__fromEmail, self.__password)
                server.sendmail(self.__fromEmail, self.__toEmail, msg.as_string())
            print("Mail sent successfully via Outlook SMTP.")
        except Exception as e:
            print(f"Outlook SMTP send failed: {e}")
