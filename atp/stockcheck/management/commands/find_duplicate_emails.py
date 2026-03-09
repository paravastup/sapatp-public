# /var/www/atp/atp/stockcheck/management/commands/find_duplicate_emails.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Count  # Import the Count function

class Command(BaseCommand):
    help = 'Finds duplicate email addresses in the user model'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        duplicates = User.objects.values('email').annotate(email_count=Count('email')).filter(email_count__gt=1)

        if duplicates:
            self.stdout.write("Duplicate emails found:")
            for duplicate in duplicates:
                self.stdout.write(f"{duplicate['email']}: {duplicate['email_count']}")
        else:
            self.stdout.write("No duplicate emails found.")
