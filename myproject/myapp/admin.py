from django.contrib import admin
from .models import CustomUser, Chat, Message

# Регистрация ваших моделей
admin.site.register(CustomUser)
admin.site.register(Chat)
admin.site.register(Message)
