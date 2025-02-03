from django.views.generic import TemplateView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login, logout
from .serializers import UserRegistrationSerializer, UserLoginSerializer, MessageSerializer
from .models import CustomUser, Chat, Message
from django.shortcuts import redirect


class UserRegistrationView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        Chat.objects.create(user=user)  # Создание чата для нового пользователя


class UserLoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


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
