from rest_framework import serializers
from .models import CustomUser, Chat, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('id', 'chat', 'user_message', 'ai_response', 'created_at', 'api_key_used')
        read_only_fields = ('created_at',)

    def validate_user_message(self, value):
        if not value.strip():
            raise serializers.ValidationError('Message cannot be empty')
        return value.strip()

    def validate_chat(self, value):
        if not value:
            raise serializers.ValidationError('Chat is required')
        return value

    def create(self, validated_data):
        return super().create(validated_data)


class ChatSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Chat
        fields = ('id', 'name', 'created_at', 'is_active', 'messages')


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = CustomUser(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email')
