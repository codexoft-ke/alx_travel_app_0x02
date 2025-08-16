"""
URL configuration for listings app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it.
router = DefaultRouter()
# router.register(r'', views.ListingViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('welcome/', views.welcome_view, name='welcome'),
    # Add more URL patterns here as needed
]
