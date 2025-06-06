from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Room(Base):
    __tablename__ = 'rooms'
    
    id = Column(Integer, primary_key=True)
    room_number = Column(String(10), unique=True, nullable=False)
    room_type = Column(String(50), nullable=False)
    rate = Column(Float, nullable=False)
    status = Column(String(20), default='available')  # available, occupied, maintenance
    bookings = relationship('Booking', back_populates='room')

class Guest(Base):
    __tablename__ = 'guests'
    
    id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True)
    phone = Column(String(20), nullable=False)  # Updated to be required
    address = Column(String(200))
    id_type = Column(String(50), nullable=False)  # Passport, National ID, etc.
    country = Column(String(100), nullable=False)  # Country of residence
    nationality = Column(String(100), nullable=False)  # Nationality
    date_of_birth = Column(DateTime, nullable=False)  # Date of Birth
    bookings = relationship('Booking', back_populates='guest')

class Booking(Base):
    __tablename__ = 'bookings'
    
    id = Column(Integer, primary_key=True)
    guest_id = Column(Integer, ForeignKey('guests.id'))
    room_id = Column(Integer, ForeignKey('rooms.id'))
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=False)
    total_amount = Column(Float)
    status = Column(String(20), default='pending')  # pending, confirmed, checked_in, completed, cancelled
    
    guest = relationship('Guest', back_populates='bookings')
    room = relationship('Room', back_populates='bookings')