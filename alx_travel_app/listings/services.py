"""
Chapa Payment Gateway Service

This module provides integration with the Chapa Payment Gateway API
for initiating and verifying payments.
"""

import requests
import logging
from decimal import Decimal
from typing import Dict, Optional, Any
from django.conf import settings
from django.utils import timezone


logger = logging.getLogger(__name__)


class ChapaPaymentError(Exception):
    """Custom exception for Chapa payment errors"""
    pass


class ChapaPaymentService:
    """
    Service class for integrating with Chapa Payment Gateway
    """
    
    def __init__(self):
        self.secret_key = settings.CHAPA_SECRET_KEY
        self.public_key = settings.CHAPA_PUBLIC_KEY
        self.base_url = settings.CHAPA_BASE_URL
        
        if not self.secret_key:
            raise ChapaPaymentError("CHAPA_SECRET_KEY not configured")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers for Chapa API"""
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make HTTP request to Chapa API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request payload
            
        Returns:
            API response data
            
        Raises:
            ChapaPaymentError: If request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        
        try:
            logger.info(f"Making {method} request to {url}")
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=data, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            else:
                raise ChapaPaymentError(f"Unsupported HTTP method: {method}")
            
            logger.info(f"Response status: {response.status_code}")
            
            # Parse response
            try:
                response_data = response.json()
            except ValueError:
                logger.error(f"Invalid JSON response: {response.text}")
                raise ChapaPaymentError("Invalid response from payment gateway")
            
            # Check for success
            if response.status_code not in [200, 201]:
                error_message = response_data.get('message', 'Unknown error occurred')
                logger.error(f"API error: {error_message}")
                raise ChapaPaymentError(f"Payment gateway error: {error_message}")
            
            return response_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise ChapaPaymentError(f"Failed to connect to payment gateway: {str(e)}")
    
    def initialize_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize payment with Chapa
        
        Args:
            payment_data: Payment initialization data
            
        Returns:
            Payment initialization response
        """
        endpoint = "/transaction/initialize"
        
        # Validate required fields
        required_fields = ['amount', 'currency', 'email', 'first_name', 'last_name', 'tx_ref']
        for field in required_fields:
            if field not in payment_data:
                raise ChapaPaymentError(f"Missing required field: {field}")
        
        # Ensure amount is string format for Chapa
        payment_data['amount'] = str(payment_data['amount'])
        
        logger.info(f"Initializing payment for tx_ref: {payment_data['tx_ref']}")
        
        response = self._make_request('POST', endpoint, payment_data)
        
        if response.get('status') == 'success':
            return response.get('data', {})
        else:
            error_msg = response.get('message', 'Payment initialization failed')
            raise ChapaPaymentError(error_msg)
    
    def verify_payment(self, tx_ref: str) -> Dict[str, Any]:
        """
        Verify payment status with Chapa
        
        Args:
            tx_ref: Transaction reference
            
        Returns:
            Payment verification response
        """
        endpoint = f"/transaction/verify/{tx_ref}"
        
        logger.info(f"Verifying payment for tx_ref: {tx_ref}")
        
        response = self._make_request('GET', endpoint)
        
        if response.get('status') == 'success':
            return response.get('data', {})
        else:
            error_msg = response.get('message', 'Payment verification failed')
            raise ChapaPaymentError(error_msg)
    
    def get_payment_status(self, verification_data: Dict[str, Any]) -> str:
        """
        Get standardized payment status from Chapa verification data
        
        Args:
            verification_data: Chapa verification response data
            
        Returns:
            Standardized payment status
        """
        chapa_status = verification_data.get('status', '').lower()
        
        status_mapping = {
            'success': 'completed',
            'pending': 'processing',
            'failed': 'failed',
            'cancelled': 'cancelled',
        }
        
        return status_mapping.get(chapa_status, 'failed')
    
    def create_payment_payload(self, payment, user, booking, callback_url: str = None, 
                             return_url: str = None) -> Dict[str, Any]:
        """
        Create payment payload for Chapa initialization
        
        Args:
            payment: Payment model instance
            user: User model instance
            booking: Booking model instance
            callback_url: Webhook callback URL
            return_url: User return URL after payment
            
        Returns:
            Payment payload for Chapa API
        """
        # Generate transaction reference if not exists
        tx_ref = payment.generate_tx_ref()
        
        payload = {
            'amount': str(payment.amount),
            'currency': payment.currency,
            'email': user.email,
            'first_name': user.first_name or user.username,
            'last_name': user.last_name or '',
            'phone_number': getattr(user, 'phone_number', ''),
            'tx_ref': tx_ref,
            'callback_url': callback_url,
            'return_url': return_url,
            'customization': {
                'title': 'ALX Travel App',
                'description': f'Payment for booking #{booking.id} - {booking.listing.title}',
                'logo': None,  # You can add your logo URL here
            },
            'meta': {
                'booking_id': booking.id,
                'user_id': user.id,
                'listing_id': booking.listing.id,
            }
        }
        
        # Remove empty values
        return {k: v for k, v in payload.items() if v is not None and v != ''}
