from main import HotelManagementSystem
from sqlalchemy import text

def update_guest_schema():
    hotel = HotelManagementSystem()
    
    # SQL statements to modify columns
    alter_statements = """
    ALTER TABLE guests
        MODIFY email VARCHAR(100) NULL,
        MODIFY address VARCHAR(200) NULL,
        MODIFY id_type VARCHAR(50) NULL,
        MODIFY country VARCHAR(100) NULL,
        MODIFY nationality VARCHAR(100) NULL,
        MODIFY date_of_birth DATETIME NULL;
    """
    
    try:
        # Execute the ALTER TABLE statements
        with hotel.engine.connect() as connection:
            connection.execute(text(alter_statements))
            connection.commit()
        print("Successfully updated the guests table schema!")
    except Exception as e:
        print(f"Error updating schema: {str(e)}")

if __name__ == '__main__':
    update_guest_schema()