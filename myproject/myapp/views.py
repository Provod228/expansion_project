from django.views.generic import TemplateView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login, logout
from .serializers import UserRegistrationSerializer, UserLoginSerializer, MessageSerializer
from .models import CustomUser, Chat, Message
from django.shortcuts import redirect, render
from .forms import CustomAuthenticationForm, CustomUserCreationForm
from openai import OpenAI


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
        }, status=status.HTTP_201_CREATED)

    def get_ai_response(self, user_message):
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key="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",  # Ваш токен
        )

        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://yourwebsite.com",  # Замените на ваш URL сайта
                "X-Title": "Your Site Name",  # Замените на название вашего сайта
            },
            model="qwen/qwen-vl-plus:free",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_message
                        }
                    ]
                }
            ]
        )

        return completion.choices[0].message.content  # Возвращаем ответ от ИИ
