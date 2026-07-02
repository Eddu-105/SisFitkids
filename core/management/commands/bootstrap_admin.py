import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Create or update the initial professor/super admin from environment variables.'

    def handle(self, *args, **options):
        username = os.environ.get('ADMIN_USERNAME', 'profesor')
        password = os.environ.get('ADMIN_PASSWORD')
        email = os.environ.get('ADMIN_EMAIL', '')
        first_name = os.environ.get('ADMIN_FIRST_NAME', 'Profesor')
        last_name = os.environ.get('ADMIN_LAST_NAME', 'Principal')

        if not password:
            raise CommandError('ADMIN_PASSWORD is required to bootstrap the professor user.')

        User = get_user_model()
        user, created = User.objects.get_or_create(username=username)
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.role = User.Role.TEACHER
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        action = 'created' if created else 'updated'
        self.stdout.write(self.style.SUCCESS(f'Professor user {action}: {username}'))
