from django.contrib import admin
from .models import CustomUser, Chat, Message

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Chat)
admin.site.register(Message)
