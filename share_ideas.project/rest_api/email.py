from django.core.mail import EmailMessage
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text

from django.contrib.auth.tokens import PasswordResetTokenGenerator


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
                str(user.pk) + str(timestamp) + str(user.is_active)
        )


account_activation_token = AccountActivationTokenGenerator()

# -------- Sending email confirmation mail -------------------


def mail_confirmation(user_=None, request=None):
    current_site = get_current_site(request)
    message = render_to_string('email/email_confirmation.html', {
        'user': user_,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user_.pk)),
        'token': account_activation_token.make_token(user_),
    })
    mail_subject = 'Your Mail confirmation message'
    email = EmailMessage(mail_subject, message, to=[user_.email])
    email.send()
    return

