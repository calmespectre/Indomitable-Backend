from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from rest_framework import generics, views
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from orders.models import Order, OrderItem
from accounts.models import CustomUser
from .serializers import OrderSerializer


class DashboardStatsView(views.APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        range = request.GET.get('range', 'week')
        now = timezone.now()
        if range == 'today':
            start = now.replace(hour=0, minute=0, second=0)
        elif range == 'week':
            start = now - timedelta(days=7)
        elif range == 'month':
            start = now - timedelta(days=30)
        else:
            start = now - timedelta(days=365)

        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status='pending').count()
        total_revenue = Order.objects.aggregate(
            Sum('total'))['total__sum'] or 0
        total_products = 0  # you can add if you have Product model
        total_customers = CustomUser.objects.count()
        low_stock = 0
        monthly_revenue = Order.objects.filter(
            created_at__gte=start).aggregate(Sum('total'))['total__sum'] or 0
        monthly_orders = Order.objects.filter(created_at__gte=start).count()
        conversion_rate = 0  # calculate as needed

        return Response({
            'totalOrders': total_orders,
            'pendingOrders': pending_orders,
            'totalRevenue': float(total_revenue),
            'totalProducts': total_products,
            'totalCustomers': total_customers,
            'lowStockItems': low_stock,
            'monthlyRevenue': float(monthly_revenue),
            'monthlyOrders': monthly_orders,
            'conversionRate': conversion_rate,
        })


class RecentOrdersView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        limit = int(self.request.GET.get('limit', 10))
        return Order.objects.all().order_by('-created_at')[:limit]


class TopProductsView(views.APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        limit = int(request.GET.get('limit', 5))
        items = OrderItem.objects.values('product_name', 'product_image') \
            .annotate(total_sold=Sum('quantity'), revenue=Sum('price')) \
            .order_by('-total_sold')[:limit]
        return Response([{
            'id': idx,
            'name': item['product_name'],
            'image': item.get('product_image'),
            'total_sold': item['total_sold'],
            'revenue': float(item['revenue'])
        } for idx, item in enumerate(items)])


class RecentCustomersView(views.APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        limit = int(request.GET.get('limit', 5))
        users = CustomUser.objects.order_by('-date_joined')[:limit]
        return Response([{
            'id': user.id,
            'full_name': f"{user.first_name} {user.last_name}".strip() or user.email,
            'email': user.email,
            'phone': getattr(user, 'phone', ''),
            'created_at': user.date_joined,
            'order_count': Order.objects.filter(user=user).count(),
            'total_spent': float(Order.objects.filter(user=user).aggregate(Sum('total'))['total__sum'] or 0)
        } for user in users])


class CustomerListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return CustomUser.objects.all()

    def list(self, request, *args, **kwargs):
        users = self.get_queryset()
        data = [{
            'id': user.id,
            'full_name': f"{user.first_name} {user.last_name}".strip() or user.email,
            'email': user.email,
            'phone': getattr(user, 'phone', ''),
            'created_at': user.date_joined,
            'order_count': Order.objects.filter(user=user).count(),
            'total_spent': float(Order.objects.filter(user=user).aggregate(Sum('total'))['total__sum'] or 0),
            'address': getattr(user, 'address', '')
        } for user in users]
        return Response(data)


class OrderUpdateStatusView(views.APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({"error": "Not found"}, status=404)
        new_status = request.data.get('status')
        if new_status in ['pending', 'processing', 'shipped', 'delivered', 'cancelled']:
            order.status = new_status
            order.save()
            serializer = OrderSerializer(order)
            return Response(serializer.data)
        return Response({"error": "Invalid status"}, status=400)

# You'll also need Notification model/views for announcements – skip for now
