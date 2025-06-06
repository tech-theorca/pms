from main import HotelManagementSystem
from datetime import datetime, timedelta

# Initialize the system
hotel = HotelManagementSystem()

# Add a room
room = hotel.add_room('101', 'Standard', 100.0)

# Add a guest
guest = hotel.add_guest(
    'John', 'Doe',
    'john@example.com',
    '1234567890',
    '123 Main St',
    'passport',
    'United States',
    'American',
    datetime(1990, 1, 1)  # Example date of birth
)

# Create a booking
check_in = datetime.now()
check_out = check_in + timedelta(days=2)
booking = hotel.create_booking(guest.id, room.id, check_in, check_out)

# Check in the guest
hotel.check_in_guest(booking.id)

# Check out the guest
hotel.check_out_guest(booking.id)