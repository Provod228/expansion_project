from django.views.generic import TemplateView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login, logout, get_user_model
from .models import CustomUser, Chat, Message
from django.shortcuts import redirect, render, get_object_or_404
from .forms import CustomAuthenticationForm, CustomUserCreationForm
from openai import OpenAI
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib import messages
from .tokens import generate_activation_token
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
import logging

logger = logging.getLogger(__name__)

class UserRegistrationView(TemplateView):
    template_name = 'register.html'  # Укажите ваш шаблон

    def get(self, request, *args, **kwargs):
        form = CustomUserCreationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = CustomUserCreationForm(data=request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Деактивируем пользователя до активации
            user.save()

            # Отправка электронной почты
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = generate_activation_token(user)
            activation_link = f"http://localhost:8000/activate/{uid}/{token}/"
            send_mail(
                'Активация аккаунта',
                f'Пожалуйста, активируйте свой аккаунт, перейдя по следующей ссылке: {activation_link}',
                'your-email@example.com',
                [user.email],
                fail_silently=False,
            )
            messages.success(request, 'Пожалуйста, проверьте свою почту для активации аккаунта.')
            return redirect('login')
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
    template_name = 'chat.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_authenticated:
            chat, created = Chat.objects.get_or_create(user=self.request.user)  # Создаем чат, если его еще нет
            context['chat'] = chat  # Передаем чат в контекст
            context['messages'] = Message.objects.filter(chat=chat)  # Получаем сообщения для чата
        else:
            context['chat'] = None
            context['messages'] = []

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

def activate_account(request, uidb64, token):
    user_id = force_str(urlsafe_base64_decode(uidb64))
    user = get_object_or_404(CustomUser, pk=user_id)

    if default_token_generator.check_token(user, token):
        if not user.is_active:
            user.is_active = True
            user.save()
            
            # Создание чата для активированного пользователя
            Chat.objects.get_or_create(user=user)  # Создаем чат, если его еще нет
            
            messages.success(request, 'Ваш аккаунт активирован!')
            return redirect('activation_success')
        else:
            messages.info(request, 'Ваш аккаунт уже активирован.')
            return redirect('already_active')
    else:
        messages.error(request, 'Ссылка активации недействительна.')
        return redirect('activation_failed')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Деактивируем пользователя до активации
            user.save()
            
            # Создание чата для нового пользователя
            Chat.objects.create(user=user)  # Создаем чат
            
            # Отправка электронной почты с активацией
            messages.success(request, 'Пожалуйста, проверьте свою почту для активации аккаунта.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def activation_success_view(request):
    return render(request, 'activation_success.html')  # Укажите ваш шаблон

def google_login(request):
    # Логика для входа через Google
    user = ...  # Получите пользователя после успешного входа

    if not Chat.objects.filter(user=user).exists():
        logger.info(f"Создание нового чата для пользователя: {user.username}")
        Chat.objects.create(user=user)
    else:
        logger.info(f"Чат уже существует для пользователя: {user.username}")

    return redirect('chat_page')
