from django.views.generic import TemplateView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login, logout
from .serializers import UserRegistrationSerializer, UserLoginSerializer, MessageSerializer
from .models import CustomUser, Chat, Message
from django.shortcuts import redirect, render
from .forms import CustomAuthenticationForm, CustomUserCreationForm


class UserRegistrationView(TemplateView):
    template_name = 'register.html'  # Укажите ваш шаблон

    def get(self, request, *args, **kwargs):
        form = CustomUserCreationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = CustomUserCreationForm(data=request.POST)
        if form.is_valid():
            user = form.save()
            # Создание чата для нового пользователя
            Chat.objects.create(user=user)
            return redirect('login')  # Перенаправление на страницу входа
        return render(request, self.template_name, {'form': form})


class UserLoginView(TemplateView):
    template_name = 'login.html'  # Укажите ваш шаблон

    def get(self, request, *args, **kwargs):
        form = CustomAuthenticationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('chat_view')  # Перенаправление на страницу чата
            else:
                return render(request, self.template_name, {'form': form, 'error': 'Неверные учетные данные'})
        return render(request, self.template_name, {'form': form})


class ChatView(TemplateView):
    template_name = 'chat.html'  # Укажите ваш шаблон

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages'] = Message.objects.all()  # Получаем все сообщения
        return context


class MessageCreateView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]  # Только авторизованные пользователи могут отправлять сообщения

    def perform_create(self, serializer):
        user_message = serializer.validated_data['user_message']
        ai_response = self.get_ai_response(user_message)
        serializer.save(chat=self.request.user.chat, ai_response=ai_response)

    def get_ai_response(self, user_message):
        return f"AI response to: {user_message}"  # Пример ответа


def logout_view(request):
    logout(request)
    return redirect('chat_view')  # Перенаправление на страницу чата после выхода
