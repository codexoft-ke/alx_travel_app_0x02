"""
URL configuration for listings app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'listings', views.ListingViewSet, basename='listing')
router.register(r'bookings', views.BookingViewSet, basename='booking')
router.register(r'reviews', views.ReviewViewSet, basename='review')
router.register(r'payments', views.PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('welcome/', views.welcome_view, name='welcome'),
    path('payment/webhook/', views.payment_webhook, name='payment-webhook'),
    # Add more URL patterns here as needed
]
