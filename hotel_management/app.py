from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from main import HotelManagementSystem
from booking_engine import BookingEngine
from models import Room, Guest, Booking, RoomType, PaymentMethod, Payment
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
    if request.method == 'POST' and 'search' not in request.form:
        try:
            room_number = request.form['room_number']
            room_type_id = request.form['room_type_id']
            
            hotel.add_room(room_number, room_type_id)
            flash('Room added successfully!', 'success')
            
        except Exception as e:
            hotel.session.rollback()
            flash(f'Error adding room: {str(e)}', 'error')
            
        return redirect(url_for('rooms'))
    
    search_term = request.form.get('search_term') if request.method == 'POST' else request.args.get('search_term')
    if search_term:
        rooms = hotel.session.query(Room).join(RoomType).filter(
            or_(
                Room.room_number.ilike(f'%{search_term}%'),
                RoomType.type_name.ilike(f'%{search_term}%')
            )
        ).all()
    else:
        rooms = hotel.session.query(Room).all()
    
    room_types = hotel.session.query(RoomType).all()
    return render_template('rooms.html', rooms=rooms, room_types=room_types)

@app.route('/guests', methods=['GET', 'POST'])
def guests():
    # Add this list of countries
    countries = [
        {"code": "US", "name": "United States", "nationality": "American"},
        {"code": "GB", "name": "United Kingdom", "nationality": "British"},
        {"code": "FR", "name": "France", "nationality": "French"},
        {"code": "DE", "name": "Germany", "nationality": "German"},
        {"code": "IT", "name": "Italy", "nationality": "Italian"},
        {"code": "ES", "name": "Spain", "nationality": "Spanish"},
        {"code": "PT", "name": "Portugal", "nationality": "Portuguese"},
        {"code": "ID", "name": "Indonesia", "nationality": "Indonesian"},
        # Add more countries as needed
    ]
    
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
            try:
                # Get form data
                first_name = request.form['first_name']
                last_name = request.form['last_name']
                email = request.form['email']
                phone = request.form['phone']
                address = request.form['address']
                id_type = request.form['id_type']
                country = request.form['country']
                nationality = request.form['nationality']
                
                # Handle optional date_of_birth
                date_of_birth = None
                if request.form['date_of_birth']:
                    try:
                        date_of_birth = datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d')
                    except ValueError:
                        return jsonify({'success': False, 'error': 'Invalid date format'})
                
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
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
    
    # Get all guests for display
    guests = hotel.session.query(Guest).all()
    return render_template('guests.html', guests=guests, countries=countries)

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
    
    # Get all required data
    rooms = hotel.session.query(Room).all()
    guests = hotel.session.query(Guest).all()
    
    return render_template('bookings.html', 
                           bookings=bookings, 
                           rooms=rooms, 
                           guests=guests)

@app.route('/create_payment', methods=['POST'])
def create_payment():
    try:
        booking_id = request.form.get('booking_id')
        amount = request.form.get('amount')
        payment_method_id = request.form.get('payment_method_id')
        
        if not all([booking_id, amount, payment_method_id]):
            return jsonify({'success': False, 'error': 'Missing required fields'})
        
        # Create new payment
        payment = Payment(
            booking_id=booking_id,
            amount=amount,
            payment_method_id=payment_method_id,
            payment_date=datetime.utcnow(),
            status='completed'
        )
        
        hotel.session.add(payment)
        hotel.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        hotel.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

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
                    'title': str(room.room_number),
                    'start': date_str,
                    'end': date_str,
                    'color': status_colors.get(booking.status, '#6c757d'),
                    'extendedProps': {
                        'guest': f"{booking.guest.first_name} {booking.guest.last_name}",
                        'status': booking.status,
                        'room_type': room.room_type.type_name  # Changed from room.room_type
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
                        'room_type': room.room_type.type_name  # Changed from room.room_type
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
                'room_type': room.room_type.type_name,  # Changed from room.room_type to room.room_type.type_name
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

@app.route('/guests/<int:guest_id>', methods=['GET', 'PUT'])
def get_guest(guest_id):
    try:
        guest = hotel.session.query(Guest).get(guest_id)
        if not guest:
            return jsonify({'error': 'Guest not found'}), 404

        if request.method == 'GET':
            return jsonify({
                'id': guest.id,
                'first_name': guest.first_name or 'N/A',
                'last_name': guest.last_name or 'N/A',
                'email': guest.email or 'N/A',
                'phone': guest.phone or 'N/A',
                'id_type': guest.id_type or 'N/A',
                'country': guest.country or 'N/A',
                'nationality': guest.nationality or 'N/A',
                'date_of_birth': guest.date_of_birth.strftime('%Y-%m-%d') if guest.date_of_birth else 'N/A',
                'address': guest.address or 'N/A'
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            guest.first_name = data.get('first_name')
            guest.last_name = data.get('last_name')
            guest.email = data.get('email')
            guest.phone = data.get('phone')
            guest.id_type = data.get('id_type')
            guest.country = data.get('country')
            guest.nationality = data.get('nationality')
            guest.address = data.get('address')
            
            if date_str := data.get('date_of_birth'):
                try:
                    guest.date_of_birth = datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    guest.date_of_birth = None
            else:
                guest.date_of_birth = None
            
            hotel.session.commit()
            return jsonify({'success': True, 'message': 'Guest updated successfully'})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/guests/data')
def get_guests_data():
    guests = Guest.query.all()
    return jsonify([{
        'id': guest.id,
        'first_name': guest.first_name,
        'last_name': guest.last_name,
        'email': guest.email,
        'phone': guest.phone,
        'id_type': guest.id_type,
        'country': guest.country,
        'nationality': guest.nationality
    } for guest in guests])

# Add these imports at the top if not already present
from models import RoomType

# Add these routes
@app.route('/room_types', methods=['GET', 'POST'])
def room_types():
    if request.method == 'POST':
        try:
            room_type_id = request.form.get('room_type_id')
            type_name = request.form['type_name']
            description = request.form['description']
            base_price = float(request.form['base_price'])
            max_guest = int(request.form['max_guest'])
            
            if room_type_id:  # Update existing room type
                room_type = hotel.session.query(RoomType).get(room_type_id)
                if room_type:
                    room_type.type_name = type_name
                    room_type.description = description
                    room_type.base_price = base_price
                    room_type.max_guest = max_guest
                    flash('Room type updated successfully!', 'success')
            else:  # Create new room type
                room_type = RoomType(
                    type_name=type_name,
                    description=description,
                    base_price=base_price,
                    max_guest=max_guest
                )
                hotel.session.add(room_type)
                flash('Room type added successfully!', 'success')
                
            hotel.session.commit()
            
        except Exception as e:
            hotel.session.rollback()
            flash(f'Error: {str(e)}', 'error')
            
        return redirect(url_for('room_types'))
    
    room_types = hotel.session.query(RoomType).all()
    return render_template('room_types.html', room_types=room_types)

@app.route('/room_types/<int:id>', methods=['DELETE'])
def delete_room_type(id):
    try:
        room_type = hotel.session.query(RoomType).get(id)
        if room_type:
            hotel.session.delete(room_type)
            hotel.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Room type not found'}), 404
    except Exception as e:
        hotel.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/payment_methods', methods=['GET', 'POST'])
def payment_methods():
    if request.method == 'POST':
        if 'search' in request.form:
            search_term = request.form['search_term']
            payment_methods = hotel.session.query(PaymentMethod).filter(
                or_(
                    PaymentMethod.name.ilike(f'%{search_term}%'),
                    PaymentMethod.code.ilike(f'%{search_term}%'),
                    PaymentMethod.description.ilike(f'%{search_term}%')
                )
            ).all()
        else:
            try:
                method_id = request.form.get('method_id')
                name = request.form['name']
                code = request.form['code']
                description = request.form['description']
                
                if method_id:  # Update existing
                    method = hotel.session.query(PaymentMethod).get(method_id)
                    if method:
                        method.name = name
                        method.code = code
                        method.description = description
                        flash('Payment method updated successfully!', 'success')
                else:  # Create new
                    method = PaymentMethod(
                        name=name,
                        code=code,
                        description=description
                    )
                    hotel.session.add(method)
                    flash('Payment method added successfully!', 'success')
                
                hotel.session.commit()
            except Exception as e:
                hotel.session.rollback()
                flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('payment_methods'))
    
    payment_methods = hotel.session.query(PaymentMethod).all()
    return render_template('payment_methods.html', payment_methods=payment_methods)

@app.route('/payment_methods/<int:method_id>', methods=['GET'])
def get_payment_method(method_id):
    method = hotel.session.query(PaymentMethod).get(method_id)
    if not method:
        return jsonify({'error': 'Payment method not found'}), 404
    
    return jsonify({
        'id': method.id,
        'name': method.name,
        'code': method.code,
        'description': method.description
    })

@app.route('/payment_methods/<int:method_id>/toggle', methods=['POST'])
def toggle_payment_method(method_id):
    method = hotel.session.query(PaymentMethod).get(method_id)
    if method:
        method.is_active = not method.is_active
        hotel.session.commit()
        flash('Payment method status updated successfully!', 'success')
    else:
        flash('Payment method not found!', 'error')
    return redirect(url_for('payment_methods'))

if __name__ == '__main__':
    app.run(debug=True)