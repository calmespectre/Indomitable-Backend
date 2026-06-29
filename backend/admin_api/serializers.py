from rest_framework import serializers
from orders.models import Order, OrderItem
from accounts.models import CustomUser   # adjust to your actual user model


class OrderItemSerializer(serializers.ModelSerializer):
    variant_color = serializers.CharField(source='color', default='')
    variant_size = serializers.CharField(source='size', default='')

    class Meta:
        model = OrderItem
        fields = ['product_name', 'variant_color',
                  'variant_size', 'quantity', 'price']


class OrderSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(
        source='total', max_digits=10, decimal_places=2)
    shipping_address = serializers.CharField(source='delivery_address')
    payment_method = serializers.CharField()
    # you may need to add this field to model
    payment_status = serializers.CharField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'created_at', 'full_name', 'email', 'phone',
            'total_amount', 'status', 'payment_method', 'payment_status',
            'shipping_address', 'items'
        ]

    def get_full_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
        return "Guest"

    def get_email(self, obj):
        return obj.user.email if obj.user else ""

    def get_phone(self, obj):
        return obj.delivery_phone or (obj.user.phone if obj.user else "")
