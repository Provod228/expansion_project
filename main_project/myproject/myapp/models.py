from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
import re
from django.contrib.sessions.models import Session
from django.utils import timezone


class ApiKey(models.Model):
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=255)
    base_url = models.URLField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.is_active})"


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    def clean(self):
        super().clean()
        if not self.is_valid_email(self.email):
            raise ValidationError("Email is not valid.")

    @staticmethod
    def is_valid_email(email):
        return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

    def __str__(self):
        return self.username

    def clear_sessions(self):
        """Очищает все сессии пользователя"""
        Session.objects.filter(
            expire_date__gte=timezone.now(),
            session_data__contains=str(self.id)
        ).delete()

    def logout_all_sessions(self):
        """Выход из всех сессий пользователя"""
        self.clear_sessions()
        return True


class Chat(models.Model):
    user = models.ForeignKey(CustomUser, related_name='chats', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default="Новый чат")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.user.username}"

    class Meta:
        ordering = ['-created_at']


class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    user_message = models.TextField()
    ai_response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    api_key_used = models.ForeignKey(ApiKey, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Message in {self.chat.name} at {self.created_at}"

    class Meta:
        ordering = ['created_at']

