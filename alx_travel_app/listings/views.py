from django.shortcuts import render
from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.urls import reverse
import logging

from .models import Listing, Booking, Review, Payment
from .serializers import (
    ListingSerializer, ListingDetailSerializer, 
    BookingSerializer, BookingCreateSerializer,
    ReviewSerializer, ReviewCreateSerializer,
    PaymentSerializer, PaymentCreateSerializer, PaymentStatusSerializer
)
from .services import ChapaPaymentService, ChapaPaymentError
from .tasks import send_payment_confirmation_email, send_booking_confirmation_email, send_payment_failed_email

logger = logging.getLogger(__name__)

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


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payments.
    
    Provides operations for payment initiation, verification, and status tracking.
    """
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_method', 'booking']
    ordering_fields = ['created_at', 'amount', 'paid_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return payments for the current user"""
        return Payment.objects.filter(user=self.request.user).select_related(
            'booking', 'booking__listing'
        )
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return PaymentCreateSerializer
        elif self.action in ['update_status', 'verify']:
            return PaymentStatusSerializer
        return PaymentSerializer
    
    def perform_create(self, serializer):
        """Set the user field to the current user"""
        serializer.save(user=self.request.user)
    
    @swagger_auto_schema(
        method='post',
        operation_description="Initiate payment for a booking",
        request_body=PaymentCreateSerializer,
        responses={
            201: openapi.Response(
                description="Payment initiated successfully",
                schema=PaymentSerializer
            ),
            400: "Bad request - validation errors",
            404: "Booking not found"
        }
    )
    @action(detail=False, methods=['post'])
    def initiate(self, request):
        """
        Initiate payment with Chapa
        """
        serializer = PaymentCreateSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Create payment record
            payment = serializer.save()
            
            # Initialize Chapa payment service
            chapa_service = ChapaPaymentService()
            
            # Build callback and return URLs
            callback_url = request.build_absolute_uri(
                reverse('payment-webhook')
            )
            return_url = request.build_absolute_uri('/payment/success/')
            
            # Create payment payload
            payment_payload = chapa_service.create_payment_payload(
                payment=payment,
                user=request.user,
                booking=payment.booking,
                callback_url=callback_url,
                return_url=return_url
            )
            
            # Initialize payment with Chapa
            chapa_response = chapa_service.initialize_payment(payment_payload)
            
            # Update payment with Chapa response
            payment.chapa_checkout_url = chapa_response.get('checkout_url')
            payment.status = 'processing'
            payment.gateway_response = chapa_response
            payment.save()
            
            # Update booking status
            payment.booking.status = 'pending'
            payment.booking.save()
            
            # Send booking confirmation email
            send_booking_confirmation_email.delay(payment.booking.id)
            
            # Return response with checkout URL
            response_serializer = PaymentSerializer(payment)
            return Response({
                'message': 'Payment initiated successfully',
                'payment': response_serializer.data,
                'checkout_url': payment.chapa_checkout_url
            }, status=status.HTTP_201_CREATED)
            
        except ChapaPaymentError as e:
            logger.error(f"Chapa payment error: {str(e)}")
            return Response({
                'error': 'Payment initiation failed',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Payment initiation error: {str(e)}")
            return Response({
                'error': 'Internal server error during payment initiation'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        method='post',
        operation_description="Verify payment status with Chapa",
        responses={
            200: openapi.Response(
                description="Payment verification result",
                schema=PaymentStatusSerializer
            ),
            404: "Payment not found",
            400: "Verification failed"
        }
    )
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """
        Verify payment status with Chapa
        """
        payment = self.get_object()
        
        if not payment.chapa_tx_ref:
            return Response({
                'error': 'No transaction reference available for verification'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Initialize Chapa service
            chapa_service = ChapaPaymentService()
            
            # Verify payment with Chapa
            verification_data = chapa_service.verify_payment(payment.chapa_tx_ref)
            
            # Update payment status
            new_status = chapa_service.get_payment_status(verification_data)
            old_status = payment.status
            
            payment.status = new_status
            payment.chapa_transaction_id = verification_data.get('id')
            payment.payment_reference = verification_data.get('reference')
            payment.gateway_response = verification_data
            
            if new_status == 'completed' and old_status != 'completed':
                payment.paid_at = timezone.now()
                # Update booking status
                payment.booking.status = 'confirmed'
                payment.booking.save()
                # Send confirmation email
                send_payment_confirmation_email.delay(payment.id)
            elif new_status == 'failed':
                payment.failure_reason = verification_data.get('failure_reason', 'Payment failed')
                # Send failure notification
                send_payment_failed_email.delay(payment.id)
            
            payment.save()
            
            serializer = PaymentStatusSerializer(payment)
            return Response({
                'message': 'Payment verification completed',
                'payment': serializer.data
            })
            
        except ChapaPaymentError as e:
            logger.error(f"Chapa verification error: {str(e)}")
            return Response({
                'error': 'Payment verification failed',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Payment verification error: {str(e)}")
            return Response({
                'error': 'Internal server error during payment verification'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        method='get',
        operation_description="Get payment status",
        responses={200: PaymentStatusSerializer}
    )
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """
        Get current payment status
        """
        payment = self.get_object()
        serializer = PaymentStatusSerializer(payment)
        return Response(serializer.data)


@swagger_auto_schema(
    method='post',
    operation_description="Webhook endpoint for Chapa payment notifications",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'tx_ref': openapi.Schema(type=openapi.TYPE_STRING),
            'status': openapi.Schema(type=openapi.TYPE_STRING),
            'id': openapi.Schema(type=openapi.TYPE_STRING),
            'amount': openapi.Schema(type=openapi.TYPE_NUMBER),
            'currency': openapi.Schema(type=openapi.TYPE_STRING),
        }
    ),
    responses={
        200: "Webhook processed successfully",
        400: "Invalid webhook data",
        404: "Payment not found"
    }
)
@api_view(['POST'])
def payment_webhook(request):
    """
    Webhook endpoint for Chapa payment notifications
    """
    try:
        webhook_data = request.data
        tx_ref = webhook_data.get('tx_ref')
        
        if not tx_ref:
            logger.warning("Webhook received without tx_ref")
            return Response({'error': 'Missing tx_ref'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Find payment by transaction reference
        try:
            payment = Payment.objects.get(chapa_tx_ref=tx_ref)
        except Payment.DoesNotExist:
            logger.warning(f"Payment not found for tx_ref: {tx_ref}")
            return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Initialize Chapa service for verification
        chapa_service = ChapaPaymentService()
        
        # Verify payment with Chapa to ensure webhook authenticity
        verification_data = chapa_service.verify_payment(tx_ref)
        
        # Update payment status
        new_status = chapa_service.get_payment_status(verification_data)
        old_status = payment.status
        
        payment.status = new_status
        payment.chapa_transaction_id = verification_data.get('id')
        payment.payment_reference = verification_data.get('reference')
        payment.gateway_response = verification_data
        
        if new_status == 'completed' and old_status != 'completed':
            payment.paid_at = timezone.now()
            # Update booking status
            payment.booking.status = 'confirmed'
            payment.booking.save()
            # Send confirmation email
            send_payment_confirmation_email.delay(payment.id)
        elif new_status == 'failed':
            payment.failure_reason = verification_data.get('failure_reason', 'Payment failed')
            # Send failure notification
            send_payment_failed_email.delay(payment.id)
        
        payment.save()
        
        logger.info(f"Webhook processed successfully for payment {payment.id}")
        
        return Response({
            'message': 'Webhook processed successfully',
            'payment_id': payment.payment_id,
            'status': payment.status
        })
        
    except ChapaPaymentError as e:
        logger.error(f"Chapa error in webhook: {str(e)}")
        return Response({
            'error': 'Payment verification failed',
            'details': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return Response({
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
