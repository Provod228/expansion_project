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

    def dispatch(self, request, *args, **kwargs):
        # Проверка, вошел ли пользователь в систему
        if not request.user.is_authenticated:
            return redirect('login')  # Перенаправление на страницу входа
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chat = Chat.objects.filter(user=self.request.user).first()  # Получаем чат для текущего пользователя
        context['chat'] = chat  # Передаем чат в контекст
        context['messages'] = Message.objects.filter(chat=chat)  # Получаем сообщения для чата
        return context


def logout_view(request):
    logout(request)
    return redirect('chat_view')  # Перенаправление на страницу чата после выхода


class MessageCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        print(request.data)  # Выводим данные запроса в консоль
        user_message = request.data.get('user_message')
        chat_id = request.data.get('chat_id')

        if not user_message or not chat_id:
            return Response({'error': 'user_message and chat_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Имитация ответа ИИ
        ai_response = self.get_ai_response(user_message)

        # Сохранение сообщения в базе данных
        message = Message.objects.create(
            chat_id=chat_id,
            user_message=user_message,
            ai_response=ai_response
        )

        return Response({
            'user_message': user_message,
            'ai_response': ai_response,
            'message_id': message.id
        }, status=201)

    def get_ai_response(self, user_message):
        return f"AI response to: {user_message}"  # Пример ответа
