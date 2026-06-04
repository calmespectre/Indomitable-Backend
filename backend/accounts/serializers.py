from rest_framework import serializers
from .models import CustomUser, Order, OrderItem, OrderStatusHistory, FavoriteItem
from django.conf import settings


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'full_name', 'is_staff']


class UserProfileSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()
    memberSince = serializers.CharField(source='date_joined')
    isAdmin = serializers.BooleanField(source='is_staff')

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'full_name', 'phone_number', 'address',
            'profile_picture', 'profile_picture_url', 'is_staff',
            'is_superuser', 'memberSince', 'isAdmin'
        ]
        read_only_fields = ['id', 'email',
                            'is_staff', 'is_superuser', 'memberSince', 'isAdmin']

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


# ============ ORDER SERIALIZERS ============

class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'status', 'description', 'created_at']


class OrderItemSerializer(serializers.ModelSerializer):
    # React uses item.price, Django model has product_price
    price = serializers.DecimalField(
        source='product_price', max_digits=10, decimal_places=2)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'product_name',
                  'price', 'quantity', 'product_image']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    # React uses order.total, Django model has total_amount
    total = serializers.DecimalField(
        source='total_amount', max_digits=10, decimal_places=2)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'created_at', 'status',
            'subtotal', 'shipping_cost', 'total',
            'delivery_name', 'delivery_phone',
            'delivery_address', 'delivery_location',
            'payment_method', 'mpesa_number',
            'tracking_number', 'estimated_delivery',
            'items', 'status_history'
        ]
        read_only_fields = ['id', 'order_number', 'created_at']


class CreateOrderSerializer(serializers.Serializer):
    delivery_name = serializers.CharField(max_length=255, required=False)
    delivery_phone = serializers.CharField(max_length=20, required=False)
    delivery_address = serializers.CharField(required=False)
    delivery_location = serializers.CharField(
        max_length=255, required=False, default='')
    payment_method = serializers.CharField(
        max_length=20, required=False, default='card')
    mpesa_number = serializers.CharField(
        max_length=20, required=False, allow_null=True, default=None)
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


# ============ FAVORITE SERIALIZERS ============

class FavoriteItemSerializer(serializers.ModelSerializer):
    # React uses title/image/price, Django model has product_name/product_image/product_price
    title = serializers.CharField(source='product_name')
    image = serializers.URLField(
        source='product_image', allow_null=True, required=False)
    price = serializers.DecimalField(
        source='product_price', max_digits=10, decimal_places=2)
    category = serializers.CharField(required=False, default='')

    class Meta:
        model = FavoriteItem
        fields = ['id', 'product_id', 'title',
                  'image', 'price', 'category', 'added_at']
        read_only_fields = ['id', 'added_at']
