import os, datetime, logging
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db.models import signals
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.core.mail import send_mail, BadHeaderError, EmailMessage, EmailMultiAlternatives
from django.contrib.auth.models import AbstractUser, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.utils.translation import gettext_lazy as _


from django.contrib.auth.models import BaseUserManager


           
class SearchHistory(models.Model):
    username = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    time = models.DateField(auto_now_add=True)
    referencekey = models.CharField(max_length=5000)

    def __unicode__(self):
        return '{0} - {1} - {2}'.format(self.username, self.time, self.referencekey)

    def __str__(self):
        return '{0} - {1} - {2}'.format(self.username, self.time, self.referencekey)

class HelpGuide(models.Model):
    username = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    time = models.DateField(auto_now_add=True)
    title = models.CharField(max_length=150)
    description = models.CharField(max_length=150)

    def __unicode__(self):
        return '{0} - {1} - {2}'.format(self.username, self.time, self.referencekey)

    def __str__(self):
        return '{0} - {1} - {2}'.format(self.username, self.time, self.referencekey)

class Plant(models.Model):
    users = models.ManyToManyField(User,related_name='plant')
    code = models.CharField(
        max_length=15,
        help_text="Plant Code, for example: 1000"
        )
    description = models.CharField(
        max_length = 30,
        help_text="Plant Code description, for example: ACME Glass Plant"
        )

    def __str__(self):
        return u'{0}'.format(self.description)

class Pattern(models.Model):
    code = models.CharField(max_length=15)
    description = models.CharField(max_length = 30)

    def __str__(self):
        return self.description

class Universe(models.Model):
    code = models.CharField(max_length=15)
    description = models.CharField(max_length = 30)

    def __str__(self):
        return self.description

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    company = models.CharField(max_length=30, blank=True, null=True)
    role = models.CharField(max_length=30, blank=True, null=True)
    website = models.URLField(max_length=50, blank=True, null=True)
    business = models.CharField(max_length=10, blank=True,null=True)

@receiver(post_save, sender=User, dispatch_uid="update_user_profile")
def update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()


class AuditEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=100, blank=True, null=False)
    host = models.CharField(max_length=100, blank=True, null=False)
    login_time = models.DateTimeField(blank=True, null=True)
    logout_time = models.DateTimeField(blank=True, null=True)
    ip = models.GenericIPAddressField(null=True)
    def __unicode__(self):
        return '{0} - {1} - {2}'.format(self.user, self.login_time, self.logout_time, self.ip)

    def __str__(self):
        return '{0} - {1} - {2}'.format(self.user, self.login_time, self.logout_time, self.ip)


@receiver(user_logged_in)
def log_user_logged_in(sender, user, request, **kwargs):
    session_key = request.session.session_key
    audit_entry = AuditEntry.objects.create(login_time=datetime.datetime.now(), session_key=session_key, user=user, host=request.META['HTTP_HOST'], ip=request.META['REMOTE_ADDR'])
    request.session['audit_entry_id'] = audit_entry.id

@receiver(user_logged_out)
def log_user_logged_out(sender, user, request, **kwargs):
    audit_entry_id = request.session.get('audit_entry_id')
    if audit_entry_id is not None:
        AuditEntry.objects.filter(id=audit_entry_id).update(logout_time=datetime.datetime.now())

"""

@receiver(user_logged_in)
def log_user_logged_in(sender, user, request, **kwargs):
    audit_entries = AuditEntry.objects.filter(session_key=request.session.session_key, user=user.id)[:1]
    if not audit_entries:
        audit_entry = AuditEntry(login_time=datetime.datetime.now(),session_key=request.session.session_key, user=user, host=request.META['HTTP_HOST'], ip=request.META['REMOTE_ADDR'])
        audit_entry.save()


@receiver(user_logged_out)
def log_user_logged_out(sender, user, request, **kwargs):
    audit_entries = AuditEntry.objects.filter(session_key=request.session.session_key, user=user.id, host=request.META['HTTP_HOST'], ip=request.META['REMOTE_ADDR'])
    audit_entries.filter(logout_time__isnull=True).update(logout_time=datetime.datetime.now())
    if not audit_entries:
        audit_entry = AuditEntry(logout_time=datetime.datetime.now(), session_key=request.session.session_key, user=user, host=request.META['HTTP_HOST'])
        audit_entry.save()

-

@receiver(user_logged_out)
def log_user_logged_out(sender, user, request, **kwargs):
    audit_entries = AuditEntry.objects.filter(session_key=request.session.session_key, user=user.id, host=request.META['HTTP_HOST'], ip=request.META['REMOTE_ADDR'])
    audit_entries.filter(logout_time__isnull=True).update(logout_time=datetime.datetime.now())

"""

@receiver(pre_save,sender=User,dispatch_uid='active')
def active(sender,instance,**kwargs):
    
    if instance.is_active and get_user_model().objects.filter(pk=instance.pk, is_active=False).exists():
        subject = "Account activation confirmation for  - " + instance.username
        html_content = f'<p> This email is to confirm that your account on https://localhost is now active</p> <br></hr> <p> Your user account {instance.username} is now activated'
        text_content = ''
        from_email = settings.EMAIL_HOST_USER
        to_email = [instance.email]
        message = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        message.attach_alternative(html_content, "text/html")
        message.send()
