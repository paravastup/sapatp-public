# yourapp/management/commands/resolve_duplicate_emails.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import models

class Command(BaseCommand):
    help = 'Resolves duplicate email addresses in the user model'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        duplicates = User.objects.values('email').annotate(email_count=models.Count('email')).filter(email_count__gt=1)

        for duplicate in duplicates:
            email = duplicate['email']
            users = User.objects.filter(email=email)
            primary_user = users.first()
            
            for user in users[1:]:
                self.merge_users(primary_user, user)

            self.stdout.write(f"Resolved duplicates for email: {email}")

    def merge_users(self, primary_user, duplicate_user):
        # Example merge logic: transfer relevant data to the primary_user and delete duplicate_user
        # This is just a placeholder, and you should adapt it to your specific needs

        # Transfer data from duplicate_user to primary_user if needed
        # For example, merge profiles, orders, etc.
        # Assuming you have a Profile model related to User
        # primary_user.profile.some_field += duplicate_user.profile.some_field

        # Delete the duplicate user
        duplicate_user.delete()
