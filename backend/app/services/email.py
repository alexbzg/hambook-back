from typing import List
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr, BaseModel

from app.core.config import EMAIL_USER, EMAIL_PASSWORD, EMAIL_FROM, EMAIL_PORT, EMAIL_HOST
from app.services import html_templates_service


class EmailSchema(BaseModel):
    email: List[EmailStr]

class EmailService:

    async def send(
		self, 
		*,
        recipients: List[EmailStr], 
        subject: str, 
        template: str,
        template_params: dict):
        # Define the config
        conf = ConnectionConfig(
            MAIL_USERNAME=EMAIL_USER,
            MAIL_PASSWORD=EMAIL_PASSWORD,
            MAIL_FROM=EMAIL_FROM,
            MAIL_PORT=EMAIL_PORT,
            MAIL_SERVER=EMAIL_HOST,
            MAIL_STARTTLS=False,
            MAIL_SSL_TLS=True,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
        # Generate the HTML template base on the template name
        template = html_templates_service.template(template)

        html = template.render(**template_params)

        # Define the message options
        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            body=html,
            subtype="html"
        )

        # Send the email
        fm = FastMail(conf)
        await fm.send_message(message)


