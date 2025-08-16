"""
Management command to seed the database with sample travel listings data
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import random

from listings.models import Listing, Booking, Review


class Command(BaseCommand):
    help = 'Seed the database with sample travel listings, bookings, and reviews'

    def add_arguments(self, parser):
        parser.add_argument(
            '--listings',
            type=int,
            default=20,
            help='Number of sample listings to create (default: 20)',
        )
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Number of sample users to create (default: 10)',
        )
        parser.add_argument(
            '--bookings',
            type=int,
            default=30,
            help='Number of sample bookings to create (default: 30)',
        )
        parser.add_argument(
            '--reviews',
            type=int,
            default=50,
            help='Number of sample reviews to create (default: 50)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Review.objects.all().delete()
            Booking.objects.all().delete()
            Listing.objects.all().delete()
            # Keep superuser and admin users, delete others
            User.objects.filter(is_superuser=False, is_staff=False).delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared.'))

        # Create sample users
        users_count = options['users']
        listings_count = options['listings']
        bookings_count = options['bookings']
        reviews_count = options['reviews']

        self.stdout.write(f'Creating {users_count} sample users...')
        users = self.create_sample_users(users_count)

        self.stdout.write(f'Creating {listings_count} sample listings...')
        listings = self.create_sample_listings(listings_count, users)

        self.stdout.write(f'Creating {bookings_count} sample bookings...')
        bookings = self.create_sample_bookings(bookings_count, users, listings)

        self.stdout.write(f'Creating {reviews_count} sample reviews...')
        reviews = self.create_sample_reviews(reviews_count, users, listings, bookings)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded database with:\n'
                f'  - {len(users)} users\n'
                f'  - {len(listings)} listings\n'
                f'  - {len(bookings)} bookings\n'
                f'  - {len(reviews)} reviews'
            )
        )

    def create_sample_users(self, count):
        """Create sample users"""
        users = []
        first_names = [
            'John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'Robert', 'Jessica',
            'William', 'Ashley', 'James', 'Amanda', 'Christopher', 'Melissa', 'Daniel'
        ]
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
            'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzales'
        ]

        for i in range(count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            username = f"{first_name.lower()}{last_name.lower()}{i+1}"
            email = f"{username}@example.com"

            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password='samplepass123'
                )
                users.append(user)

        return users

    def create_sample_listings(self, count, users):
        """Create sample travel listings"""
        listings = []
        
        # Sample data for listings
        listing_data = [
            {
                'title': 'Cozy Downtown Apartment',
                'location': 'New York, NY',
                'description': 'A comfortable apartment in the heart of Manhattan with modern amenities and city views.',
                'price': 150.00,
                'bedrooms': 1,
                'bathrooms': 1,
                'max_guests': 2,
                'amenities': 'WiFi, Kitchen, Air Conditioning, TV, Heating'
            },
            {
                'title': 'Beachfront Villa',
                'location': 'Malibu, CA',
                'description': 'Stunning beachfront villa with private beach access and panoramic ocean views.',
                'price': 450.00,
                'bedrooms': 4,
                'bathrooms': 3,
                'max_guests': 8,
                'amenities': 'WiFi, Kitchen, Pool, Beach Access, Parking, BBQ'
            },
            {
                'title': 'Mountain Cabin Retreat',
                'location': 'Aspen, CO',
                'description': 'Rustic mountain cabin perfect for skiing and outdoor adventures.',
                'price': 280.00,
                'bedrooms': 3,
                'bathrooms': 2,
                'max_guests': 6,
                'amenities': 'WiFi, Fireplace, Kitchen, Parking, Mountain Views'
            },
            {
                'title': 'Historic Brownstone',
                'location': 'Boston, MA',
                'description': 'Beautiful historic brownstone in Back Bay with original details and modern updates.',
                'price': 225.00,
                'bedrooms': 2,
                'bathrooms': 2,
                'max_guests': 4,
                'amenities': 'WiFi, Kitchen, Historic Charm, Central Location'
            },
            {
                'title': 'Modern Loft in Arts District',
                'location': 'Los Angeles, CA',
                'description': 'Trendy loft in the vibrant Arts District with industrial design and city views.',
                'price': 190.00,
                'bedrooms': 1,
                'bathrooms': 1,
                'max_guests': 3,
                'amenities': 'WiFi, Kitchen, Air Conditioning, City Views, Art Galleries Nearby'
            },
            {
                'title': 'Lakeside Cottage',
                'location': 'Lake Tahoe, CA',
                'description': 'Charming lakeside cottage with private dock and stunning mountain views.',
                'price': 320.00,
                'bedrooms': 2,
                'bathrooms': 1,
                'max_guests': 4,
                'amenities': 'WiFi, Kitchen, Lake Access, Dock, Mountain Views, Kayaks'
            },
            {
                'title': 'Urban Studio',
                'location': 'Chicago, IL',
                'description': 'Modern studio apartment in downtown Chicago, perfect for business travelers.',
                'price': 120.00,
                'bedrooms': 1,
                'bathrooms': 1,
                'max_guests': 2,
                'amenities': 'WiFi, Kitchen, Gym Access, Business Center'
            },
            {
                'title': 'Luxury Penthouse',
                'location': 'Miami, FL',
                'description': 'Stunning penthouse with rooftop terrace and panoramic city and ocean views.',
                'price': 600.00,
                'bedrooms': 3,
                'bathrooms': 3,
                'max_guests': 6,
                'amenities': 'WiFi, Kitchen, Pool, Gym, Concierge, Ocean Views, Rooftop Terrace'
            },
            {
                'title': 'Desert Oasis',
                'location': 'Scottsdale, AZ',
                'description': 'Beautiful desert retreat with pool, spa, and stunning sunset views.',
                'price': 375.00,
                'bedrooms': 3,
                'bathrooms': 2,
                'max_guests': 6,
                'amenities': 'WiFi, Kitchen, Pool, Spa, Desert Views, Parking'
            },
            {
                'title': 'Vintage Airstream',
                'location': 'Austin, TX',
                'description': 'Unique vintage Airstream trailer in a trendy Austin neighborhood.',
                'price': 85.00,
                'bedrooms': 1,
                'bathrooms': 1,
                'max_guests': 2,
                'amenities': 'WiFi, Kitchenette, Unique Experience, Central Location'
            }
        ]

        # Create listings using the sample data and random variations
        for i in range(count):
            base_listing = listing_data[i % len(listing_data)]
            user = random.choice(users)
            
            # Add some random variation to prices and guest capacity
            price_variation = random.uniform(0.8, 1.3)
            price = Decimal(str(round(base_listing['price'] * price_variation, 2)))
            
            listing = Listing.objects.create(
                title=f"{base_listing['title']} #{i+1}" if i >= len(listing_data) else base_listing['title'],
                description=base_listing['description'],
                location=base_listing['location'],
                price_per_night=price,
                bedrooms=base_listing['bedrooms'],
                bathrooms=base_listing['bathrooms'],
                max_guests=base_listing['max_guests'],
                amenities=base_listing['amenities'],
                created_by=user,
                availability=random.choice([True, True, True, False])  # 75% available
            )
            listings.append(listing)

        return listings

    def create_sample_bookings(self, count, users, listings):
        """Create sample bookings"""
        bookings = []
        booking_statuses = ['pending', 'confirmed', 'cancelled', 'completed']
        
        for _ in range(count):
            user = random.choice(users)
            listing = random.choice(listings)
            
            # Generate random dates
            start_date = timezone.now().date() + timedelta(days=random.randint(-30, 90))
            duration = random.randint(2, 14)  # 2-14 days
            end_date = start_date + timedelta(days=duration)
            
            # Ensure we don't exceed max guests
            num_guests = random.randint(1, min(listing.max_guests, 4))
            
            # Calculate total price
            total_price = listing.price_per_night * duration
            
            # Random status
            status = random.choice(booking_statuses)
            
            # Special requests (sometimes)
            special_requests = ""
            if random.choice([True, False, False]):  # 33% chance
                requests = [
                    "Late check-in requested",
                    "Extra towels needed",
                    "Celebrating anniversary",
                    "Business trip - quiet space needed",
                    "Traveling with pet"
                ]
                special_requests = random.choice(requests)
            
            try:
                booking = Booking.objects.create(
                    listing=listing,
                    user=user,
                    check_in_date=start_date,
                    check_out_date=end_date,
                    num_guests=num_guests,
                    total_price=total_price,
                    status=status,
                    special_requests=special_requests
                )
                bookings.append(booking)
            except Exception as e:
                # Skip if there's a unique constraint violation
                continue

        return bookings

    def create_sample_reviews(self, count, users, listings, bookings):
        """Create sample reviews"""
        reviews = []
        
        review_comments = [
            "Amazing stay! The place was exactly as described and the host was very responsive.",
            "Great location and clean apartment. Would definitely book again.",
            "Beautiful views and comfortable accommodations. Highly recommended!",
            "Perfect for a weekend getaway. The amenities were excellent.",
            "Lovely place with great attention to detail. Thanks for a wonderful stay!",
            "Good value for money. The listing was accurate and check-in was smooth.",
            "Outstanding hospitality and a gorgeous property. 5 stars!",
            "Clean, comfortable, and well-equipped. Great communication from the host.",
            "Fantastic location with easy access to all the main attractions.",
            "Wonderful stay! The place exceeded our expectations in every way.",
            "Decent stay but could use some updates. Overall acceptable.",
            "Nice place but a bit smaller than expected. Good for a short stay.",
        ]
        
        created_reviews = 0
        attempts = 0
        max_attempts = count * 3  # Prevent infinite loop
        
        while created_reviews < count and attempts < max_attempts:
            attempts += 1
            user = random.choice(users)
            listing = random.choice(listings)
            
            # Check if user already reviewed this listing
            if Review.objects.filter(user=user, listing=listing).exists():
                continue
            
            # Find a completed booking for more realistic reviews
            booking = None
            user_bookings = Booking.objects.filter(
                user=user, 
                listing=listing, 
                status='completed'
            ).first()
            
            if user_bookings and random.choice([True, False]):
                booking = user_bookings
            
            # Generate ratings
            rating = random.choices([1, 2, 3, 4, 5], weights=[2, 3, 10, 35, 50])[0]  # Weighted towards higher ratings
            
            # Generate detailed ratings (sometimes)
            cleanliness = random.randint(rating-1, 5) if rating > 1 else rating
            accuracy = random.randint(rating-1, 5) if rating > 1 else rating
            location_rating = random.randint(rating-1, 5) if rating > 1 else rating
            value = random.randint(rating-1, 5) if rating > 1 else rating
            
            comment = random.choice(review_comments)
            
            try:
                review = Review.objects.create(
                    listing=listing,
                    user=user,
                    booking=booking,
                    rating=rating,
                    comment=comment,
                    cleanliness_rating=cleanliness if random.choice([True, False]) else None,
                    accuracy_rating=accuracy if random.choice([True, False]) else None,
                    location_rating=location_rating if random.choice([True, False]) else None,
                    value_rating=value if random.choice([True, False]) else None,
                )
                reviews.append(review)
                created_reviews += 1
            except Exception as e:
                # Skip if there's a unique constraint violation or other error
                continue

        return reviews
