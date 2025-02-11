from django.urls import path, include
from .views import UserRegistrationView, UserLoginView, ChatView, logout_view, MessageCreateView, register, activate_account, activation_success_view

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('chat/', ChatView.as_view(), name='chat_view'),
    path('logout/', logout_view, name='logout'),
    path('messages/', MessageCreateView.as_view(), name='message_create'),
    path('activate/<uidb64>/<token>/', activate_account, name='activate'),
    path('activation/success/', activation_success_view, name='activation_success'),
]
