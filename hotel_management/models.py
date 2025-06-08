from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, DECIMAL, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class RoomType(Base):
    __tablename__ = 'room_types'
    
    id = Column(Integer, primary_key=True)
    type_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    base_price = Column(DECIMAL(10,2), nullable=False)
    max_guest = Column(Integer, nullable=False)
    rooms = relationship('Room', back_populates='room_type')

class Room(Base):
    __tablename__ = 'rooms'
    
    id = Column(Integer, primary_key=True)
    room_number = Column(String(10), unique=True, nullable=False)
    room_type_id = Column(Integer, ForeignKey('room_types.id'), nullable=False)
    rate = Column(Float, nullable=False)
    status = Column(String(20), default='available')  # available, occupied, maintenance
    
    room_type = relationship('RoomType', back_populates='rooms')
    bookings = relationship('Booking', back_populates='room')

class Guest(Base):
    __tablename__ = 'guests'
    
    id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    phone = Column(String(20), nullable=False)
    address = Column(String(200), nullable=True)
    id_type = Column(String(50), nullable=True)
    country = Column(String(100), nullable=True)
    nationality = Column(String(100), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
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