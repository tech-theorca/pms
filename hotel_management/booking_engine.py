from datetime import datetime
from sqlalchemy import and_, not_
from models import Room, Booking
from time import sleep

class BookingEngine:
    def __init__(self, hotel_system):
        self.hotel = hotel_system
        self.max_retries = 3
        self.retry_delay = 1  # seconds

    def _execute_with_retry(self, operation):
        retries = 0
        while retries < self.max_retries:
            try:
                self.hotel.refresh_session()
                result = operation()
                self.hotel.session.commit()
                return result
            except Exception as e:
                retries += 1
                if retries == self.max_retries:
                    self.hotel.session.rollback()
                    raise e
                sleep(self.retry_delay * retries)  # Exponential backoff
                continue

    def check_room_availability(self, check_in: datetime, check_out: datetime):
        def _check_availability():
            # Get all rooms that are not booked for the given date range
            booked_room_ids = self.hotel.session.query(Booking.room_id).filter(
                and_(
                    Booking.status.in_(['pending', 'confirmed', 'checked_in']),
                    Booking.check_out > check_in,
                    Booking.check_in < check_out
                )
            ).all()

            # Convert results to a list of IDs
            booked_ids = [room_id for (room_id,) in booked_room_ids]

            # Query available rooms
            available_rooms = self.hotel.session.query(Room)
            if booked_ids:
                available_rooms = available_rooms.filter(~Room.id.in_(booked_ids))
            
            return available_rooms.all()

        return self._execute_with_retry(_check_availability)

    def create_booking(self, guest_id: int, room_id: int, check_in: datetime, check_out: datetime):
        def _create_booking():
            # Check if room is available
            available_rooms = self.check_room_availability(check_in, check_out)
            if not any(room.id == room_id for room in available_rooms):
                raise ValueError("Room is not available for the selected dates")

            # Create new booking
            booking = Booking(
                guest_id=guest_id,
                room_id=room_id,
                check_in=check_in,
                check_out=check_out,
                status='pending'
            )
            self.hotel.session.add(booking)
            return booking

        return self._execute_with_retry(_create_booking)