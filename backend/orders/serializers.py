from rest_framework import serializers
from .models import Order, OrderItem, Favorite


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'product_image',
                  'quantity', 'price', 'size', 'color']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'tracking_number', 'status', 'created_at',
            'items', 'subtotal', 'shipping_cost', 'total', 'delivery_location',
            'delivery_address', 'delivery_phone', 'payment_method', 'mpesa_number',
            'estimated_delivery'
        ]


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['id', 'product_id', 'title',
                  'image', 'price', 'category', 'added_at']
