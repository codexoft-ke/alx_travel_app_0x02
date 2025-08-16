from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Listing, Booking, Review, Payment


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model - used in nested representations
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


class ListingSerializer(serializers.ModelSerializer):
    """
    Serializer for Listing model
    """
    created_by = UserSerializer(read_only=True)
    average_rating = serializers.ReadOnlyField()
    reviews_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'description', 'location', 'price_per_night',
            'max_guests', 'bedrooms', 'bathrooms', 'amenities', 'availability',
            'created_by', 'created_at', 'updated_at', 'is_active',
            'average_rating', 'reviews_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def get_reviews_count(self, obj):
        """Get the count of reviews for this listing"""
        return obj.reviews.count()

    def validate_price_per_night(self, value):
        """Validate price_per_night is positive"""
        if value <= 0:
            raise serializers.ValidationError("Price per night must be greater than 0")
        return value

    def validate_max_guests(self, value):
        """Validate max_guests is reasonable"""
        if value < 1:
            raise serializers.ValidationError("Maximum guests must be at least 1")
        if value > 50:
            raise serializers.ValidationError("Maximum guests cannot exceed 50")
        return value


class ListingDetailSerializer(ListingSerializer):
    """
    Detailed serializer for Listing model including reviews
    """
    reviews = serializers.SerializerMethodField()
    
    class Meta(ListingSerializer.Meta):
        fields = ListingSerializer.Meta.fields + ['reviews']
    
    def get_reviews(self, obj):
        """Get recent reviews for this listing"""
        recent_reviews = obj.reviews.all()[:5]  # Get latest 5 reviews
        return ReviewSerializer(recent_reviews, many=True).data


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for Booking model
    """
    listing = ListingSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    listing_id = serializers.IntegerField(write_only=True)
    duration_days = serializers.ReadOnlyField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'listing', 'listing_id', 'user', 'check_in_date', 'check_out_date',
            'num_guests', 'total_price', 'status', 'special_requests',
            'created_at', 'updated_at', 'duration_days'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user', 'total_price']

    def validate(self, data):
        """Custom validation for booking dates and guests"""
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')
        num_guests = data.get('num_guests', 1)
        listing_id = data.get('listing_id')

        # Validate dates
        if check_in and check_out:
            if check_in >= check_out:
                raise serializers.ValidationError("Check-out date must be after check-in date")
            
            from django.utils import timezone
            if check_in < timezone.now().date():
                raise serializers.ValidationError("Check-in date cannot be in the past")

        # Validate guest count against listing capacity
        if listing_id:
            try:
                listing = Listing.objects.get(id=listing_id)
                if num_guests > listing.max_guests:
                    raise serializers.ValidationError(
                        f"Number of guests ({num_guests}) exceeds maximum allowed ({listing.max_guests})"
                    )
                if not listing.availability:
                    raise serializers.ValidationError("This listing is not available for booking")
            except Listing.DoesNotExist:
                raise serializers.ValidationError("Invalid listing ID")

        return data

    def create(self, validated_data):
        """Create booking with calculated total price"""
        listing_id = validated_data.pop('listing_id')
        listing = Listing.objects.get(id=listing_id)
        
        # Calculate total price
        check_in = validated_data['check_in_date']
        check_out = validated_data['check_out_date']
        duration = (check_out - check_in).days
        total_price = listing.price_per_night * duration
        
        booking = Booking.objects.create(
            listing=listing,
            total_price=total_price,
            **validated_data
        )
        return booking


class BookingCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for creating bookings
    """
    listing_id = serializers.IntegerField()
    
    class Meta:
        model = Booking
        fields = [
            'listing_id', 'check_in_date', 'check_out_date', 
            'num_guests', 'special_requests'
        ]

    def validate(self, data):
        """Validate booking data"""
        return BookingSerializer().validate(data)


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for Review model
    """
    user = UserSerializer(read_only=True)
    listing = ListingSerializer(read_only=True)
    listing_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'listing', 'listing_id', 'user', 'booking', 'rating', 'comment',
            'cleanliness_rating', 'accuracy_rating', 'location_rating', 'value_rating',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user', 'listing']

    def validate_rating(self, value):
        """Validate rating is between 1 and 5"""
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

    def validate(self, data):
        """Validate review data"""
        listing_id = data.get('listing_id')
        user = self.context['request'].user if self.context.get('request') else None
        
        if listing_id and user:
            # Check if user already reviewed this listing
            if Review.objects.filter(listing_id=listing_id, user=user).exists():
                raise serializers.ValidationError("You have already reviewed this listing")
        
        return data

    def create(self, validated_data):
        """Create review with listing"""
        listing_id = validated_data.pop('listing_id')
        listing = Listing.objects.get(id=listing_id)
        
        review = Review.objects.create(
            listing=listing,
            **validated_data
        )
        return review


class ReviewCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for creating reviews
    """
    listing_id = serializers.IntegerField()
    
    class Meta:
        model = Review
        fields = [
            'listing_id', 'rating', 'comment',
            'cleanliness_rating', 'accuracy_rating', 'location_rating', 'value_rating'
        ]

    def validate(self, data):
        """Validate review data"""
        return ReviewSerializer().validate(data)


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for Payment model
    """
    booking = BookingSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    booking_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_id', 'booking', 'booking_id', 'user', 'amount', 'currency',
            'payment_method', 'status', 'chapa_tx_ref', 'chapa_checkout_url',
            'chapa_transaction_id', 'payment_reference', 'failure_reason',
            'created_at', 'updated_at', 'paid_at', 'is_successful', 'is_pending'
        ]
        read_only_fields = [
            'id', 'payment_id', 'user', 'chapa_tx_ref', 'chapa_checkout_url',
            'chapa_transaction_id', 'payment_reference', 'failure_reason',
            'created_at', 'updated_at', 'paid_at', 'is_successful', 'is_pending'
        ]

    def validate_booking_id(self, value):
        """Validate booking exists and belongs to user"""
        user = self.context['request'].user if self.context.get('request') else None
        if user:
            try:
                booking = Booking.objects.get(id=value, user=user)
                # Check if payment already exists for this booking
                if hasattr(booking, 'payment'):
                    raise serializers.ValidationError("Payment already exists for this booking")
                return value
            except Booking.DoesNotExist:
                raise serializers.ValidationError("Booking not found or does not belong to you")
        return value

    def validate_amount(self, value):
        """Validate payment amount matches booking total"""
        booking_id = self.initial_data.get('booking_id')
        if booking_id:
            try:
                booking = Booking.objects.get(id=booking_id)
                if value != booking.total_price:
                    raise serializers.ValidationError(
                        f"Payment amount ({value}) must match booking total ({booking.total_price})"
                    )
            except Booking.DoesNotExist:
                pass
        return value

    def create(self, validated_data):
        """Create payment for booking"""
        booking_id = validated_data.pop('booking_id')
        booking = Booking.objects.get(id=booking_id)
        
        payment = Payment.objects.create(
            booking=booking,
            user=booking.user,
            **validated_data
        )
        return payment


class PaymentCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for creating payments
    """
    booking_id = serializers.IntegerField()
    
    class Meta:
        model = Payment
        fields = ['booking_id', 'amount', 'currency', 'payment_method']

    def validate(self, data):
        """Validate payment data"""
        return PaymentSerializer(context=self.context).validate(data)


class PaymentStatusSerializer(serializers.ModelSerializer):
    """
    Serializer for payment status updates
    """
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_id', 'status', 'chapa_transaction_id', 
            'payment_reference', 'paid_at', 'is_successful'
        ]
        read_only_fields = ['id', 'payment_id', 'is_successful']
