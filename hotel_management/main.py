from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Room, Guest, Booking
from dotenv import load_dotenv
import os

load_dotenv()

class HotelManagementSystem:
    def __init__(self):
        # Create MySQL connection URL
        db_url = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
        self.engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=3600,  # Recycle connections every hour
            pool_size=10,       # Maximum number of connections in the pool
            max_overflow=20,    # Maximum number of connections that can be created beyond pool_size
            pool_timeout=30,    # Timeout for getting a connection from the pool
            connect_args={
                'connect_timeout': 30,
                'read_timeout': 120,
                'write_timeout': 120
            }
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.refresh_session()

    def refresh_session(self):
        if hasattr(self, 'session'):
            self.session.close()
        self.session = self.Session()

    def add_room(self, room_number, room_type, rate):
        try:
            room = Room(room_number=room_number, room_type=room_type, rate=rate)
            self.session.add(room)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise e

    def add_guest(self, first_name, last_name, email, phone, address, id_type, country, nationality, date_of_birth):
        guest = Guest(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
            id_type=id_type,
            country=country,
            nationality=nationality,
            date_of_birth=date_of_birth
        )
        self.session.add(guest)
        self.session.commit()
        return guest

    def create_booking(self, guest_id, room_id, check_in, check_out):
        # Get the room
        room = self.session.query(Room).get(room_id)
        if not room:
            raise ValueError("Room not found")

        # Check if room is available for the requested dates
        existing_booking = self.session.query(Booking).filter(
            Booking.room_id == room_id,
            Booking.status.in_(['pending', 'confirmed', 'checked_in']),
            # Check if there's any overlap with existing bookings
            Booking.check_in < check_out,
            Booking.check_out > check_in
        ).first()

        if existing_booking:
            raise ValueError(f"Room {room.room_number} is not available for the selected dates")

        booking = Booking(
            guest_id=guest_id,
            room_id=room_id,
            check_in=check_in,
            check_out=check_out,
            status='pending'
        )
        
        # Calculate total amount
        days = (check_out - check_in).days
        booking.total_amount = days * room.rate

        self.session.add(booking)
        self.session.commit()
        return booking

    def get_available_rooms(self):
        return self.session.query(Room).filter_by(status='available').all()

    def check_in_guest(self, booking_id):
        booking = self.session.query(Booking).get(booking_id)
        if booking:
            booking.status = 'checked_in'
            booking.room.status = 'occupied'
            self.session.commit()
            return True
        return False

    def check_out_guest(self, booking_id):
        booking = self.session.query(Booking).get(booking_id)
        if booking:
            booking.status = 'completed'
            booking.room.status = 'available'
            self.session.commit()
            return True
        return False