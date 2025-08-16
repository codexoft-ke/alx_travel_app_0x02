from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid

# Create your models here.

class Listing(models.Model):
    """
    Travel listing model - represents accommodations available for booking
    """
    title = models.CharField(max_length=200, help_text="Title of the travel listing")
    description = models.TextField(help_text="Detailed description of the listing")
    location = models.CharField(max_length=100, help_text="Location of the travel destination")
    price_per_night = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Price per night",
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Additional fields for better listing representation
    max_guests = models.PositiveIntegerField(default=1, help_text="Maximum number of guests")
    bedrooms = models.PositiveIntegerField(default=1, help_text="Number of bedrooms")
    bathrooms = models.PositiveIntegerField(default=1, help_text="Number of bathrooms")
    amenities = models.TextField(blank=True, help_text="Available amenities (comma-separated)")
    availability = models.BooleanField(default=True, help_text="Is the listing available for booking")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Travel Listing"
        verbose_name_plural = "Travel Listings"

    def __str__(self):
        return f"{self.title} - {self.location}"

    @property
    def average_rating(self):
        """Calculate average rating from reviews"""
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(review.rating for review in reviews) / reviews.count(), 1)
        return 0.0


class Booking(models.Model):
    """
    Booking model - represents a reservation for a listing
    """
    BOOKING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    check_in_date = models.DateField(help_text="Check-in date")
    check_out_date = models.DateField(help_text="Check-out date")
    num_guests = models.PositiveIntegerField(default=1, help_text="Number of guests")
    total_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Total booking price",
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    status = models.CharField(
        max_length=20, 
        choices=BOOKING_STATUS_CHOICES, 
        default='pending',
        help_text="Booking status"
    )
    special_requests = models.TextField(blank=True, help_text="Special requests from the guest")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        unique_together = ['listing', 'check_in_date', 'check_out_date']

    def __str__(self):
        return f"Booking for {self.listing.title} by {self.user.username}"

    def clean(self):
        """Custom validation"""
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        
        if self.check_in_date and self.check_out_date:
            if self.check_in_date >= self.check_out_date:
                raise ValidationError("Check-out date must be after check-in date")
            
            if self.check_in_date < timezone.now().date():
                raise ValidationError("Check-in date cannot be in the past")
        
        if self.num_guests and self.listing and self.num_guests > self.listing.max_guests:
            raise ValidationError(f"Number of guests cannot exceed {self.listing.max_guests}")

    @property
    def duration_days(self):
        """Calculate booking duration in days"""
        if self.check_in_date and self.check_out_date:
            return (self.check_out_date - self.check_in_date).days
        return 0


class Review(models.Model):
    """
    Review model - represents user reviews for listings
    """
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    booking = models.OneToOneField(
        Booking, 
        on_delete=models.CASCADE, 
        related_name='review',
        null=True, 
        blank=True,
        help_text="Associated booking (if any)"
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField(help_text="Review comment")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Review categories for detailed feedback
    cleanliness_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="Cleanliness rating (1-5)"
    )
    accuracy_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="Accuracy rating (1-5)"
    )
    location_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="Location rating (1-5)"
    )
    value_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="Value for money rating (1-5)"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        unique_together = ['listing', 'user']  # One review per user per listing

    def __str__(self):
        return f"Review by {self.user.username} for {self.listing.title} ({self.rating}/5)"


class Payment(models.Model):
    """
    Payment model - represents payment transactions for bookings
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('chapa', 'Chapa'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
    ]
    
    # Core payment fields
    payment_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    booking = models.OneToOneField(
        Booking, 
        on_delete=models.CASCADE, 
        related_name='payment',
        help_text="Associated booking"
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='payments',
        help_text="User who made the payment"
    )
    
    # Payment details
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Payment amount"
    )
    currency = models.CharField(max_length=3, default='ETB', help_text="Payment currency")
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHOD_CHOICES, 
        default='chapa',
        help_text="Payment method used"
    )
    status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='pending',
        help_text="Payment status"
    )
    
    # Chapa-specific fields
    chapa_tx_ref = models.CharField(
        max_length=100, 
        unique=True, 
        null=True, 
        blank=True,
        help_text="Chapa transaction reference"
    )
    chapa_checkout_url = models.URLField(
        null=True, 
        blank=True,
        help_text="Chapa checkout URL"
    )
    chapa_transaction_id = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        help_text="Chapa transaction ID"
    )
    
    # Additional tracking fields
    payment_reference = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        help_text="External payment reference"
    )
    gateway_response = models.JSONField(
        null=True, 
        blank=True,
        help_text="Raw gateway response data"
    )
    failure_reason = models.TextField(
        null=True, 
        blank=True,
        help_text="Reason for payment failure"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Timestamp when payment was completed"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        indexes = [
            models.Index(fields=['chapa_tx_ref']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Payment {self.payment_id} - {self.status} - {self.amount} {self.currency}"
    
    @property
    def is_successful(self):
        """Check if payment was successful"""
        return self.status == 'completed'
    
    @property
    def is_pending(self):
        """Check if payment is pending"""
        return self.status in ['pending', 'processing']
    
    @property
    def can_be_refunded(self):
        """Check if payment can be refunded"""
        return self.status == 'completed'
    
    def generate_tx_ref(self):
        """Generate a unique transaction reference for Chapa"""
        if not self.chapa_tx_ref:
            self.chapa_tx_ref = f"ALX-{self.booking.id}-{uuid.uuid4().hex[:8].upper()}"
            self.save(update_fields=['chapa_tx_ref'])
        return self.chapa_tx_ref
