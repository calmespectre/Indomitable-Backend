from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from .models import Order, OrderItem, Favorite
from .serializers import OrderSerializer, FavoriteSerializer


class OrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(
            user=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data

        order_number = data.get('order_number', '')
        if Order.objects.filter(order_number=order_number).exists():
            return Response({"error": "Order number already exists"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.create(
                user=request.user,
                order_number=order_number,
                tracking_number=data.get('tracking_number', ''),
                subtotal=Decimal(str(data.get('subtotal', 0))),
                shipping_cost=Decimal(str(data.get('shipping_cost', 0))),
                total=Decimal(str(data.get('total', 0))),
                delivery_location=data.get('delivery_location', '') or None,
                delivery_address=data.get('delivery_address', '') or None,
                delivery_phone=data.get('delivery_phone', '') or None,
                payment_method=data.get('payment_method', '') or None,
                mpesa_number=data.get('mpesa_number', '') or None,
                estimated_delivery=data.get('estimated_delivery', '') or None
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        items_data = data.get('items', [])
        for item_data in items_data:
            product_image = item_data.get(
                'product_image', item_data.get('image', ''))
            if not product_image:
                product_image = None

            try:
                OrderItem.objects.create(
                    order=order,
                    product_name=item_data.get(
                        'product_name', item_data.get('name', 'Unknown Product')),
                    product_image=product_image,
                    quantity=int(item_data.get('quantity', 1)),
                    price=Decimal(str(item_data.get('price', 0))),
                    size=item_data.get('size', '') or None,
                    color=item_data.get('color', '') or None
                )
            except Exception as e:
                order.delete()
                return Response({"error": f"Failed to save item: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, user=request.user)
            if order.status in ['shipped', 'delivered']:
                return Response({"error": "Cannot cancel order that has been shipped or delivered"}, status=status.HTTP_400_BAD_REQUEST)
            order.status = 'cancelled'
            order.save()
            serializer = OrderSerializer(order)
            return Response(serializer.data)
        except Order.DoesNotExist:
            return Response({"message": "Order not found"}, status=status.HTTP_404_NOT_FOUND)


class OrderClearHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        orders = Order.objects.filter(user=request.user)
        orders.delete()
        return Response({"message": "Order history cleared"})


class FavoriteListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        favorites = Favorite.objects.filter(user=request.user)
        serializer = FavoriteSerializer(favorites, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            product_id=data.get('product_id'),
            defaults={
                'title': data.get('title', ''),
                'image': data.get('image', '') or None,
                'price': Decimal(str(data.get('price', 0))),
                'category': data.get('category', '')
            }
        )
        if not created:
            return Response({"message": "Already in favorites"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = FavoriteSerializer(favorite)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FavoriteDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id):
        try:
            favorite = Favorite.objects.get(
                user=request.user, product_id=product_id)
            favorite.delete()
            return Response({"message": "Removed from favorites"})
        except Favorite.DoesNotExist:
            return Response({"message": "Favorite not found"}, status=status.HTTP_404_NOT_FOUND)
