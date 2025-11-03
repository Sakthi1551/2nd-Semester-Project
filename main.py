import psycopg2
from psycopg2 import errors
import sys
from admin import admin_main
from customer import customer_main
from servicePro import service_main

DB_NAME = "Miniproject"
DB_USER = "postgres"
DB_PASS = "postgresSQL"
DB_HOST = "localhost" 

connection = None
cursor = None

def setup_database():
    global connection, cursor
    try:
        connection = psycopg2.connect(
            dbname=DB_NAME, 
            user=DB_USER, 
            password=DB_PASS, 
            host=DB_HOST
        )
        cursor = connection.cursor()
        #print("Successfully connected to PostgreSQL database.")

        
        return True

    except Exception as e:
        print(f"Error connecting to the PostgreSQL database or setting up tables: {e}")
        print("ACTION REQUIRED: Please verify your PostgreSQL server is running and the connection variables (DB_NAME, DB_USER, etc.) are correct.")
        return False


def main_menu():
    """Main application loop for user role selection."""
    while True:
        print("\n" + "="*40)
        print("EVENT MANAGEMENT APPLICATION - MAIN MENU")
        print("="*40)
        print("Select your role:")
        print("1. Service Provider Portal")
        print("2. Customer Portal (View/Book Services)")
        print("3. Admin Portal (Management)")
        print("4. Exit Application")

        try:
            choice = input("Enter your choice (1-4): ").strip()
            
            if choice == '1':
                service_main()
            elif choice == '2':
                customer_main()
            elif choice == '3':
                admin_main()
            elif choice == '4':
                print("Exiting Application.")
                break
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")
                
        except Exception as e:
            print(f"An unexpected application error occurred: {e}")
            connection.rollback() 


def start_application():
    if setup_database():
        try:
            main_menu()
        finally:
            if connection:
                connection.close()
                print("Database Connection Closed.")
    else:
        print("Application could not start due to database error.")

        
if __name__ == "__main__":
    start_application()
