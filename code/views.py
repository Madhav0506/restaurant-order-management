from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Device, Table, ServiceRequest, Notification, APILog
from .serializers import (DeviceSerializer, TableSerializer, 
                          ServiceRequestSerializer, NotificationSerializer, UserSerializer)
import time


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Device.objects.all()
        return Device.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def register_device(self, request):
        """Register a new device"""
        device_id = request.data.get('device_id')
        device_type = request.data.get('device_type')
        
        if not device_id or not device_type:
            return Response({'error': 'device_id and device_type are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        device, created = Device.objects.get_or_create(
            device_id=device_id,
            defaults={'device_type': device_type, 'user': request.user}
        )
        
        if not created:
            device.is_active = True
            device.last_active = timezone.now()
            device.save()
        
        serializer = self.get_serializer(device)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class TableViewSet(viewsets.ModelViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def toggle_occupancy(self, request, pk=None):
        """Toggle table occupied status"""
        table = self.get_object()
        table.is_occupied = not table.is_occupied
        table.save()
        serializer = self.get_serializer(table)
        return Response(serializer.data)


class ServiceRequestViewSet(viewsets.ModelViewSet):
    queryset = ServiceRequest.objects.all()
    serializer_class = ServiceRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return ServiceRequest.objects.all()
        return ServiceRequest.objects.filter(customer_device__user=self.request.user)
    
    def perform_create(self, serializer):
        """Create a service request and send notification to staff"""
        # Get customer's device
        device = Device.objects.filter(user=self.request.user, is_active=True).first()
        
        if not device:
            raise ValueError("No active device found for user")
        
        service_request = serializer.save(customer_device=device)
        
        # Create notifications for all staff users
        staff_users = User.objects.filter(is_staff=True)
        notifications = []
        for staff in staff_users:
            notifications.append(Notification(
                recipient=staff,
                notification_type='SERVICE_REQUEST',
                title=f"New {service_request.get_request_type_display()}",
                message=f"Table {service_request.table.table_number} requires {service_request.get_request_type_display()}",
                service_request=service_request
            ))
        
        Notification.objects.bulk_create(notifications)
        
        # TODO: Send push notification via channels/websockets
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update service request status"""
        service_request = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(ServiceRequest.STATUS_CHOICES):
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        service_request.status = new_status
        
        if new_status == 'ACKNOWLEDGED' and not service_request.assigned_staff:
            service_request.assigned_staff = request.user
        
        service_request.save()
        
        # Notify customer
        Notification.objects.create(
            recipient=service_request.customer_device.user,
            notification_type='ORDER_UPDATE',
            title='Request Status Updated',
            message=f"Your request status is now: {service_request.get_status_display()}",
            service_request=service_request
        )
        
        serializer = self.get_serializer(service_request)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_requests(self, request):
        """Get all pending service requests"""
        pending = ServiceRequest.objects.filter(status='PENDING')
        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)
    
    @action(detail=True, methods=['patch'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        self.get_queryset().update(is_read=True)
        return Response({'message': 'All notifications marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get unread notification count"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})


# Authentication endpoints
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new user"""
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not all([username, email, password]):
        return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.create_user(username=username, email=email, password=password)
    
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'user': UserSerializer(user).data,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login user"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    
    if user is None:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'user': UserSerializer(user).data,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    })
