from rest_framework import serializers
from .models import CustomUser
from django.conf import settings


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'full_name', 'is_staff']


class UserProfileSerializer(serializers.ModelSerializer):
    # React expects profile_picture_url, so we generate it here
    profile_picture_url = serializers.SerializerMethodField()
    memberSince = serializers.CharField(source='date_joined')

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'full_name', 'phone_number', 'address',
            'profile_picture', 'profile_picture_url', 'is_staff',
            'is_superuser', 'memberSince'
        ]
        read_only_fields = ['id', 'email',
                            'is_staff', 'is_superuser', 'memberSince']

    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            # Returns absolute URL like http://127.0.0.1:8000/media/profile_pics/image.jpg
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
            return f"{settings.BASE_URL}{obj.profile_picture.url}"
        return None


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'full_name', 'password']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data.get('full_name', ''),
            password=validated_data['password']
        )
        return user
