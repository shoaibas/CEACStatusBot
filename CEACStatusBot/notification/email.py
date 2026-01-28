import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from .handle import NotificationHandle

class EmailNotificationHandle(NotificationHandle):
    def __init__(self, fromEmail: str, toEmail: str, password: str) -> None:
        super().__init__()
        self.__fromEmail = fromEmail
        self.__toEmail = toEmail.split("|")
        self.__password = password
        self.__smtp_server = "smtp.gmail.com"
        self.__smtp_port = 465  # SSL port

    def send(self, result):
        mail_title = '[CEACStatusBot] {} : {}'.format(result["application_num_origin"], result['status'])
        mail_content = str(result)

        msg = MIMEMultipart()
        msg["Subject"] = Header(mail_title, 'utf-8')
        msg["From"] = self.__fromEmail
        msg["To"] = ";".join(self.__toEmail)
        msg.attach(MIMEText(mail_content, 'plain', 'utf-8'))

        try:
            with smtplib.SMTP_SSL(self.__smtp_server, self.__smtp_port) as smtp:
                smtp.login(self.__fromEmail, self.__password)
                smtp.sendmail(self.__fromEmail, self.__toEmail, msg.as_string())
            print("Mail sent successfully via Gmail SMTP.")
        except Exception as e:
            print(f"Gmail SMTP send failed: {e}")
