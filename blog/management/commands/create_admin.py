from django.core.management.base import BaseCommand
from blog.models import Admin


class Command(BaseCommand):
    help = 'Create an admin user for the blog'

    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, help='Admin name')
        parser.add_argument('--email', type=str, help='Admin email', required=True)
        parser.add_argument('--password', type=str, help='Admin password', required=True)

    def handle(self, *args, **options):
        name = options.get('name', 'Administrator')
        email = options['email']
        password = options['password']

        # Check if admin already exists
        if Admin.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.ERROR(f'Admin with email {email} already exists!')
            )
            return

        # Create admin
        admin = Admin(name=name, email=email)
        admin.set_password(password)
        admin.save()

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created admin: {name} ({email})')
        )