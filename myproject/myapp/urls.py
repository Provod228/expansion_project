from django.urls import path
from .views import UserRegistrationView, UserLoginView, ChatView, logout_view, MessageCreateView

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('chat/', ChatView.as_view(), name='chat_view'),
    path('logout/', logout_view, name='logout'),
    path('messages/', MessageCreateView.as_view(), name='message_create'),
]
