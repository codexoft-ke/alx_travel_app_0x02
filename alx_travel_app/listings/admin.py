from django.contrib import admin
from .models import Listing, Booking, Review, Payment

# Register your models here.

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    """
    Admin configuration for Listing model
    """
    list_display = ('title', 'location', 'price_per_night', 'max_guests', 'created_by', 'availability', 'is_active', 'created_at')
    list_filter = ('availability', 'is_active', 'created_at', 'location', 'bedrooms', 'max_guests')
    search_fields = ('title', 'location', 'description', 'created_by__username')
    list_editable = ('availability', 'is_active')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'average_rating')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'location')
        }),
        ('Property Details', {
            'fields': ('bedrooms', 'bathrooms', 'max_guests', 'amenities')
        }),
        ('Pricing', {
            'fields': ('price_per_night',)
        }),
        ('Availability', {
            'fields': ('availability', 'average_rating')
        }),
        ('Management', {
            'fields': ('created_by', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """
    Admin configuration for Booking model
    """
    list_display = ('id', 'listing', 'user', 'check_in_date', 'check_out_date', 'num_guests', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'check_in_date', 'check_out_date', 'created_at', 'num_guests')
    search_fields = ('listing__title', 'user__username', 'user__email', 'special_requests')
    list_editable = ('status',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'duration_days')
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('listing', 'user', 'check_in_date', 'check_out_date', 'num_guests')
        }),
        ('Pricing & Status', {
            'fields': ('total_price', 'status', 'duration_days')
        }),
        ('Additional Information', {
            'fields': ('special_requests',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('listing', 'user')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Admin configuration for Review model
    """
    list_display = ('id', 'listing', 'user', 'rating', 'created_at', 'has_detailed_ratings')
    list_filter = ('rating', 'created_at', 'cleanliness_rating', 'accuracy_rating', 'location_rating', 'value_rating')
    search_fields = ('listing__title', 'user__username', 'comment')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Review Information', {
            'fields': ('listing', 'user', 'booking')
        }),
        ('Ratings', {
            'fields': ('rating', 'cleanliness_rating', 'accuracy_rating', 'location_rating', 'value_rating')
        }),
        ('Comment', {
            'fields': ('comment',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('listing', 'user', 'booking')
    
    def has_detailed_ratings(self, obj):
        """Check if the review has detailed ratings"""
        return bool(obj.cleanliness_rating or obj.accuracy_rating or obj.location_rating or obj.value_rating)
    has_detailed_ratings.boolean = True
    has_detailed_ratings.short_description = 'Has Detailed Ratings'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """
    Admin configuration for Payment model
    """
    list_display = (
        'payment_id', 'user', 'booking', 'amount', 'currency', 
        'payment_method', 'status', 'chapa_tx_ref', 'created_at'
    )
    list_filter = (
        'status', 'payment_method', 'currency', 'created_at', 'paid_at'
    )
    search_fields = (
        'payment_id', 'chapa_tx_ref', 'chapa_transaction_id', 
        'user__username', 'user__email', 'booking__id'
    )
    list_editable = ('status',)
    ordering = ('-created_at',)
    readonly_fields = (
        'payment_id', 'created_at', 'updated_at', 'paid_at', 
        'is_successful', 'is_pending', 'can_be_refunded'
    )
    
    fieldsets = (
        ('Payment Information', {
            'fields': (
                'payment_id', 'booking', 'user', 'amount', 'currency', 
                'payment_method', 'status'
            )
        }),
        ('Chapa Details', {
            'fields': (
                'chapa_tx_ref', 'chapa_checkout_url', 'chapa_transaction_id',
                'payment_reference'
            )
        }),
        ('Status Information', {
            'fields': (
                'is_successful', 'is_pending', 'can_be_refunded',
                'failure_reason'
            )
        }),
        ('Gateway Response', {
            'fields': ('gateway_response',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('booking', 'user', 'booking__listing')
    
    def has_change_permission(self, request, obj=None):
        """Allow status changes but protect critical fields"""
        return True
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly after creation"""
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing payment
            readonly.extend([
                'booking', 'user', 'amount', 'currency', 'payment_method',
                'chapa_tx_ref', 'chapa_checkout_url', 'chapa_transaction_id'
            ])
        return readonly
