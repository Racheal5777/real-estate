from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
import logging
from .models import Profile

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=User)
def create_profile_and_send_welcome(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        # send welcome email (requires email settings configured)
        subject = 'Welcome to Real Estate App'
        message = f'Hello {instance.username},\n\nThank you for registering at our Real Estate application.'
        # choose a sensible from_email fallback
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None) or 'webmaster@localhost'
        if instance.email:
            try:
                send_mail(subject, message, from_email, [instance.email], fail_silently=False)
            except Exception as exc:
                # log the exception so developers can diagnose email problems
                logger.exception('Failed to send welcome email to %s: %s', instance.email, exc)
            