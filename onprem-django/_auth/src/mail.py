from django.core.mail import EmailMessage, send_mail
from django.urls import reverse
from django.core.mail import EmailMessage
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes

from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string

class MailVerificate:
    def __init__(self, address, token, uidb64, payload) -> None:
        self.dst = address
        self.token = token
        self.uidb64 = uidb64
        self.payload = payload
        self.sender = 'test@test.io'
        self.title = '[TEST] Email Certified'
    
    def send(self):
        send_mail(
            self.title,
            self.payload,
            self.sender,
            [self.dst],
            fail_silently=False,
        )
        

def send_mail(request, user):
    mail_subject = '[Teiren] Verification mail'
    
    # 유저 정보에서 idb64 생성
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    confirmation_link = reverse('activate', args=[uidb64, token])
    message = render_to_string('registration/activation.html', {
        'user': user,
        'domain': 'https://app.teiren.io',
        'uid': uidb64,
        'token': token,
        'confirmation_link': confirmation_link,
    })
    mail_to = user.email
    email = EmailMessage(mail_subject, message, to=[mail_to])
    is_send_success = email.send()
    
    return True if is_send_success == 1 else False