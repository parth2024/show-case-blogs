from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from blog.models import Admin
import os

class Command(BaseCommand):
    help = "Create or update a blog admin/editor account securely (password via env var)."

    def add_arguments(self, parser):
        parser.add_argument('--name', required=True, help='Full name of the admin/editor')
        parser.add_argument('--email', required=True, help='Unique email for the admin/editor')
        parser.add_argument('--role', choices=['admin', 'editor'], default='admin', help='Role for this account')
        parser.add_argument('--inactive', action='store_true', help='Create user as inactive')
        parser.add_argument('--update', action='store_true', help='Update an existing user if found')
        parser.add_argument('--password-env', default='BLOG_ADMIN_PASSWORD', help='Env var name holding the password')

    def handle(self, *args, **options):
        name = options['name'].strip()
        email = options['email'].strip()
        role = options['role']
        is_active = not options['inactive']
        env_var = options['password_env']
        update = options['update']

        raw_password = os.environ.get(env_var)
        if not raw_password:
            raise CommandError(f"Password not provided. Set the {env_var} environment variable before running this command.")

        try:
            if update:
                try:
                    admin = Admin.objects.get(email=email)
                    admin.name = name
                    admin.role = role
                    admin.is_active = is_active
                    admin.set_password(raw_password)
                    admin.save()
                    self.stdout.write(self.style.SUCCESS(f"Updated admin '{email}' successfully."))
                    return
                except Admin.DoesNotExist:
                    pass  # fall through to create

            # Create new admin
            admin = Admin(name=name, email=email, role=role, is_active=is_active)
            admin.set_password(raw_password)
            admin.save()
            self.stdout.write(self.style.SUCCESS(f"Created admin '{email}' successfully."))
        except Exception as e:
            raise CommandError(f"Error creating/updating admin: {e}")
