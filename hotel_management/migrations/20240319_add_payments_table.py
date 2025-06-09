from sqlalchemy import create_engine, text

def upgrade(engine):
    conn = engine.connect()
    trans = conn.begin()
    try:
        # Create payment_methods table
        conn.execute(text('''
        CREATE TABLE payment_methods (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            code VARCHAR(20) NOT NULL UNIQUE,
            is_active BOOLEAN DEFAULT TRUE,
            description VARCHAR(200)
        );
        '''))

        # Insert default payment methods
        conn.execute(text('''
        INSERT INTO payment_methods (name, code, description) VALUES
            ('Cash', 'cash', 'Cash payment'),
            ('Credit Card', 'credit_card', 'Credit card payment'),
            ('Online Transfer', 'online', 'Online bank transfer'),
            ('Other', 'other', 'Other payment methods');
        '''))

        # Create payments table
        conn.execute(text('''
        CREATE TABLE payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            booking_id INT NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            payment_method_id INT NOT NULL,
            payment_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status ENUM('pending', 'completed', 'failed') NOT NULL DEFAULT 'pending',
            FOREIGN KEY (booking_id) REFERENCES bookings(id),
            FOREIGN KEY (payment_method_id) REFERENCES payment_methods(id)
        );
        '''))
        trans.commit()
    except:
        trans.rollback()
        raise
    finally:
        conn.close()

def downgrade(engine):
    conn = engine.connect()
    trans = conn.begin()
    try:
        conn.execute(text('DROP TABLE IF EXISTS payments;'))
        conn.execute(text('DROP TABLE IF EXISTS payment_methods;'))
        trans.commit()
    except:
        trans.rollback()
        raise
    finally:
        conn.close()