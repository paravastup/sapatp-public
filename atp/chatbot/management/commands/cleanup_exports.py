"""
Management command to clean up old export files
Run daily via cron to delete exports older than 7 days

Usage:
    python manage.py cleanup_exports
    python manage.py cleanup_exports --days 14  # Custom retention period
    python manage.py cleanup_exports --dry-run  # Preview what would be deleted
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import os
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up export files older than specified days (default: 7 days)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to retain exports (default: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        from chatbot.models import EmailAuditLog, ExportNotification

        retention_days = options['days']
        dry_run = options['dry_run']
        cutoff_date = timezone.now() - timedelta(days=retention_days)

        self.stdout.write(
            self.style.SUCCESS(
                f'\n{"[DRY RUN] " if dry_run else ""}Export Cleanup Starting...'
            )
        )
        self.stdout.write(f'Retention period: {retention_days} days')
        self.stdout.write(f'Cutoff date: {cutoff_date.strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write('-' * 70)

        # Find old exports
        old_exports = EmailAuditLog.objects.filter(
            sent_at__lt=cutoff_date,
            status='success'
        )

        total_count = old_exports.count()
        deleted_files = 0
        deleted_notifications = 0
        deleted_records = 0
        errors = 0

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('\nNo old exports found to clean up.'))
            return

        self.stdout.write(f'\nFound {total_count} exports to clean up:')

        for export in old_exports:
            try:
                # Show what we're processing
                age_days = (timezone.now() - export.sent_at).days
                self.stdout.write(
                    f'\n  • Export ID {export.id}: {export.csv_filename}'
                )
                self.stdout.write(f'    User: {export.user.username}')
                self.stdout.write(f'    Sent: {export.sent_at.strftime("%Y-%m-%d %H:%M")} ({age_days} days ago)')
                self.stdout.write(f'    Products: {export.product_count}')

                if not dry_run:
                    # Delete associated notifications
                    notif_count = ExportNotification.objects.filter(export_log=export).count()
                    if notif_count > 0:
                        ExportNotification.objects.filter(export_log=export).delete()
                        deleted_notifications += notif_count
                        self.stdout.write(f'    ✓ Deleted {notif_count} notification(s)')

                    # Delete file from disk
                    if export.csv_file:
                        file_path = export.csv_file.path
                        if os.path.exists(file_path):
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            deleted_files += 1
                            self.stdout.write(
                                f'    ✓ Deleted file ({file_size / 1024:.1f} KB)'
                            )
                        else:
                            self.stdout.write('    ⚠ File already missing from disk')

                    # Delete database record
                    export.delete()
                    deleted_records += 1
                    self.stdout.write('    ✓ Deleted database record')
                else:
                    self.stdout.write('    [Would delete in real run]')

            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f'    ✗ Error: {str(e)}')
                )
                logger.error(f'Error cleaning up export {export.id}: {e}', exc_info=True)

        # Summary
        self.stdout.write('\n' + '=' * 70)
        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] - No changes made'))
            self.stdout.write(f'\nWould delete:')
            self.stdout.write(f'  • {total_count} export records')
            self.stdout.write(f'  • {total_count} files from disk')
            self.stdout.write(f'  • Associated notifications')
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ Cleanup Complete!'))
            self.stdout.write(f'\nDeleted:')
            self.stdout.write(f'  • {deleted_records} export records')
            self.stdout.write(f'  • {deleted_files} files from disk')
            self.stdout.write(f'  • {deleted_notifications} notifications')

        if errors > 0:
            self.stdout.write(self.style.ERROR(f'\n⚠ {errors} errors occurred'))

        self.stdout.write('\n' + '=' * 70 + '\n')

        # Log to Django logger
        if not dry_run:
            logger.info(
                f'[CLEANUP] Deleted {deleted_records} exports older than {retention_days} days. '
                f'Files: {deleted_files}, Notifications: {deleted_notifications}, Errors: {errors}'
            )
