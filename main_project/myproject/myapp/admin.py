from django.contrib import admin
from .models import CustomUser, Chat, Message, ApiKey

@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'key')

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active')
    search_fields = ('username', 'email')

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'user__username')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('chat', 'created_at', 'api_key_used')
    list_filter = ('chat__user', 'created_at')
    search_fields = ('user_message', 'ai_response')
