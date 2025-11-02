from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Device(models.Model):
    DEVICE_TYPES = [
        ('CUSTOMER', 'Customer'),
        ('STAFF', 'Staff'),
        ('MASTER', 'Master'),
        ('SLAVE', 'Slave')
    ]
    
    device_id = models.CharField(max_length=255, unique=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    is_active = models.BooleanField(default=True)
    last_active = models.DateTimeField(auto_now=True)
    auth_token = models.CharField(max_length=500, blank=True, null=True)
    
    class Meta:
        db_table = 'devices'
    
    def __str__(self):
        return f"{self.device_id} - {self.device_type}"


class Table(models.Model):
    table_number = models.CharField(max_length=20, unique=True)
    capacity = models.IntegerField()
    is_occupied = models.BooleanField(default=False)
    qr_code = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'tables'
    
    def __str__(self):
        return f"Table {self.table_number}"


class ServiceRequest(models.Model):
    REQUEST_TYPES = [
        ('WAITER', 'Call Waiter'),
        ('BILL', 'Request Bill'),
        ('ORDER', 'Place Order'),
        ('ASSISTANCE', 'Need Assistance')
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled')
    ]
    
    request_id = models.AutoField(primary_key=True)
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='requests')
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    customer_device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='customer_requests')
    assigned_staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'service_requests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Request {self.request_id} - {self.request_type} - {self.status}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('SERVICE_REQUEST', 'Service Request'),
        ('ORDER_UPDATE', 'Order Update'),
        ('SYSTEM', 'System')
    ]
    
    notification_id = models.AutoField(primary_key=True)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"


class APILog(models.Model):
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    response_time = models.FloatField()  # in milliseconds
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'api_logs'
    
    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.status_code}"
