from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Device, Table, ServiceRequest, Notification

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class DeviceSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Device
        fields = ['id', 'device_id', 'device_type', 'user', 'is_active', 'last_active']
        read_only_fields = ['last_active', 'auth_token']


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ['id', 'table_number', 'capacity', 'is_occupied', 'qr_code']


class ServiceRequestSerializer(serializers.ModelSerializer):
    table = TableSerializer(read_only=True)
    customer_device = DeviceSerializer(read_only=True)
    assigned_staff = UserSerializer(read_only=True)
    table_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ServiceRequest
        fields = ['request_id', 'table', 'table_id', 'request_type', 'status', 
                  'customer_device', 'assigned_staff', 'created_at', 'updated_at', 'notes']
        read_only_fields = ['request_id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        table_id = validated_data.pop('table_id')
        table = Table.objects.get(id=table_id)
        validated_data['table'] = table
        return super().create(validated_data)


class NotificationSerializer(serializers.ModelSerializer):
    recipient = UserSerializer(read_only=True)
    service_request = ServiceRequestSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = ['notification_id', 'recipient', 'notification_type', 'title', 
                  'message', 'service_request', 'is_read', 'created_at']
        read_only_fields = ['notification_id', 'created_at']
