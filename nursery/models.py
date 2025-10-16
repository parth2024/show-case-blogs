from django.db import models
from django.utils import timezone

# Create your models here.
class ContactMessage(models.Model):
    """Model to store contact form submissions"""
    name = models.CharField(max_length=200, verbose_name="Nom")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Téléphone")
    message = models.TextField(verbose_name="Message")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Date de création")
    is_read = models.BooleanField(default=False, verbose_name="Lu")
    
    class Meta:
        verbose_name = "Message de contact"
        verbose_name_plural = "Messages de contact"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.email} ({self.created_at.strftime('%d/%m/%Y')})"
    
    def mark_as_read(self):
        """Mark the message as read"""
        self.is_read = True
        self.save()
