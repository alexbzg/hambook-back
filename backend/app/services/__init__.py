from app.services.authentication import AuthService
from app.services.html_templates import HTMLTemplatesService
from app.services.qrz_client import QrzClient

auth_service = AuthService()
html_templates_service = HTMLTemplatesService()
qrz_client_service = QrzClient()

from app.services.email import EmailService
email_service = EmailService()

from app.services.callsigns_autocomplete import CallsignsTrie
callsigns_autocomplete_service = CallsignsTrie()

