# ALX Travel App - Database Models and API

This Django project implements a comprehensive travel booking system with database models for listings, bookings, and reviews.

## Overview

The project contains three main models:
- **Listing**: Travel accommodations with details and pricing
- **Booking**: User reservations for listings
- **Review**: User reviews and ratings for listings

## Models Structure

### Listing Model
- **Fields**: title, description, location, price_per_night, max_guests, bedrooms, bathrooms, amenities, availability, created_by, created_at, updated_at, is_active
- **Relationships**: One-to-many with Bookings and Reviews
- **Methods**: `average_rating` property to calculate average review rating

### Booking Model
- **Fields**: listing, user, check_in_date, check_out_date, num_guests, total_price, status, special_requests, created_at, updated_at
- **Status Choices**: pending, confirmed, cancelled, completed
- **Validation**: Prevents overlapping bookings, validates date ranges and guest capacity
- **Methods**: `duration_days` property to calculate booking length

### Review Model
- **Fields**: listing, user, booking, rating, comment, cleanliness_rating, accuracy_rating, location_rating, value_rating, created_at, updated_at
- **Constraints**: One review per user per listing
- **Validation**: Rating validation (1-5 scale)

## API Serializers

### ListingSerializer
- Full listing details with nested user information
- Includes calculated fields: `average_rating`, `reviews_count`
- Validation for price and guest capacity

### BookingSerializer
- Booking creation and management
- Automatic total price calculation
- Date and capacity validation
- Status management

### ReviewSerializer
- Review creation with rating validation
- Support for detailed category ratings
- Prevents duplicate reviews per user per listing

## Management Commands

### Seed Command
Populates the database with sample data for testing and development.

```bash
python manage.py seed --listings 20 --users 10 --bookings 30 --reviews 50
```

**Options:**
- `--listings N`: Number of sample listings to create (default: 20)
- `--users N`: Number of sample users to create (default: 10)
- `--bookings N`: Number of sample bookings to create (default: 30)
- `--reviews N`: Number of sample reviews to create (default: 50)
- `--clear`: Clear existing data before seeding

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirement.txt
   ```

2. **Create Migrations**
   ```bash
   python manage.py makemigrations
   ```

3. **Apply Migrations**
   ```bash
   python manage.py migrate
   ```

4. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

5. **Seed Database** (Optional)
   ```bash
   python manage.py seed
   ```

6. **Run Server**
   ```bash
   python manage.py runserver
   ```

## Key Features

### Models
- **Data Integrity**: Proper field validation and constraints
- **Relationships**: Well-defined foreign key relationships
- **Business Logic**: Custom validation methods and properties
- **Timestamps**: Automatic created_at and updated_at fields

### Serializers
- **Nested Serialization**: Related model data included in API responses
- **Validation**: Comprehensive field and cross-field validation
- **Read/Write Fields**: Proper separation of input and output fields
- **Calculated Fields**: Dynamic fields like ratings and counts

### Admin Interface
- **Custom Admin Classes**: Enhanced admin interface for all models
- **Filtering**: Advanced filtering options for listings, bookings, and reviews
- **Search**: Full-text search capabilities
- **Inline Editing**: Quick status and availability updates

### Sample Data
- **Realistic Data**: Diverse, realistic sample listings and bookings
- **Relationships**: Proper data relationships maintained
- **Variety**: Different property types, locations, and price ranges
- **Reviews**: Weighted realistic review ratings and comments

## Database Schema Highlights

### Constraints
- **Unique Constraints**: Prevent duplicate bookings and reviews
- **Check Constraints**: Ensure data validity (positive prices, valid dates)
- **Foreign Key Constraints**: Maintain referential integrity

### Indexes
- **Performance**: Automatic indexes on foreign keys and commonly queried fields
- **Ordering**: Default ordering for better user experience

### Validation
- **Model Level**: Clean methods for complex validation logic
- **Field Level**: Validators for individual field constraints
- **Serializer Level**: API-specific validation rules

## Files Structure

```
listings/
├── models.py              # Database models (Listing, Booking, Review)
├── serializers.py         # DRF serializers for API
├── admin.py              # Django admin configuration
├── management/
│   └── commands/
│       └── seed.py       # Database seeding command
└── migrations/           # Database migrations
```

## Testing the Implementation

1. **Access Admin Interface**: `/admin/` (use superuser credentials)
2. **View Sample Data**: Browse listings, bookings, and reviews
3. **Test Relationships**: Verify foreign key relationships work correctly
4. **API Testing**: Use DRF browsable API or tools like Postman

## Configuration Notes

- **Database**: Currently configured with SQLite for development
- **Settings**: Uses local_settings.py for development configuration
- **Dependencies**: All required packages listed in requirement.txt
- **Python Path**: Configured in manage.py for proper module resolution

This implementation provides a solid foundation for a travel booking application with proper data modeling, validation, and API serialization capabilities.
