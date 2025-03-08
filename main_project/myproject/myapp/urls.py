from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.contrib.auth import views as auth_views
from .views import (
    ChatView,
    logout_view,
    MessageViewSet,
    GoogleLoginView,
    auth_success_view,
    ChatViewSet,
    LogoutView,
    UserRegistrationView,
    UserLoginView,
)

# Создаем router для ViewSet'ов
router = DefaultRouter()
router.register(r'chats', ChatViewSet, basename='chat')
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [
    path('', ChatView.as_view(), name='chat_view'),
    path('chat/', ChatView.as_view(), name='chat_view'),
    path('logout/', logout_view, name='logout'),
    
    # Стандартная аутентификация
    path('login/', UserLoginView.as_view(), name='account_login'),
    path('signup/', UserRegistrationView.as_view(), name='account_signup'),
    
    # Google OAuth
    path('accounts/', include('allauth.urls')),
    path('auth-success/', auth_success_view, name='auth_success'),
    path('google/login/', GoogleLoginView.as_view(), name='google_login'),
    
    # Чаты и сообщения
    path('chat/create/', ChatViewSet.as_view({'post': 'create'}), name='chat_create'),
    path('chat/<int:pk>/delete/', ChatViewSet.as_view({'post': 'delete'}), name='chat_delete'),
    path('chat/<int:pk>/rename/', ChatViewSet.as_view({'post': 'rename'}), name='chat_rename'),
    path('chat/<int:pk>/messages/', ChatView.as_view(), name='chat_messages'),
    path('messages/', MessageViewSet.as_view({'post': 'create', 'get': 'list'}), name='message_create'),
    
    # API endpoints
    path('api/', include(router.urls)),
]
