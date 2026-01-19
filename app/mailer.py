
import os
import smtplib
from email.mime.text import MIMEText

def send_email(to_email:str, subject:str, html_body:str)->bool:
    host = os.getenv('SMTP_HOST')
    user = os.getenv('SMTP_USER')
    pwd = os.getenv('SMTP_PASS')
    port = int(os.getenv('SMTP_PORT','587'))
    fromaddr = os.getenv('SMTP_FROM','EduDAP Office <no-reply@example.com>')
    if not host or not user or not pwd:
        return False
    msg = MIMEText(html_body, 'html')
    msg['Subject'] = subject
    msg['From'] = fromaddr
    msg['To'] = to_email
    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, pwd)
        server.sendmail(fromaddr, [to_email], msg.as_string())
    return True
