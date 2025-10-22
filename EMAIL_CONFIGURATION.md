# Email Configuration Guide - Contact Form

## Overview
The contact form on the nursery app is now fully functional and can send messages to the school mailbox (`contact@ambassadeurs.edu`).

## Features Implemented

### 1. Contact Form Email Functionality
- Users can fill out the contact form with their name, email, phone (optional), and message
- Form submissions are sent to `contact@ambassadeurs.edu`
- Success and error messages are displayed to users
- All submissions are saved to the database as a backup

### 2. Database Storage
- All contact messages are stored in the `ContactMessage` model
- Messages can be viewed and managed through the Django admin panel
- Fields tracked: name, email, phone, message, creation date, read status

### 3. Admin Interface
- Access messages at: `/admin/nursery/contactmessage/`
- Features:
  - View all contact messages
  - Filter by read/unread status and date
  - Search by name, email, or message content
  - Mark messages as read/unread
  - Automatic date sorting (newest first)

## Current Configuration

### Development Mode (Currently Active)
The system is configured to use **Console Backend** for testing:

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**What this means:**
- Emails are printed to the console/terminal instead of being sent
- Perfect for testing without needing real SMTP credentials
- You can see the email content when you run the Django server

### Testing the Contact Form
1. Start your Django development server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to the contact page: `http://localhost:8000/nursery/contact/`

3. Fill out and submit the form

4. Check your terminal/console where Django is running - you'll see the email content printed there

5. Check the admin panel to verify the message was saved to the database

## Production Configuration

When you're ready to deploy to production, you'll need to configure a real SMTP server. Here are the most common options:

### Option 1: Gmail SMTP (Simple but limited)

**Steps:**
1. Enable 2-factor authentication on your Gmail account
2. Generate an "App Password" at https://myaccount.google.com/apppasswords
3. Update `daycare/settings.py`:

```python
# Comment out the console backend
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Enable SMTP backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-gmail@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password-here'  # 16-character app password
```

**Limitations:**
- Gmail limits: 500 emails/day for free accounts
- Not ideal for high-volume use

### Option 2: Professional Email Provider (Recommended)

If you have a professional email service (like cPanel, Office 365, etc.):

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.ambassadeurs.edu'  # Your mail server
EMAIL_PORT = 587  # or 465 for SSL
EMAIL_USE_TLS = True  # or EMAIL_USE_SSL = True for port 465
EMAIL_HOST_USER = 'noreply@ambassadeurs.edu'
EMAIL_HOST_PASSWORD = 'your-email-password'
```

**Get these settings from:**
- Your hosting provider's documentation
- cPanel → Email Accounts → Configure Email Client
- Your IT administrator

### Option 3: Third-Party Email Services (Most Reliable)

For best deliverability and scalability:

#### SendGrid
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = 'your-sendgrid-api-key'
```
- Free tier: 100 emails/day
- Website: https://sendgrid.com

#### Mailgun
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'postmaster@your-domain.mailgun.org'
EMAIL_HOST_PASSWORD = 'your-mailgun-password'
```
- Free tier: 5,000 emails/month
- Website: https://mailgun.com

#### Amazon SES (Advanced)
- Most cost-effective for high volume
- Requires AWS account setup
- $0.10 per 1,000 emails

## Security Best Practices

### 1. Use Environment Variables
Never hardcode passwords in `settings.py`. Use environment variables instead:

```python
import os

EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
```

Then create a `.env` file:
```
EMAIL_HOST_USER=noreply@ambassadeurs.edu
EMAIL_HOST_PASSWORD=your-secure-password
```

Install `python-decouple` or `django-environ` to load these:
```bash
pip install python-decouple
```

### 2. Protect Credentials
- Add `.env` to `.gitignore`
- Never commit passwords to version control
- Use different credentials for development and production

## Customization Options

### Change Recipient Email
Edit in `daycare/settings.py`:
```python
CONTACT_EMAIL = 'contact@ambassadeurs.edu'  # Change to any email
```

### Change Sender Email
```python
DEFAULT_FROM_EMAIL = 'noreply@ambassadeurs.edu'  # Change to any email
```

### Customize Email Content
Edit `nursery/views.py`, around line 31-44 to modify the email template.

### Add More Form Fields
1. Update the HTML form in `nursery/templates/nursery/contact.html`
2. Update the `ContactMessage` model in `nursery/models.py`
3. Update the view logic in `nursery/views.py`
4. Run migrations: `python manage.py makemigrations && python manage.py migrate`

## Troubleshooting

### Emails Not Sending
1. Check console for error messages
2. Verify SMTP credentials are correct
3. Ensure your email provider allows SMTP access
4. Check firewall settings (ports 587 or 465 must be open)
5. Verify email addresses are valid

### Gmail Specific Issues
- Enable "Less secure app access" (not recommended) OR use App Passwords
- Check if Gmail is blocking sign-in attempts
- Gmail may require additional verification

### Messages Not Appearing in Admin
- Verify migrations were applied: `python manage.py migrate`
- Check if user has admin permissions
- Ensure `nursery` app is in `INSTALLED_APPS`

## Testing Email Functionality

### Test with Console Backend (Current Setup)
```bash
python manage.py runserver
# Submit a form, check terminal output
```

### Test with Real SMTP
After configuring SMTP settings:
```bash
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail(
...     'Test Subject',
...     'Test message body',
...     'from@ambassadeurs.edu',
...     ['contact@ambassadeurs.edu'],
...     fail_silently=False,
... )
```

## Files Modified

1. **nursery/views.py** - Added email sending logic
2. **nursery/models.py** - Created ContactMessage model
3. **nursery/admin.py** - Added admin interface for messages
4. **nursery/templates/nursery/contact.html** - Added success/error message display
5. **daycare/settings.py** - Added email configuration settings

## Next Steps

1. **For Development:** Continue using console backend to test
2. **For Production:**
   - Choose an email provider
   - Configure SMTP settings
   - Use environment variables for credentials
   - Test thoroughly before going live
3. **Optional Enhancements:**
   - Add email confirmation to users (auto-reply)
   - Implement rate limiting to prevent spam
   - Add CAPTCHA to prevent bot submissions
   - Set up email notifications for new messages

## Support

If you need help configuring email for production, you'll need:
- Access to your domain's email settings
- SMTP server details from your hosting provider
- Or an account with a third-party email service

Contact your hosting provider or system administrator for SMTP credentials.
