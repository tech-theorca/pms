from sqlalchemy import create_engine, text
import sys
import os
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import Base

load_dotenv()

def upgrade():
    # Create MySQL connection URL
    db_url = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    engine = create_engine(db_url)
    
    # Create room_types table
    with engine.connect() as conn:
        conn.execute(text("""
        CREATE TABLE room_types (
            id INT AUTO_INCREMENT PRIMARY KEY,
            type_name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT,
            base_price DECIMAL(10,2) NOT NULL,
            max_guest INT NOT NULL
        )
        """))
        
        # Insert default room types
        conn.execute(text("""
        INSERT INTO room_types (type_name, description, base_price, max_guest) VALUES
        ('Standard', 'Standard room with basic amenities', 500000.00, 2),
        ('Deluxe', 'Deluxe room with additional comfort', 750000.00, 2),
        ('Suite', 'Luxurious suite with separate living area', 1200000.00, 4)
        """))
        
        # Create temporary column in rooms table
        conn.execute(text("ALTER TABLE rooms ADD COLUMN room_type_id INT"))
        
        # Update room_type_id based on existing room_type values
        conn.execute(text("""
        UPDATE rooms r
        JOIN room_types rt ON r.room_type = rt.type_name
        SET r.room_type_id = rt.id
        """))
        
        # Make room_type_id NOT NULL and add foreign key
        conn.execute(text("""
        ALTER TABLE rooms
        MODIFY room_type_id INT NOT NULL,
        ADD FOREIGN KEY (room_type_id) REFERENCES room_types(id),
        DROP COLUMN room_type
        """))
        
        conn.commit()

def downgrade():
    engine = create_engine(f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}")
    
    with engine.connect() as conn:
        # Add room_type column back
        conn.execute(text("ALTER TABLE rooms ADD COLUMN room_type VARCHAR(50)"))
        
        # Restore room_type values
        conn.execute(text("""
        UPDATE rooms r
        JOIN room_types rt ON r.room_type_id = rt.id
        SET r.room_type = rt.type_name
        """))
        
        # Drop foreign key and room_type_id
        conn.execute(text("""
        ALTER TABLE rooms
        DROP FOREIGN KEY rooms_ibfk_2,
        DROP COLUMN room_type_id
        """))
        
        # Drop room_types table
        conn.execute(text("DROP TABLE room_types"))
        
        conn.commit()