from itertools import count
from sys import is_stack_trampoline_active
from celery import shared_task
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

from rest_framework import settings

User = get_user_model()
logger = logging.getLogger(__name__)



@shared_task
def block_inactive_user():
    """
    Блокирует пользователей, которые не заходили более месяца
    """
    month_time=timezone.now-timezone.timedelta(days=30)
    inactive_users = User.objects.filter(
        is_active=True,
        last_login__lt=month_time
    )
    count= inactive_users.count()
    updated_count= inactive_users.update(is_active=False)
    logger.info(f'Заблокировано {updated_count} неактивных пользователей')

    return {
        'total_found': count,
        'blocked': updated_count,
        'date_threshold': month_time.isoformat()
    }


@shared_task
def send_course_update_notification(course_id, course_name, user_email, user_name):
    """
    Отправка уведомления пользователю об обновлении курса
    """
    try:
        subject = f'Курс "{course_name}" был обновлен!'
        message = f'''
        Здравствуйте, {user_name}!

        Курс "{course_name}", на который вы подписаны, был обновлен.

        Зайдите на платформу, чтобы ознакомиться с новыми материалами.

        С уважением,
        Команда платформы
        '''

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )

        logger.info(f'Уведомление отправлено пользователю {user_email} о курсе {course_name}')
        return True

    except Exception as e:
        logger.error(f'Ошибка отправки уведомления {user_email}: {e}')
        return False


@shared_task
def notify_course_subscribers(course_id, course_name, updated_fields=None):
    """
    Отправка уведомлений всем подписчикам курса
    """
    from lesson.models import Subscription

    subscribers = Subscription.objects.filter(course_id=course_id).select_related('user')

    if not subscribers.exists():
        logger.info(f'Нет подписчиков для курса {course_name}')
        return {'status': 'no_subscribers', 'count': 0}

    sent_count = 0
    for subscription in subscribers:
        user = subscription.user
        send_course_update_notification.delay(
            course_id=course_id,
            course_name=course_name,
            user_email=user.email,
            user_name=user.name if hasattr(user, 'name') else user.email
        )
        sent_count += 1

    logger.info(f'Отправлено {sent_count} уведомлений для курса {course_name}')
    return {'status': 'sent', 'count': sent_count}