#!/usr/bin/env python
"""
Test script for Chapa Payment Integration

This script tests the Chapa payment integration by:
1. Creating a test user and listing
2. Creating a booking
3. Initiating a payment
4. Verifying payment status

Run this script with: python test_chapa_integration.py
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_travel_app.settings')
django.setup()

from django.contrib.auth.models import User
from listings.models import Listing, Booking, Payment
from listings.services import ChapaPaymentService, ChapaPaymentError
from django.utils import timezone
from datetime import date, timedelta


def create_test_data():
    """Create test user, listing, and booking"""
    print("Creating test data...")
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    if created:
        user.set_password('password123')
        user.save()
        print(f"✓ Created test user: {user.username}")
    else:
        print(f"✓ Using existing test user: {user.username}")
    
    # Create test listing
    listing, created = Listing.objects.get_or_create(
        title='Test Accommodation',
        defaults={
            'description': 'A beautiful test accommodation for testing purposes',
            'location': 'Addis Ababa, Ethiopia',
            'price_per_night': Decimal('150.00'),
            'max_guests': 4,
            'bedrooms': 2,
            'bathrooms': 1,
            'amenities': 'WiFi, Air Conditioning, Kitchen',
            'created_by': user
        }
    )
    if created:
        print(f"✓ Created test listing: {listing.title}")
    else:
        print(f"✓ Using existing test listing: {listing.title}")
    
    # Create test booking
    check_in = date.today() + timedelta(days=7)
    check_out = check_in + timedelta(days=3)
    total_price = listing.price_per_night * 3  # 3 nights
    
    booking, created = Booking.objects.get_or_create(
        listing=listing,
        user=user,
        check_in_date=check_in,
        check_out_date=check_out,
        defaults={
            'num_guests': 2,
            'total_price': total_price,
            'status': 'pending'
        }
    )
    if created:
        print(f"✓ Created test booking: #{booking.id}")
    else:
        print(f"✓ Using existing test booking: #{booking.id}")
    
    return user, listing, booking


def test_payment_initialization():
    """Test payment initialization with Chapa"""
    print("\n" + "="*50)
    print("TESTING PAYMENT INITIALIZATION")
    print("="*50)
    
    user, listing, booking = create_test_data()
    
    try:
        # Create payment record
        payment = Payment.objects.create(
            booking=booking,
            user=user,
            amount=booking.total_price,
            currency='ETB',
            payment_method='chapa'
        )
        print(f"✓ Created payment record: {payment.payment_id}")
        
        # Initialize Chapa service
        chapa_service = ChapaPaymentService()
        print("✓ Initialized Chapa service")
        
        # Create payment payload
        callback_url = "https://your-app.com/api/v1/payment/webhook/"
        return_url = "https://your-app.com/payment/success/"
        
        payment_payload = chapa_service.create_payment_payload(
            payment=payment,
            user=user,
            booking=booking,
            callback_url=callback_url,
            return_url=return_url
        )
        print(f"✓ Created payment payload: {payment_payload['tx_ref']}")
        
        # Initialize payment with Chapa
        print("Initializing payment with Chapa...")
        chapa_response = chapa_service.initialize_payment(payment_payload)
        
        # Update payment record
        payment.chapa_checkout_url = chapa_response.get('checkout_url')
        payment.status = 'processing'
        payment.gateway_response = chapa_response
        payment.save()
        
        print("✓ Payment initialization successful!")
        print(f"  - Transaction Reference: {payment.chapa_tx_ref}")
        print(f"  - Checkout URL: {payment.chapa_checkout_url}")
        print(f"  - Status: {payment.status}")
        
        return payment
        
    except ChapaPaymentError as e:
        print(f"✗ Chapa Payment Error: {e}")
        return None
    except Exception as e:
        print(f"✗ Unexpected Error: {e}")
        return None


def test_payment_verification(payment):
    """Test payment verification with Chapa"""
    if not payment:
        print("✗ No payment to verify")
        return
    
    print("\n" + "="*50)
    print("TESTING PAYMENT VERIFICATION")
    print("="*50)
    
    try:
        chapa_service = ChapaPaymentService()
        
        print(f"Verifying payment: {payment.chapa_tx_ref}")
        verification_data = chapa_service.verify_payment(payment.chapa_tx_ref)
        
        # Update payment status
        new_status = chapa_service.get_payment_status(verification_data)
        payment.status = new_status
        payment.chapa_transaction_id = verification_data.get('id')
        payment.payment_reference = verification_data.get('reference')
        payment.gateway_response = verification_data
        
        if new_status == 'completed':
            payment.paid_at = timezone.now()
            payment.booking.status = 'confirmed'
            payment.booking.save()
        
        payment.save()
        
        print("✓ Payment verification successful!")
        print(f"  - Status: {payment.status}")
        print(f"  - Chapa Transaction ID: {payment.chapa_transaction_id}")
        print(f"  - Payment Reference: {payment.payment_reference}")
        
    except ChapaPaymentError as e:
        print(f"✗ Chapa Verification Error: {e}")
    except Exception as e:
        print(f"✗ Unexpected Error: {e}")


def print_summary():
    """Print summary of all payments"""
    print("\n" + "="*50)
    print("PAYMENT SUMMARY")
    print("="*50)
    
    payments = Payment.objects.all().order_by('-created_at')[:5]
    
    if not payments.exists():
        print("No payments found.")
        return
    
    for payment in payments:
        print(f"\nPayment ID: {payment.payment_id}")
        print(f"  - Booking: #{payment.booking.id}")
        print(f"  - User: {payment.user.username}")
        print(f"  - Amount: {payment.amount} {payment.currency}")
        print(f"  - Status: {payment.status}")
        print(f"  - Chapa TX Ref: {payment.chapa_tx_ref}")
        print(f"  - Created: {payment.created_at}")
        if payment.paid_at:
            print(f"  - Paid: {payment.paid_at}")


def main():
    """Main test function"""
    print("CHAPA PAYMENT INTEGRATION TEST")
    print("=" * 50)
    
    try:
        # Test payment initialization
        payment = test_payment_initialization()
        
        if payment:
            # Test payment verification
            test_payment_verification(payment)
        
        # Print summary
        print_summary()
        
        print("\n" + "="*50)
        print("TEST COMPLETED")
        print("="*50)
        print("Note: This test uses Chapa's sandbox environment.")
        print("To complete a test payment, visit the checkout URL and use test card details.")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"Test failed with error: {e}")


if __name__ == '__main__':
    main()
