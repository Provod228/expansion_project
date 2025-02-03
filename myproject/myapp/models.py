from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
import re


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    def clean(self):
        super().clean()
        # Проверка на рабочую почту
        if not self.is_valid_email(self.email):
            raise ValidationError("Email is not valid.")

    @staticmethod
    def is_valid_email(email):
        # Пример простой проверки на рабочую почту
        # Здесь можно добавить более сложную логику проверки
        return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

    def __str__(self):
        return self.username


class Chat(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat for {self.user.username}"


class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    user_message = models.TextField()
    ai_response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.chat.user.username} at {self.created_at}"
