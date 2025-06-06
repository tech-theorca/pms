from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from main import HotelManagementSystem
from booking_engine import BookingEngine
from models import Room, Guest, Booking
from datetime import datetime, timedelta
from sqlalchemy import or_
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Initialize the hotel management system
hotel = HotelManagementSystem()

# Initialize booking engine with the hotel system
booking_engine = BookingEngine(hotel)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/rooms', methods=['GET', 'POST'])
def rooms():
    if request.method == 'POST':
        try:
            room_number = request.form['room_number']
            room_type = request.form['room_type']
            rate = request.form['rate']
            
            hotel.add_room(room_number, room_type, rate)
            flash('Room added successfully!', 'success')
            
        except Exception as e:
            # Roll back the session on error
            hotel.session.rollback()  # Changed from db.session to hotel.session
            flash(f'Error adding room: {str(e)}', 'error')
            
        return redirect(url_for('rooms'))
    
    if 'search' in request.form:
        search_term = request.form['search_term']
        rooms = hotel.session.query(Room).filter(
            or_(
                Room.room_number.ilike(f'%{search_term}%'),
                Room.room_type.ilike(f'%{search_term}%')
            )
        ).all()
    else:
        rooms = hotel.session.query(Room).all()
    return render_template('rooms.html', rooms=rooms)

@app.route('/guests', methods=['GET', 'POST'])
def guests():
    if request.method == 'POST':
        if 'search' in request.form:
            search_term = request.form['search_term']
            guests = hotel.session.query(Guest).filter(
                or_(
                    Guest.first_name.ilike(f'%{search_term}%'),
                    Guest.last_name.ilike(f'%{search_term}%'),
                    Guest.email.ilike(f'%{search_term}%'),
                    Guest.phone.ilike(f'%{search_term}%'),
                    Guest.nationality.ilike(f'%{search_term}%'),
                    Guest.country.ilike(f'%{search_term}%')
                )
            ).all()
        else:
            # Get form data
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            phone = request.form['phone']
            address = request.form['address']
            id_type = request.form['id_type']
            country = request.form['country']
            nationality = request.form['nationality']
            date_of_birth = datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d')
            
            try:
                # Create new guest with all fields
                guest = hotel.add_guest(
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
                flash('Guest added successfully!', 'success')
            except Exception as e:
                flash(f'Error adding guest: {str(e)}', 'error')
            guests = hotel.session.query(Guest).all()
    else:
        guests = hotel.session.query(Guest).all()
    return render_template('guests.html', guests=guests)

@app.route('/bookings', methods=['GET', 'POST'])
def bookings():
    if request.method == 'POST':
        if 'search' in request.form:
            search_term = request.form['search_term']
            bookings = hotel.session.query(Booking).join(Guest).filter(
                or_(
                    Guest.first_name.ilike(f'%{search_term}%'),
                    Guest.last_name.ilike(f'%{search_term}%'),
                    Booking.status.ilike(f'%{search_term}%')
                )
            ).all()
        else:
            guest_id = int(request.form['guest_id'])
            room_id = int(request.form['room_id'])
            check_in = datetime.strptime(request.form['check_in'], '%Y-%m-%d')
            check_out = datetime.strptime(request.form['check_out'], '%Y-%m-%d')
            try:
                hotel.create_booking(guest_id, room_id, check_in, check_out)
                flash('Booking created successfully!', 'success')
            except Exception as e:
                flash(f'Error creating booking: {str(e)}', 'error')
            bookings = hotel.session.query(Booking).all()
    else:
        bookings = hotel.session.query(Booking).all()
    # Get all rooms instead of just 'available' ones
    rooms = hotel.session.query(Room).all()
    guests = hotel.session.query(Guest).all()
    return render_template('bookings.html', bookings=bookings, rooms=rooms, guests=guests)

@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

@app.route('/api/bookings')
def get_bookings():
    rooms = hotel.session.query(Room).all()
    bookings = hotel.session.query(Booking).all()
    events = []
    
    booking_lookup = {}
    for booking in bookings:
        for date in (booking.check_in + timedelta(n) for n in range((booking.check_out - booking.check_in).days)):
            date_str = date.strftime('%Y-%m-%d')
            if date_str not in booking_lookup:
                booking_lookup[date_str] = {}
            booking_lookup[date_str][booking.room.room_number] = booking
    
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for day in range(60):
        current_date = start_date + timedelta(days=day)
        date_str = current_date.strftime('%Y-%m-%d')
        
        for room in rooms:
            booking = booking_lookup.get(date_str, {}).get(room.room_number)
            if booking:
                status_colors = {
                    'pending': '#ffc107',
                    'confirmed': '#28a745',
                    'checked_in': '#007bff',
                    'cancelled': '#dc3545',
                    'completed': '#6f42c1'
                }
                events.append({
                    'title': str(room.room_number),  # Just show room number
                    'start': date_str,
                    'end': date_str,
                    'color': status_colors.get(booking.status, '#6c757d'),
                    'extendedProps': {
                        'guest': f"{booking.guest.first_name} {booking.guest.last_name}",
                        'status': booking.status,
                        'room_type': room.room_type
                    }
                })
            else:
                events.append({
                    'title': str(room.room_number),
                    'start': date_str,
                    'end': date_str,
                    'color': '#ffffff',
                    'textColor': '#666666',
                    'extendedProps': {
                        'status': 'available',
                        'room_type': room.room_type
                    }
                })
    
    return jsonify(events)

@app.route('/update_booking_status/<int:booking_id>', methods=['POST'])
def update_booking_status(booking_id):
    new_status = request.form['status']
    booking = hotel.session.query(Booking).get(booking_id)
    if booking:
        booking.status = new_status
        hotel.session.commit()
        flash('Booking status updated successfully!', 'success')
    else:
        flash('Booking not found!', 'error')
    return redirect(url_for('bookings'))

@app.route('/check_room_number', methods=['POST'])
def check_room_number():
    room_number = request.form.get('room_number')
    existing_room = hotel.session.query(Room).filter_by(room_number=room_number).first()
    return jsonify({'exists': existing_room is not None})

@app.route('/check_room_availability', methods=['POST'])
def check_room_availability():
    try:
        # Validate input data
        if not request.form.get('check_in') or not request.form.get('check_out'):
            return jsonify({
                'error': 'Check-in and check-out dates are required'
            }), 400

        try:
            check_in = datetime.strptime(request.form['check_in'], '%Y-%m-%d')
            check_out = datetime.strptime(request.form['check_out'], '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'error': 'Invalid date format. Please use YYYY-MM-DD'
            }), 400
        
        # Ensure dates are valid
        if check_in >= check_out:
            return jsonify({
                'error': 'Check-in date must be before check-out date'
            }), 400

        if check_in < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
            return jsonify({
                'error': 'Check-in date cannot be in the past'
            }), 400

        # Attempt to get available rooms
        available_rooms = booking_engine.check_room_availability(check_in, check_out)
        
        return jsonify({
            'success': True,
            'available_rooms': [{
                'id': room.id,
                'room_number': room.room_number,
                'room_type': room.room_type,
                'rate': float(room.rate)
            } for room in available_rooms]
        })
    except Exception as e:
        print(f"Room availability check error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error fetching available rooms. Please try again.',
            'details': str(e) if app.debug else None
        }), 500

if __name__ == '__main__':
    app.run(debug=True)