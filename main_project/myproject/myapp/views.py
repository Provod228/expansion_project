from django.views.generic import TemplateView, View
from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login, logout
from .serializers import UserRegistrationSerializer, UserLoginSerializer, MessageSerializer, ChatSerializer
from .models import CustomUser, Chat, Message, ApiKey
from django.shortcuts import redirect, render, get_object_or_404
from .forms import CustomAuthenticationForm, CustomUserCreationForm
from openai import OpenAI
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib import messages
from .tokens import generate_activation_token
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db import models
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from django.conf import settings
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.contrib.sessions.models import Session
from django.core.exceptions import ObjectDoesNotExist
from allauth.account.adapter import DefaultAccountAdapter
from django.views.decorators.http import condition
from django.db import transaction
import json
from rest_framework.decorators import action
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

@receiver(user_logged_out)
def on_user_logged_out(sender, request, **kwargs):
    # Очищаем все сессионные данные при выходе
    request.session.flush()

class CustomAccountAdapter(DefaultAccountAdapter):
    def logout(self, request):
        try:
            request.session.flush()
            logout(request)
        except Exception as e:
            logger.error(f"Error in custom logout: {e}")

@csrf_exempt
def logout_view(request):
    try:
        with transaction.atomic():
            if request.user.is_authenticated:
                # Удаляем все сессии пользователя
                Session.objects.filter(
                    expire_date__gte=timezone.now(),
                    session_data__contains=str(request.user.id)
                ).delete()
                
                # Очищаем текущую сессию
                request.session.flush()
                
                # Очищаем куки социальной авторизации
                response = JsonResponse({
                    'status': 'success',
                    'message': 'Successfully logged out'
                })
                
                # Удаляем куки авторизации
                response.delete_cookie('sessionid')
                response.delete_cookie('csrftoken')
                response.delete_cookie('messages')
                response.delete_cookie('googleauth')  # Кука Google Auth
                
                # Выполняем выход
                logout(request)
                
                return response
            
            return JsonResponse({
                'status': 'success'
            })
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

class ChatView(TemplateView):
    template_name = 'chat.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            # Получаем все чаты пользователя
            context['chats'] = Chat.objects.filter(user=self.request.user).order_by('-id')
            
            # Получаем текущий чат
            chat_id = self.request.GET.get('chat_id')
            
            # Если чат не выбран или не существует, берем последний или создаем новый
            if not chat_id or not context['chats'].filter(id=chat_id).exists():
                context['current_chat'] = context['chats'].first()
                if not context['current_chat']:
                    context['current_chat'] = Chat.objects.create(
                        user=self.request.user,
                        name=f"Новый чат {timezone.now().strftime('%d.%m.%Y %H:%M')}"
                    )
            else:
                context['current_chat'] = get_object_or_404(Chat, id=chat_id, user=self.request.user)
            
            # Получаем сообщения текущего чата
            context['messages'] = Message.objects.filter(chat=context['current_chat']).order_by('created_at')
        
        return context

class BaseAPIView(APIView):
    permission_classes = [IsAuthenticated]

class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Chat.objects.filter(user=self.request.user).order_by('-id')

    def perform_create(self, serializer):
        chat_name = self.request.data.get('name', '').strip()
        if not chat_name:
            chat_name = f"Новый чат {timezone.now().strftime('%d.%m.%Y %H:%M')}"
        serializer.save(user=self.request.user, name=chat_name)

    @action(detail=True, methods=['post'])
    def rename(self, request, pk=None):
        chat = self.get_object()
        new_name = request.data.get('name', '').strip()
        
        if not new_name:
            return Response(
                {'error': 'Имя чата не может быть пустым'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        chat.name = new_name
        chat.save()
        
        return Response({
            'success': True,
            'chat_id': chat.id,
            'chat_name': chat.name
        })

    @action(detail=True, methods=['post'])
    def delete(self, request, pk=None):
        try:
            with transaction.atomic():
                chat = self.get_object()
                chat.delete()
                
                if not Chat.objects.filter(user=request.user).exists():
                    new_chat = Chat.objects.create(
                        user=request.user,
                        name=f"Новый чат {timezone.now().strftime('%d.%m.%Y %H:%M')}"
                    )
                    return Response({
                        'success': True,
                        'redirect_to': f'/chat/?chat_id={new_chat.id}'
                    })
                return Response({'success': True})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        chat_id = self.request.query_params.get('chat_id')
        if chat_id:
            return Message.objects.filter(
                chat_id=chat_id,
                chat__user=self.request.user
            ).order_by('created_at')
        return Message.objects.none()

    def create(self, request, *args, **kwargs):
        try:
            chat = self.get_or_create_chat(request)
            api_key = self.get_active_api_key()
            message_data = self.prepare_message_data(request, chat, api_key)
            
            serializer = self.get_serializer(data=message_data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            return Response({
                'ai_response': message_data['ai_response']
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get_or_create_chat(self, request):
        chat_id = request.data.get('chat_id')
        if chat_id:
            return get_object_or_404(Chat, id=chat_id, user=request.user)
        return Chat.objects.filter(user=request.user).first() or Chat.objects.create(
            user=request.user,
            name=f"Новый чат {timezone.now().strftime('%d.%m.%Y %H:%M')}"
        )

    def get_active_api_key(self):
        api_key = ApiKey.objects.filter(is_active=True).first()
        if not api_key:
            raise Exception('No active API key available')
        return api_key

    def prepare_message_data(self, request, chat, api_key):
        ai_response = self.get_ai_response(request.data.get('user_message'), api_key)
        return {
            'chat': chat.id,
            'user_message': request.data.get('user_message'),
            'ai_response': ai_response,
            'api_key_used': api_key.id
        }

    def get_ai_response(self, user_message, api_key):
        client = OpenAI(
            base_url=api_key.base_url,
            api_key=api_key.key,
        )

        try:
            completion = client.chat.completions.create(
                model="qwen/qwen-vl-plus:free",
                messages=[{
                    "role": "user",
                    "content": [{"type": "text", "text": user_message}]
                }],
                extra_headers={
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "AI Chat Application",
                }
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in get_ai_response: {str(e)}")
            raise Exception(f"AI service error: {str(e)}")

class GoogleLoginView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('auth_success')
        return redirect('accounts/google/login/')

def auth_success_view(request):
    if request.user.is_authenticated:
        # Проверяем, есть ли у пользователя чаты
        if not Chat.objects.filter(user=request.user).exists():
            # Если чатов нет, создаем новый
            Chat.objects.create(
                user=request.user,
                name=f"Новый чат {timezone.now().strftime('%d.%m.%Y %H:%M')}"
            )
        return render(request, 'auth_success.html')
    return redirect('login')

class LogoutView(BaseAPIView):
    @method_decorator(csrf_exempt)
    def post(self, request):
        try:
            with transaction.atomic():
                if request.user.is_authenticated:
                    Session.objects.filter(
                        expire_date__gte=timezone.now(),
                        session_data__contains=str(request.user.id)
                    ).delete()
                    
                    request.session.flush()
                    
                    response = JsonResponse({
                        'status': 'success',
                        'message': 'Successfully logged out'
                    })
                    
                    response.delete_cookie('sessionid')
                    response.delete_cookie('csrftoken')
                    response.delete_cookie('messages')
                    response.delete_cookie('googleauth')
                    
                    logout(request)
                    
                    return response
                    
                return JsonResponse({'status': 'success'})
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

class UserRegistrationView(View):
    template_name = 'signup.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('chat_view')
        form = CustomUserCreationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('chat_view')
        return render(request, self.template_name, {'form': form})

class UserLoginView(View):
    template_name = 'login.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('chat_view')
        form = CustomAuthenticationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('chat_view')
        return render(request, self.template_name, {'form': form})
