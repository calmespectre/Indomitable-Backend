import os
import jwt
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from .serializers import RegisterSerializer, UserSerializer, UserProfileSerializer
from .models import CustomUser
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = username or kwargs.get('email')
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            return None
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"user": UserSerializer(user).data, "message": "Account created successfully"}, status=status.HTTP_201_CREATED)
        error_message = list(serializer.errors.values())[0][0]
        return Response({"message": str(error_message)}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        try:
            email = request.data.get('email')
            password = request.data.get('password')
            user = authenticate(request, email=email, password=password)
            if user is not None:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': UserSerializer(user).data
                })
            return Response({"message": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            # THIS WILL NOW SEND THE EXACT ERROR TO YOUR REACT APP!
            return Response({
                "message": f"Django Crash Error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordResetView(APIView):
    def post(self, request):
        email = request.data.get('email')
        return Response({"message": "If an account with that email exists, a reset link has been sent."})


class GoogleLoginView(APIView):
    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({"message": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            idinfo = google_id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id']
            )

            email = idinfo['email']
            full_name = idinfo.get('name', '')

            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={'full_name': full_name}
            )

            refresh = RefreshToken.for_user(user)

            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            })

        except ValueError:
            return Response({"message": "Invalid Google token"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AppleLoginView(APIView):
    def post(self, request):
        id_token = request.data.get('id_token')
        full_name = request.data.get('full_name', '')

        if not id_token:
            return Response({"message": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            decoded = jwt.decode(id_token, options={"verify_signature": False})
            email = decoded.get('email')

            if not email:
                return Response({"message": "Email not found in Apple token"}, status=status.HTTP_400_BAD_REQUEST)

            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={'full_name': full_name}
            )

            if created and not user.full_name and full_name:
                user.full_name = full_name
                user.save()

            refresh = RefreshToken.for_user(user)

            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            })

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# --- ACCOUNT PROFILE VIEWS ---

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(
            request.user, context={'request': request})
        return Response(serializer.data)

    def patch(self, request):
        user = request.user
        user.full_name = request.data.get('full_name', user.full_name)
        user.phone_number = request.data.get('phone_number', user.phone_number)
        user.address = request.data.get('address', user.address)
        user.save()
        serializer = UserProfileSerializer(user, context={'request': request})
        return Response(serializer.data)


class UpdateProfilePictureView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if 'profile_picture' not in request.FILES:
            return Response({"message": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

        if user.profile_picture:
            if os.path.isfile(user.profile_picture.path):
                os.remove(user.profile_picture.path)

        user.profile_picture = request.FILES['profile_picture']
        user.save()
        serializer = UserProfileSerializer(user, context={'request': request})
        return Response(serializer.data)


class DeleteProfilePictureView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        if user.profile_picture:
            if os.path.isfile(user.profile_picture.path):
                os.remove(user.profile_picture.path)
            user.profile_picture = None
            user.save()
            return Response({"message": "Profile picture deleted"})
        return Response({"message": "No profile picture to delete"}, status=status.HTTP_400_BAD_REQUEST)


class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.delete()
        return Response({"message": "Account deleted successfully"})
