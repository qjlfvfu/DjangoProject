from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_welcome_email(user):
    """Отправка приветственного письма"""
    subject = 'Добро пожаловать в Skystore!'
    html_message = render_to_string('users/email/welcome.html', {
        'user': user,
        'site_name': 'Skystore'
    })
    plain_message = strip_tags(html_message)

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_password_reset_email(user, reset_url):
    """Отправка письма для сброса пароля"""
    subject = 'Сброс пароля в Skystore'
    html_message = render_to_string('users/email/password_reset.html', {
        'user': user,
        'reset_url': reset_url,
        'site_name': 'Skystore'
    })
    plain_message = strip_tags(html_message)

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )