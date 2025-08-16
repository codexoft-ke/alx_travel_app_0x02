from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

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
