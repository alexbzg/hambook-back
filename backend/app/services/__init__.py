from app.services.authentication import AuthService
from app.services.html_templates import HTMLTemplatesService

auth_service = AuthService()
html_templates_service = HTMLTemplatesService()

from app.services.email import EmailService
email_service = EmailService()

from app.services.callsigns_autocomplete import CallsignsTrie
callsigns_autocomplete_service = CallsignsTrie()

