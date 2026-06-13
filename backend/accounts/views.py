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
from jwt import PyJWKClient

from .serializers import (
    RegisterSerializer, UserSerializer, UserProfileSerializer,
    OrderSerializer, CreateOrderSerializer, FavoriteItemSerializer
)
from .models import CustomUser, Order, OrderItem, OrderStatusHistory, FavoriteItem
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
            google_client_id = settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id']
            idinfo = google_id_token.verify_oauth2_token(
                token, google_requests.Request(), google_client_id
            )

            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')

            email = idinfo['email']
            full_name = idinfo.get('name', '')

            user, created = CustomUser.objects.get_or_create(
                email=email, defaults={'full_name': full_name}
            )
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            })
        except ValueError as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AppleLoginView(APIView):
    def post(self, request):
        id_token_str = request.data.get('id_token')
        full_name = request.data.get('full_name', '')

        if not id_token_str:
            return Response({"message": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            apple_client_id = settings.SOCIALACCOUNT_PROVIDERS['apple']['APP']['client_id']
            jwks_url = "https://appleid.apple.com/auth/keys"
            jwks_client = PyJWKClient(jwks_url)

            signing_key = jwks_client.get_signing_key_from_jwt(id_token_str)
            public_key = signing_key.key

            decoded = jwt.decode(
                id_token_str,
                public_key,
                algorithms=["RS256"],
                audience=apple_client_id,
                issuer="https://appleid.apple.com"
            )

            email = decoded.get('email')
            if not email:
                return Response({"message": "Email not found in Apple token"}, status=status.HTTP_400_BAD_REQUEST)

            user, created = CustomUser.objects.get_or_create(
                email=email, defaults={'full_name': full_name}
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
        except jwt.ExpiredSignatureError:
            return Response({"message": "Apple token has expired"}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.InvalidTokenError as e:
            return Response({"message": f"Invalid Apple token: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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


class PastOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(
            user=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            user = request.user

            delivery_name = data.get('delivery_name') or user.full_name or ''
            delivery_phone = data.get(
                'delivery_phone') or user.phone_number or ''
            delivery_address = data.get(
                'delivery_address') or user.address or ''
            delivery_location = data.get('delivery_location', '')
            payment_method = data.get('payment_method', 'card')
            mpesa_number = data.get('mpesa_number')

            subtotal = sum(
                float(item['product_price']) * item['quantity']
                for item in data['items']
            )
            shipping_cost = 0
            total_amount = subtotal + shipping_cost

            order = Order.objects.create(
                user=user,
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                total_amount=total_amount,
                delivery_name=delivery_name,
                delivery_phone=delivery_phone,
                delivery_address=delivery_address,
                delivery_location=delivery_location,
                payment_method=payment_method,
                mpesa_number=mpesa_number,
            )

            for item in data['items']:
                OrderItem.objects.create(
                    order=order,
                    product_id=item['product_id'],
                    product_name=item['product_name'],
                    product_price=item['product_price'],
                    quantity=item['quantity'],
                    product_image=item.get('product_image', ''),
                )

            OrderStatusHistory.objects.create(
                order=order,
                status='pending',
                description='Order placed successfully'
            )

            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if order.status in ['shipped', 'delivered', 'cancelled']:
            return Response(
                {"error": f"Cannot cancel order with status: {order.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = 'cancelled'
        order.save()

        OrderStatusHistory.objects.create(
            order=order,
            status='cancelled',
            description='Order cancelled by customer'
        )

        serializer = OrderSerializer(order)
        return Response(serializer.data)


class ClearOrderHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        orders = Order.objects.filter(user=request.user)
        count = orders.count()
        orders.delete()
        return Response({"message": f"Cleared {count} orders"})


class FavoriteListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        favorites = FavoriteItem.objects.filter(
            user=request.user).order_by('-added_at')
        serializer = FavoriteItemSerializer(favorites, many=True)
        return Response(serializer.data)

    def post(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response(
                {"message": "product_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        existing = FavoriteItem.objects.filter(
            user=request.user, product_id=product_id
        ).first()
        if existing:
            serializer = FavoriteItemSerializer(existing)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = FavoriteItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FavoriteRemoveView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id):
        try:
            fav = FavoriteItem.objects.get(
                user=request.user, product_id=product_id
            )
            fav.delete()
            return Response({"message": "Removed from favorites"})
        except FavoriteItem.DoesNotExist:
            return Response(
                {"message": "Favorite not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class FavoriteToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response(
                {"message": "product_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        existing = FavoriteItem.objects.filter(
            user=request.user, product_id=product_id
        ).first()

        if existing:
            existing.delete()
            return Response({"is_favorited": False, "message": "Removed from favorites"})
        else:
            serializer = FavoriteItemSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response(
                    {"is_favorited": True, "data": serializer.data},
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
