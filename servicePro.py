import psycopg2
from psycopg2 import errors 
import getpass
import tabulate
import stdiomask
import datetime
import sys

DB_NAME = "Miniproject"
DB_USER = "postgres"
DB_PASS = "postgresSQL"
DB_HOST = "localhost" 


try:
    connection = psycopg2.connect(
        dbname=DB_NAME, 
        user=DB_USER, 
        password=DB_PASS, 
        host=DB_HOST
    )
    cursor = connection.cursor()
    #print("Successfully connected to PostgreSQL database.")

except Exception as e:
    print(f"Error connecting to the PostgreSQL database: {e}")
    sys.exit(1)


cursor.execute("""CREATE TABLE IF NOT EXISTS providers(
             id SERIAL PRIMARY KEY,
             username TEXT UNIQUE NOT NULL,
             password TEXT NOT NULL,
             companyName TEXT UNIQUE NOT NULL,
             socialId TEXT UNIQUE NOT NULL,
             contactNo TEXT UNIQUE NOT NULL,
             isValid TEXT NOT NULL DEFAULT 'Pending'
             )"""
)

cursor.execute("""CREATE TABLE IF NOT EXISTS services(
             service_id SERIAL PRIMARY KEY,
             category TEXT NOT NULL,
             location TEXT NOT NULL,
             min_price FLOAT NOT NULL,
             max_price FLOAT NOT NULL,
             avg_rating REAL DEFAULT 3.0 NOT NULL,
             provider_id INTEGER NOT NULL,
             FOREIGN KEY(provider_id) REFERENCES providers(id) ON DELETE CASCADE
             )"""
)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS termination_requests(
        request_id SERIAL PRIMARY KEY,
        provider_id INTEGER NOT NULL,
        reason TEXT,
        request_date TEXT NOT NULL,
        FOREIGN KEY(provider_id) REFERENCES providers(id) ON DELETE CASCADE
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS provider_flags(
        flag_id SERIAL PRIMARY KEY,
        provider_id INTEGER NOT NULL,
        reason TEXT NOT NULL,
        details TEXT,
        flag_date TEXT NOT NULL,
        is_resolved INTEGER DEFAULT 0 NOT NULL,
        FOREIGN KEY(provider_id) REFERENCES providers(id) ON DELETE CASCADE
    )
""")

connection.commit()

def register():
    print("-"*30)
    print("Service Provider Registration")
    print("-"*30)
    username = input("Enter your username: ").strip()
    password = stdiomask.getpass("Enter your password: ")
    comp_name = input("Enter your Company Name: ")
    social_id = input("Enter your Social Media Page(With Platform)/Website: ")

    while True:
        contact_num = input("Enter your Contact info: ")
        if contact_num.isdigit() and len(contact_num) == 10:
            break  
        else:
            print("Error: Contact number must be exactly 10 digits and contain only numbers. Please try again.")

    try:
        cursor.execute(
            "INSERT INTO providers(username,password,companyName,socialId,contactNo) VALUES(%s,%s,%s,%s,%s)",
            (username, password, comp_name, social_id, contact_num)
        )
        connection.commit()
        print("You have Registered succesfully!!")
        
    except errors.UniqueViolation:
        connection.rollback()
        print("Registration failed. A username, company name, social ID, or contact number has already been taken!")
        
    except Exception as e:
        connection.rollback()
        print(f"An unexpected error occurred: {e}")

def login():
    print("-"*30)
    print("Service Provider Login")
    print("-"*30)
    username = input("Enter your username: ").strip()
    password = stdiomask.getpass("Enter your password: ")
    
    cursor.execute("SELECT * FROM providers WHERE username = %s AND password = %s",(username,password))
    output = cursor.fetchone()
    if output:
        if output[6]=="Pending":
            print("Your application is pending! Please wait for approval")
        else:
            print("You have Logged In!")
            return output
    else:
        print("Username or Password does not match!")
        return None
    
def add_service(prov_id):
    print("Service Categories: ")
    print("1. Decoration \n2. Catering \n3. Makeup \n4. Music Band \n5. Photography ")
    categories = ["Decoration","Catering","Makeup","Music Band","Photography"]
    
    try:
        category_choice = int(input("Enter the Service Category (1-5): "))
        if not 1 <= category_choice <= 5:
            print("Invalid category choice.")
            return
        category = categories[category_choice - 1]
    except ValueError:
        print("Invalid input for category. Please enter a number.")
        return
        
    location = input("Enter the Location: ")
    print("Enter your cost range")
    
    while True:
        try:
            min_cost = int(input("Enter your Lower end: "))
            max_cost = int(input("Enter your Higher end: "))
            if min_cost > max_cost:
                print("Your minimum cost is greater than your maximum. Try again!")
            else:
                break
        except ValueError:
            print("Invalid input for cost. Please enter whole numbers.")
            
    try:
        cursor.execute("INSERT INTO services(category,location,min_price,max_price,provider_id) VALUES(%s,%s,%s,%s,%s)",
                       (category,location,min_cost,max_cost,prov_id))
        connection.commit()
        print("Service Added Successfully!")
    except Exception as e:
        connection.rollback()
        print(f"An error occurred while adding the service: {e}")

def view_service(prov_id):
    print("Your Services \n")

    cursor.execute("SELECT service_id,category,location,min_price || ' - ' || max_price AS price_range,avg_rating AS rating,provider_id FROM services WHERE provider_id= %s ORDER BY service_id ASC",(prov_id,))
    values = cursor.fetchall()

    if values:
        print(tabulate.tabulate(values,headers=["Service_ID","Category","Location","Price Range","Rating","Provider_ID"],tablefmt="pretty"))
        return values
    else:
        print("No Services to be Found!")

def update_service(prov_id):
    
    services = view_service(prov_id)
    if not services:
        print("No Services Available!")
        return
        
    try:
        service_id = int(input("\nEnter the Service ID you wish to update: ").strip())
    except ValueError:
        print("Invalid input. Please enter a number.")
        return

    cursor.execute("SELECT * FROM services WHERE service_id = %s AND provider_id = %s", (service_id, prov_id))
    service_to_update = cursor.fetchone()

    if not service_to_update:
        print("Service not found or you do not have permission to edit this service.")
        return

    column_options = {
        '1': 'category',
        '2': 'location',
        '3': 'min_price',
        '4': 'max_price'
    }
    
    print("\nSelect the columns you want to update:")
    for num, col in column_options.items():
        print(f"{num}. {col.capitalize()}")
    
    choices = input("Enter your choices (e.g., 1, 3): ").strip()
    selected_columns = [c.strip() for c in choices.split(',') if c.strip()]

    if not selected_columns:
        print("No columns selected. Update cancelled.")
        return

    update_clauses = []
    params = []
    
    new_min_price = service_to_update[3] 
    new_max_price = service_to_update[4]
    
    for choice in selected_columns:
        if choice not in column_options:
            print(f"Invalid choice: {choice}. Skipping.")
            continue
            
        column_name = column_options[choice]
        current_value = service_to_update[int(choice)] 

        new_value = None

        if column_name in ['min_price', 'max_price']:
            while True:
                try:
                    new_value_str = input(f"Enter new value for {column_name.capitalize()} (current: {current_value}): ").strip()
                    if not new_value_str:
                        new_value = current_value
                    else:
                        new_value = float(new_value_str)
                    
                    if new_value < 0:
                        print("Prices cannot be negative. Please re-enter.")
                    else:
                        if column_name == 'min_price':
                             new_min_price = new_value
                        elif column_name == 'max_price':
                             new_max_price = new_value
                        break
                except ValueError:
                    print("Invalid input. Please enter a numerical value.")
        else:
            new_value = input(f"Enter new value for {column_name.capitalize()} (current: {current_value}): ").strip()
            if not new_value:
                 new_value = current_value


        if new_value != current_value:
            update_clauses.append(f"{column_name} = %s")
            params.append(new_value)
    
    if not update_clauses:
        print("No changes were made.")
        return
    
    if new_min_price > new_max_price:
        print("Error: Lower end price cannot be greater than Higher end price. Update cancelled.")
        return

    query = f"UPDATE services SET {', '.join(update_clauses)} WHERE service_id = %s AND provider_id = %s"
    
    params.append(service_id)
    params.append(prov_id)
    
    try:
        cursor.execute(query, tuple(params))
        connection.commit()
        print(f"Service ID {service_id} updated successfully!")
    except Exception as e:
        connection.rollback()
        print(f"An error occurred while updating the service: {e}")


def delete_service(prov_id):
    while True:
        view_service(prov_id)
        print("1. Delete 1 of your Services")
        print("2. Delete All of your Services")
        print("3. Cancel")
        
        try:
            del_choice = int(input("Enter your choice(1-3): "))
        except ValueError:
            print("Invalid input. Please enter a number from 1-3.")
            continue

        if del_choice == 1:
            try:
                service_id = int(input("Enter the ID you want to Delete: "))
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue
                
            cursor.execute("SELECT * FROM services WHERE service_id = %s AND provider_id = %s",(service_id,prov_id))
            output = cursor.fetchone()
            
            if not output:
                print("This Service does NOT Exist or you do not own it.")
                return
            else:
                try:
                    cursor.execute("DELETE FROM services WHERE service_id = %s AND provider_id = %s",(service_id,prov_id))
                    connection.commit()
                    print(f"The Service ID {service_id} has been Deleted Successfully")
                except Exception as e:
                    connection.rollback()
                    print(f"There was an Error: {e}")
                    return
        elif del_choice == 2:
            print("Are you SURE you want to Delete ALL your Services?")
            print("1. Yes")
            print("2. No")
            
            try:
                confirmation = int(input("Enter your choice(1 or 2): "))
            except ValueError:
                print("Invalid input. Please enter 1 or 2.")
                continue

            if confirmation == 1:
                try:
                    cursor.execute("DELETE FROM services WHERE provider_id = %s",(prov_id,))
                    connection.commit()
                    print("ALL your Services have been Deleted Successfully!")
                except Exception as e:
                    connection.rollback()
                    print(f"There was an Error: {e}")
            else:
                print("Deletion Cancelled")
                
        elif del_choice == 3:
            print("Deletion Cancelled")
            break
            
        else:
            print("Enter a valid choice!")

def bookings(prov_id):
    print("-"*30)
    print("Your Bookings")
    print("-"*30)
    cursor.execute("""
        SELECT o.order_id, c.username, s.category, o.booking_date
        FROM orders o
        JOIN customers c ON o.customer_id = c.cust_id
        JOIN services s ON o.serv_id = s.service_id
        JOIN providers p ON o.provider_id = p.id
        WHERE o.provider_id = %s AND o.status = 'Pending'
    """, (prov_id,))
    
    pending_bookings = cursor.fetchall()

    if not pending_bookings:
        print("You have no pending booking requests at this time.")
        return

    headers = ["Booking ID", "Customer Username", "Service Category", "Booking Date"]
    print("\nPending Booking Requests:")
    print(tabulate.tabulate(pending_bookings, headers=headers, tablefmt="pretty"))

    try:
        booking_id = int(input("\nEnter the Booking ID to manage: ").strip())
        
        cursor.execute("SELECT status FROM orders WHERE order_id = %s AND provider_id = %s", (booking_id, prov_id))
        booking_status = cursor.fetchone()

        if booking_status and booking_status[0] == 'Pending':
            choice = input("Do you want to (A)ccept or (R)eject this booking? ").strip().lower()
            if choice == 'a':
                cursor.execute("UPDATE orders SET status = 'Accepted' WHERE order_id = %s", (booking_id,))
                connection.commit()
                print(f"Booking {booking_id} has been accepted!")
            elif choice == 'r':
                cursor.execute("UPDATE orders SET status = 'Rejected' WHERE order_id = %s", (booking_id,))
                connection.commit()
                print(f"Booking {booking_id} has been rejected.")
            else:
                print("Invalid choice. Please enter 'A' or 'R'.")
        else:
            print("Booking not found, not pending, or you do not have permission to manage it.")
    except ValueError:
        print("Invalid input. Please enter a numerical Booking ID.")
    except Exception as e:
        connection.rollback()
        print(f"An error occurred while managing the booking: {e}")

def request_termination(prov_id):
    print("-----Request Account Termination-----")
    reason = input("Please explain why you wish to terminate your account (e.g., closing the company): ").strip()
    
    try:
        request_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO termination_requests(provider_id, reason, request_date) VALUES(%s,%s,%s)",
            (prov_id, reason, request_date)
        )
        connection.commit()
        print("\nYour account termination request has been sent to the admin for review.")
        print("You will be logged out automatically.")
        return True
    except Exception as e:
        connection.rollback()
        print(f"An error occurred while submitting your request: {e}")
        return False

def provider_interface(provinfo):
    prov_id = provinfo[0]
    prov_username = provinfo[1]
    prov_compName = provinfo[3]

    while True:
        print("-"*30)
        print("Service Provider Overview")
        print("-"*30)
        print(f"Welcome {prov_username} of {prov_compName}")
        print("1. Add Service \n2. Update Service \n3. Delete Service \n4. View Services \n5. Manage Bookings \n6. Account termination \n7. Exit")
        
        try:
            prov_choice = int(input("Enter your choice: "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue
            
        if prov_choice == 1:
            print("-"*30)
            print("Adding a Service")
            print("-"*30)
            add_service(prov_id)
        elif prov_choice == 2:
            print("-"*30)
            print("Updating a Service")
            print("-"*30)
            update_service(prov_id)
        elif prov_choice == 3:
            print("-"*30)
            print("Deleting a Service")
            print("-"*30)
            delete_service(prov_id)

        elif prov_choice == 4:
            print("-"*30)
            print("Service Display")
            print("-"*30)
            view_service(prov_id) 

        elif prov_choice == 5:
            print("-"*30)
            print("Manage Bookings")
            print("-"*30)
            bookings(prov_id)
        
        elif prov_choice == 6:
            if request_termination(prov_id):
                break

        elif prov_choice == 7:
            print("Logging Off!")
            break

        else:
            print("Enter a Valid Option!")


def service_main():
    while True:
        print("-"*30)
        print("SERVICE PROVIDER MODULE")
        print("-"*30)
        print("1. Register \n2. Login \n3. Exit")

        try:
            user_choice=int(input("Enter your choice: "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue
            
        if user_choice==1:
            register()
        elif user_choice==2:
            prov_info = login()
            if prov_info:
                provider_interface(prov_info)
        elif user_choice == 3:
            print("Exiting Application!")
            break
        else:
            print("Enter a Valid choice!")
            continue
            
if __name__ == "__main__":
    try:
        service_main()
    finally:
        if 'connection' in locals() and connection:
            connection.close()
            print("DB Connection Closed!")