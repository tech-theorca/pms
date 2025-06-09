from main import HotelManagementSystem
from migrations import applied_migrations
import importlib

def run_migrations():
    # Initialize the hotel management system to get the engine
    hotel = HotelManagementSystem()
    
    print("Running migrations...")
    for migration in applied_migrations:
        try:
            # Import the migration module
            migration_module = importlib.import_module(f'migrations.{migration}')
            
            # Run the upgrade function
            print(f"Applying migration: {migration}")
            migration_module.upgrade(hotel.engine)
            print(f"Migration {migration} applied successfully")
        except Exception as e:
            print(f"Error applying migration {migration}: {str(e)}")
            break
    
    print("Migrations completed")

if __name__ == "__main__":
    run_migrations()