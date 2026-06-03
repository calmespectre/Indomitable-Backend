from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Order, OrderItem, Favorite, Notification
from .serializers import OrderSerializer, FavoriteSerializer, NotificationSerializer


class OrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(
            user=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        order = Order.objects.create(
            user=request.user,
            order_number=data.get('order_number'),
            tracking_number=data.get('tracking_number', ''),
            subtotal=data.get('subtotal', 0),
            shipping_cost=data.get('shipping_cost', 0),
            total=data.get('total', 0),
            delivery_location=data.get('delivery_location', ''),
            delivery_address=data.get('delivery_address', ''),
            delivery_phone=data.get('delivery_phone', ''),
            payment_method=data.get('payment_method', ''),
            mpesa_number=data.get('mpesa_number', ''),
            estimated_delivery=data.get('estimated_delivery', '')
        )

        items_data = data.get('items', [])
        for item_data in items_data:
            OrderItem.objects.create(
                order=order,
                product_name=item_data.get(
                    'product_name', item_data.get('name', '')),
                product_image=item_data.get(
                    'product_image', item_data.get('image', '')),
                quantity=item_data.get('quantity', 1),
                price=item_data.get('price', 0),
                size=item_data.get('size', ''),
                color=item_data.get('color', '')
            )

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, user=request.user)
            serializer = OrderSerializer(order)
            return Response(serializer.data)
        except Order.DoesNotExist:
            return Response({"message": "Order not found"}, status=status.HTTP_404_NOT_FOUND)


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
                'image': data.get('image', ''),
                'price': data.get('price', 0),
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


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(
            user=request.user).order_by('-date')
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        notification = Notification.objects.create(
            user=request.user,
            type=data.get('type', 'update'),
            title=data.get('title', ''),
            message=data.get('message', ''),
            icon=data.get('icon', ''),
            color=data.get('color', ''),
            order_id=data.get('order_id', ''),
            promo_code=data.get('promoCode', '')
        )
        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
            notification.read = True
            notification.save()
            serializer = NotificationSerializer(notification)
            return Response(serializer.data)
        except Notification.DoesNotExist:
            return Response({"message": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)


class NotificationMarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        Notification.objects.filter(
            user=request.user, read=False).update(read=True)
        return Response({"message": "All notifications marked as read"})


class NotificationDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
            notification.delete()
            return Response({"message": "Notification deleted"})
        except Notification.DoesNotExist:
            return Response({"message": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)
