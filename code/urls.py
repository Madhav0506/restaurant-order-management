from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (DeviceViewSet, TableViewSet, ServiceRequestViewSet, 
                    NotificationViewSet, register, login)

router = DefaultRouter()
router.register(r'devices', DeviceViewSet)
router.register(r'tables', TableViewSet)
router.register(r'requests', ServiceRequestViewSet)
router.register(r'notifications', NotificationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', register, name='register'),
    path('auth/login/', login, name='login'),
]
