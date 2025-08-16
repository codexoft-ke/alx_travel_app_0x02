from django.shortcuts import render
from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Q

from .models import Listing, Booking, Review
from .serializers import (
    ListingSerializer, ListingDetailSerializer, 
    BookingSerializer, BookingCreateSerializer,
    ReviewSerializer, ReviewCreateSerializer
)

# Create your views here.

class ListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing travel listings.
    
    Provides CRUD operations for listings with filtering and search capabilities.
    """
    queryset = Listing.objects.filter(is_active=True)
    serializer_class = ListingSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['location', 'max_guests', 'bedrooms', 'bathrooms', 'availability']
    search_fields = ['title', 'description', 'location', 'amenities']
    ordering_fields = ['price_per_night', 'created_at', 'title']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'retrieve':
            return ListingDetailSerializer
        return ListingSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Set the created_by field to the current user"""
        serializer.save(created_by=self.request.user)
    
    def get_queryset(self):
        """Custom queryset with optional filtering"""
        queryset = super().get_queryset()
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price is not None:
            queryset = queryset.filter(price_per_night__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price_per_night__lte=max_price)
        
        # Filter by date availability (if booking dates provided)
        check_in = self.request.query_params.get('check_in_date')
        check_out = self.request.query_params.get('check_out_date')
        
        if check_in and check_out:
            # Exclude listings that have bookings overlapping with the requested dates
            overlapping_bookings = Booking.objects.filter(
                Q(check_in_date__lt=check_out) & Q(check_out_date__gt=check_in),
                status__in=['confirmed', 'pending']
            ).values_list('listing_id', flat=True)
            queryset = queryset.exclude(id__in=overlapping_bookings)
        
        return queryset
    
    @swagger_auto_schema(
        method='get',
        operation_description="Get listings available for specific dates",
        manual_parameters=[
            openapi.Parameter('check_in_date', openapi.IN_QUERY, description="Check-in date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('check_out_date', openapi.IN_QUERY, description="Check-out date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
        ]
    )
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get listings available for specific dates"""
        check_in = request.query_params.get('check_in_date')
        check_out = request.query_params.get('check_out_date')
        
        if not check_in or not check_out:
            return Response(
                {"error": "Both check_in_date and check_out_date are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use the existing get_queryset method which handles availability filtering
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing bookings.
    
    Provides CRUD operations for bookings with user-specific filtering.
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'listing']
    ordering_fields = ['created_at', 'check_in_date', 'check_out_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return bookings for the current user"""
        return Booking.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return BookingCreateSerializer
        return BookingSerializer
    
    def perform_create(self, serializer):
        """Set the user field to the current user"""
        serializer.save(user=self.request.user)
    
    @swagger_auto_schema(
        method='post',
        operation_description="Cancel a booking",
        responses={200: "Booking cancelled successfully"}
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking"""
        booking = self.get_object()
        
        if booking.status in ['cancelled', 'completed']:
            return Response(
                {"error": f"Cannot cancel a booking that is already {booking.status}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'cancelled'
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response({
            "message": "Booking cancelled successfully",
            "booking": serializer.data
        })
    
    @swagger_auto_schema(
        method='post',
        operation_description="Confirm a booking",
        responses={200: "Booking confirmed successfully"}
    )
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm a booking"""
        booking = self.get_object()
        
        if booking.status != 'pending':
            return Response(
                {"error": f"Cannot confirm a booking that is {booking.status}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'confirmed'
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response({
            "message": "Booking confirmed successfully",
            "booking": serializer.data
        })


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reviews.
    
    Provides CRUD operations for reviews with listing-specific filtering.
    """
    serializer_class = ReviewSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['listing', 'rating']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return reviews, optionally filtered by listing"""
        queryset = Review.objects.all()
        listing_id = self.request.query_params.get('listing_id')
        
        if listing_id:
            queryset = queryset.filter(listing_id=listing_id)
            
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return ReviewCreateSerializer
        return ReviewSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Set the user field to the current user"""
        serializer.save(user=self.request.user)


@swagger_auto_schema(
    method='get',
    operation_description="Welcome endpoint for the ALX Travel App API",
    responses={
        200: openapi.Response(
            description="Welcome message",
            examples={
                "application/json": {
                    "message": "Welcome to ALX Travel App API",
                    "version": "1.0.0",
                    "endpoints": {
                        "swagger": "/swagger/",
                        "redoc": "/redoc/",
                        "admin": "/admin/"
                    }
                }
            }
        )
    }
)
@api_view(['GET'])
def welcome_view(request):
    """
    Welcome endpoint that provides basic API information.
    """
    return Response({
        "message": "Welcome to ALX Travel App API",
        "version": "1.0.0",
        "endpoints": {
            "swagger": "/swagger/",
            "redoc": "/redoc/",
            "admin": "/admin/"
        }
    }, status=status.HTTP_200_OK)
