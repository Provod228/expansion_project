from django.urls import path
from .views import UserRegistrationView, UserLoginView, ChatView, MessageCreateView, logout_view

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('chat/', ChatView.as_view(), name='chat_view'),
    path('messages/', MessageCreateView.as_view(), name='message_create'),
    path('logout/', logout_view, name='logout'),
]
