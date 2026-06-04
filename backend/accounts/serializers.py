from rest_framework import serializers
from .models import CustomUser, Order, OrderItem, FavoriteItem
from django.conf import settings


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'full_name', 'is_staff']


class UserProfileSerializer(serializers.ModelSerializer):
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


# ============ NEW: ORDER & FAVORITE SERIALIZERS ============

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'product_name',
                  'product_price', 'quantity', 'product_image']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'created_at', 'status', 'total_amount',
                  'delivery_name', 'delivery_phone', 'delivery_address', 'items']
        read_only_fields = ['id', 'created_at', 'status']


class CreateOrderSerializer(serializers.Serializer):
    """
    Accepts: { delivery_name, delivery_phone, delivery_address, items: [...] }
    """
    delivery_name = serializers.CharField(max_length=255, required=False)
    delivery_phone = serializers.CharField(max_length=20, required=False)
    delivery_address = serializers.CharField(required=False)
    items = serializers.ListField(
        child=serializers.DictField(), allow_empty=False
    )

    def validate_items(self, value):
        for item in value:
            if 'product_id' not in item or 'product_name' not in item or 'product_price' not in item:
                raise serializers.ValidationError(
                    "Each item needs product_id, product_name, product_price")
            item.setdefault('quantity', 1)
            item.setdefault('product_image', '')
        return value


class FavoriteItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteItem
        fields = ['id', 'product_id', 'product_name',
                  'product_price', 'product_image', 'added_at']
        read_only_fields = ['id', 'added_at']
