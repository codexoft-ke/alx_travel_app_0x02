"""
Celery tasks for ALX Travel App

This module contains asynchronous tasks for background processing,
including email notifications and payment confirmations.
"""

from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_payment_confirmation_email(self, payment_id: int):
    """
    Send payment confirmation email to user
    
    Args:
        payment_id: Payment model ID
    """
    try:
        from .models import Payment
        
        payment = Payment.objects.select_related(
            'booking', 'booking__listing', 'user'
        ).get(id=payment_id)
        
        if not payment.is_successful:
            logger.warning(f"Payment {payment_id} is not successful, skipping email")
            return
        
        user = payment.user
        booking = payment.booking
        listing = booking.listing
        
        # Email context
        context = {
            'user': user,
            'payment': payment,
            'booking': booking,
            'listing': listing,
            'company_name': 'ALX Travel App',
            'support_email': 'support@alxtravel.com',
            'current_year': timezone.now().year,
        }
        
        # Email subject and content
        subject = f'Payment Confirmation - Booking #{booking.id}'
        
        # Plain text content
        text_content = f"""
        Dear {user.first_name or user.username},
        
        Thank you for your payment! Your booking has been confirmed.
        
        Booking Details:
        - Booking ID: #{booking.id}
        - Property: {listing.title}
        - Location: {listing.location}
        - Check-in: {booking.check_in_date}
        - Check-out: {booking.check_out_date}
        - Guests: {booking.num_guests}
        - Total Amount: {payment.amount} {payment.currency}
        - Payment ID: {payment.payment_id}
        - Transaction Reference: {payment.chapa_tx_ref}
        
        If you have any questions, please contact us at {context['support_email']}.
        
        Best regards,
        ALX Travel App Team
        """
        
        # HTML content (you can create a template for this)
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; text-align: center;">
                <h1 style="color: #007bff;">Payment Confirmed!</h1>
            </div>
            
            <div style="padding: 20px;">
                <p>Dear {user.first_name or user.username},</p>
                
                <p>Thank you for your payment! Your booking has been confirmed.</p>
                
                <div style="background-color: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Booking Details</h3>
                    <p><strong>Booking ID:</strong> #{booking.id}</p>
                    <p><strong>Property:</strong> {listing.title}</p>
                    <p><strong>Location:</strong> {listing.location}</p>
                    <p><strong>Check-in:</strong> {booking.check_in_date}</p>
                    <p><strong>Check-out:</strong> {booking.check_out_date}</p>
                    <p><strong>Guests:</strong> {booking.num_guests}</p>
                </div>
                
                <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #155724;">Payment Information</h3>
                    <p><strong>Amount Paid:</strong> {payment.amount} {payment.currency}</p>
                    <p><strong>Payment ID:</strong> {payment.payment_id}</p>
                    <p><strong>Transaction Reference:</strong> {payment.chapa_tx_ref}</p>
                    <p><strong>Payment Date:</strong> {payment.paid_at or payment.updated_at}</p>
                </div>
                
                <p>If you have any questions, please contact us at 
                   <a href="mailto:{context['support_email']}">{context['support_email']}</a>
                </p>
                
                <p>Best regards,<br>ALX Travel App Team</p>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 10px; text-align: center; font-size: 12px; color: #6c757d;">
                <p>&copy; {context['current_year']} ALX Travel App. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send()
        
        logger.info(f"Payment confirmation email sent to {user.email} for payment {payment_id}")
        
        return f"Email sent successfully to {user.email}"
        
    except Exception as exc:
        logger.error(f"Failed to send payment confirmation email: {str(exc)}")
        # Retry the task
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def send_booking_confirmation_email(self, booking_id: int):
    """
    Send booking confirmation email to user
    
    Args:
        booking_id: Booking model ID
    """
    try:
        from .models import Booking
        
        booking = Booking.objects.select_related(
            'listing', 'user'
        ).get(id=booking_id)
        
        user = booking.user
        listing = booking.listing
        
        # Email context
        context = {
            'user': user,
            'booking': booking,
            'listing': listing,
            'company_name': 'ALX Travel App',
            'support_email': 'support@alxtravel.com',
            'current_year': timezone.now().year,
        }
        
        # Email subject and content
        subject = f'Booking Confirmation - #{booking.id}'
        
        # Plain text content
        text_content = f"""
        Dear {user.first_name or user.username},
        
        Your booking request has been received and is being processed.
        
        Booking Details:
        - Booking ID: #{booking.id}
        - Property: {listing.title}
        - Location: {listing.location}
        - Check-in: {booking.check_in_date}
        - Check-out: {booking.check_out_date}
        - Guests: {booking.num_guests}
        - Total Amount: {booking.total_price} ETB
        - Status: {booking.get_status_display()}
        
        Please complete your payment to confirm your reservation.
        
        If you have any questions, please contact us at {context['support_email']}.
        
        Best regards,
        ALX Travel App Team
        """
        
        # Send email
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )
        
        logger.info(f"Booking confirmation email sent to {user.email} for booking {booking_id}")
        
        return f"Email sent successfully to {user.email}"
        
    except Exception as exc:
        logger.error(f"Failed to send booking confirmation email: {str(exc)}")
        # Retry the task
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def send_payment_failed_email(self, payment_id: int):
    """
    Send payment failed notification email to user
    
    Args:
        payment_id: Payment model ID
    """
    try:
        from .models import Payment
        
        payment = Payment.objects.select_related(
            'booking', 'booking__listing', 'user'
        ).get(id=payment_id)
        
        user = payment.user
        booking = payment.booking
        listing = booking.listing
        
        # Email subject and content
        subject = f'Payment Failed - Booking #{booking.id}'
        
        # Plain text content
        text_content = f"""
        Dear {user.first_name or user.username},
        
        We're sorry to inform you that your payment for booking #{booking.id} was not successful.
        
        Booking Details:
        - Property: {listing.title}
        - Location: {listing.location}
        - Check-in: {booking.check_in_date}
        - Check-out: {booking.check_out_date}
        - Total Amount: {payment.amount} {payment.currency}
        
        Reason: {payment.failure_reason or 'Payment was declined or cancelled'}
        
        You can try again or contact us for assistance at support@alxtravel.com.
        
        Best regards,
        ALX Travel App Team
        """
        
        # Send email
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )
        
        logger.info(f"Payment failed email sent to {user.email} for payment {payment_id}")
        
        return f"Email sent successfully to {user.email}"
        
    except Exception as exc:
        logger.error(f"Failed to send payment failed email: {str(exc)}")
        # Retry the task
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
