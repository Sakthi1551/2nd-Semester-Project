import psycopg2
from psycopg2 import errors 
import tabulate
import getpass
import stdiomask
from datetime import datetime, date, timedelta
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

cursor.execute("""CREATE TABLE IF NOT EXISTS customers(
               cust_id SERIAL PRIMARY KEY, 
               username TEXT UNIQUE NOT NULL,
               password TEXT NOT NULL,
               email TEXT NOT NULL
               )""")

cursor.execute("""CREATE TABLE IF NOT EXISTS orders(
               order_id SERIAL PRIMARY KEY, 
               customer_id INTEGER NOT NULL,
               serv_id INTEGER NOT NULL,
               provider_id INTEGER NOT NULL,
               booking_date TEXT NOT NULL,
               status TEXT NOT NULL DEFAULT 'Pending',
               FOREIGN KEY(customer_id) REFERENCES customers(cust_id) ON DELETE CASCADE,
               FOREIGN KEY(serv_id) REFERENCES services(service_id) ON DELETE CASCADE,
               FOREIGN KEY(provider_id) REFERENCES providers(id) ON DELETE CASCADE
               )""")

cursor.execute("""CREATE TABLE IF NOT EXISTS reviews(
               review_id SERIAL PRIMARY KEY, 
               customer_id INTEGER NOT NULL,
               service_id INTEGER NOT NULL,
               rating INTEGER NOT NULL,
               review_text TEXT,
               review_date TEXT NOT NULL,
               FOREIGN KEY(customer_id) REFERENCES customers(cust_id) ON DELETE CASCADE,
               FOREIGN KEY(service_id) REFERENCES services(service_id) ON DELETE CASCADE
               )""")


connection.commit()

def rating_update(service_id):
    try:
        cursor.execute("SELECT AVG(rating) FROM reviews WHERE service_id = %s", (service_id,))
        average_rating = cursor.fetchone()[0]
        
        if average_rating is not None:
            rounded_rating = round(average_rating, 2)
            
            cursor.execute("UPDATE services SET avg_rating = %s WHERE service_id = %s", (rounded_rating, service_id))
            connection.commit()
            cursor.execute("SELECT provider_id FROM services WHERE service_id = %s", (service_id,))
            provider_id = cursor.fetchone()[0]
            
            if rounded_rating < 2.5:
                cursor.execute("SELECT flag_id FROM provider_flags WHERE provider_id = %s AND reason = %s AND is_resolved = 0", (provider_id, "Low Customer Ratings"))
                if not cursor.fetchone():
                    flag_provider(provider_id, "Low Customer Ratings", f"Average rating dropped to {rounded_rating}")

    except Exception as e:
        connection.rollback()
        print(f"Error updating average rating for service ID {service_id}: {e}")

def cust_register():
    print("-"*30)
    print("Customer Registration")
    print("-"*30)
    username = input("Enter your username: ").strip()
    password = stdiomask.getpass("Enter your password: ")
    email = input("Enter your email: ")

    try:
        cursor.execute("INSERT INTO customers(username,password,email) VALUES(%s, %s, %s)",(username,password,email))
        connection.commit()
        print("You have Registered succesfully!!")
    except errors.UniqueViolation:
        connection.rollback()
        print("Username has already been taken or another unique constraint was violated!")
    except Exception as e:
        connection.rollback()
        print(f"An unexpected error occurred: {e}")

def cust_login():
    print("-"*30)
    print("Customer Login")
    print("-"*30)
    username = input("Enter your username: ").strip()
    password = stdiomask.getpass("Enter your password: ")
        
    cursor.execute("SELECT * FROM customers WHERE username = %s AND password = %s",(username,password))
    output = cursor.fetchone()

    if output:
        return output
    else:
        print("Invalid username or password!")

def service_view():     
    print("----- Services ----- \n")
    
    cursor.execute("SELECT service_id,category,location,min_price || ' - ' || max_price AS price_range,avg_rating as Rating,provider_id FROM services ORDER BY service_id ASC")
    values = cursor.fetchall()

    if values:
        print(tabulate.tabulate(values,headers=["Service_ID","Category","Location","Price Range","Rating","Provider_ID"],tablefmt="pretty"))
        while True:
            print("-----Search Options-----")
            print("1. Search By Category \n2. Search By Location \n3. Search By Price \n4. Search By Rating \n5. Exit")
            
            try:
                search_choice = int(input("Enter your choice: "))
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue

            if search_choice==1:
                cursor.execute("SELECT DISTINCT category FROM services")
                categories = cursor.fetchall()
                print(tabulate.tabulate(categories,headers=["Categories"],tablefmt="pretty"))
                category = input("Enter the category(eg. Photography, Catering etc.): ").strip()
                cursor.execute("SELECT service_id,category,location,min_price || ' - ' || max_price AS price_range,avg_rating as Rating,provider_id FROM services WHERE category = %s",(category,))
                search_res = cursor.fetchall()
                if search_res:
                    print(tabulate.tabulate(search_res,headers=["Service_ID","Category","Location","Price Range","Rating","Provider_ID"],tablefmt="pretty"))
                else:
                    print("No Services Found!")
            elif search_choice==2:
                cursor.execute("SELECT DISTINCT location FROM services")
                locations = cursor.fetchall()
                print(tabulate.tabulate(locations,headers=["Locations"],tablefmt="pretty"))
                location = input("Enter the location from the table above: ").strip()
                cursor.execute("SELECT service_id,category,location,min_price || ' - ' || max_price AS price_range,avg_rating as Rating,provider_id FROM services WHERE location = %s",(location,))
                search_res = cursor.fetchall()
                if search_res:
                    print(tabulate.tabulate(search_res,headers=["Service_ID","Category","Location","Price Range","Rating","Provider_ID"],tablefmt="pretty"))
                else:
                    print("No Services Found!")

            elif search_choice==3:
                print("Type in your Price Range down below!")
                try:
                    min_price = int(input("Enter your minimum price: "))
                    max_price = int(input("Enter your maximum price: "))
                except ValueError:
                    print("Invalid price input. Please enter numbers.")
                    continue
                    
                if min_price > max_price:
                    print("The min price is greater than the max price, try again!")
                else:
                    cursor.execute("SELECT service_id,category,location,min_price || ' - ' || max_price AS price_range,avg_rating as Rating,provider_id FROM services WHERE (min_price BETWEEN %s AND %s) OR (max_price BETWEEN %s AND %s)",(min_price,max_price,min_price,max_price))
                    search_res = cursor.fetchall()
                    if search_res:
                        print(tabulate.tabulate(search_res,headers=["Service_ID","Category","Location","Price Range","Rating","Provider_ID"],tablefmt="pretty"))
                    else:
                        print("No Services Found!")
            
            elif search_choice==4:
                try:
                    min_rating = float(input("Enter the minimum rating you want: "))
                except ValueError:
                    print("Invalid rating input. Please enter a number.")
                    continue
                cursor.execute("SELECT service_id,category,location,min_price || ' - ' || max_price AS price_range,avg_rating as Rating,provider_id FROM services WHERE avg_rating >= %s",(min_rating,))
                search_res = cursor.fetchall()
                if search_res:
                    print(tabulate.tabulate(search_res,headers=["Service_ID","Category","Location","Price Range","Rating","Provider_ID"],tablefmt="pretty"))
                else:
                    print("No Services Found!")
            elif search_choice==5:
                break
            else:
                print("Enter a valid Choice!!")
                continue
    else:
        print("No Services to be Found!")

def prov_view():
    print("---------- Providers ----------")
    cursor.execute("SELECT id,username,companyName,socialId,contactNo FROM providers WHERE isValid = 'Approved'")
    search_res = cursor.fetchall()
    if search_res:
        print(tabulate.tabulate(search_res,headers=["ID","Username","Company Name","Social ID","Contact Info"],tablefmt="pretty"))
    else:
        print("No Providers!")

def service_book(user_id):
    userID = user_id

    cursor.execute("SELECT service_id,category,location,min_price || ' - ' || max_price AS price_range,avg_rating,provider_id FROM services ORDER BY service_id ASC")
    values = cursor.fetchall()
    if not values:
        print("No services available to book.")
        return
    else:
        print(tabulate.tabulate(values,headers=["Service_ID","Category","Location","Price Range","Rating","Provider_ID"],tablefmt="pretty"))
    
    service_id = None
    while service_id is None:
        try:
            service_id_input = input("\nEnter the Service ID you wish to book: ").strip()
            if not service_id_input:
                print("Service ID cannot be empty.")
                continue
            service_id = int(service_id_input)
            
            cursor.execute("SELECT provider_id FROM services WHERE service_id = %s", (service_id,))
            service_info = cursor.fetchone()

            if not service_info:
                print(f"Error: Service ID {service_id} not found. Please try again.")
                service_id = None 
                continue
                
            provider_id = service_info[0]

        except ValueError:
            print("Invalid input. Please enter a numerical Service ID.")
            service_id = None
        except Exception as e:
            print(f"An unexpected error occurred during service lookup: {e}")
            return

    booking_date_str = None
    booking_date_obj = None
    today = date.today()

    minimum_booking_date = today + timedelta(days=14)

    while booking_date_obj is None:
        booking_date_str = input(f"Enter the booking date (YYYY-MM-DD): ").strip()
        
        try:
            booking_date_obj = datetime.strptime(booking_date_str, "%Y-%m-%d").date()
            
            if booking_date_obj < today:
                print("Error: The booking date cannot be in the past.")
                booking_date_obj = None 
            
            elif booking_date_obj < minimum_booking_date:
                print(f"Error: The booking date must be at least 14 days in advance. Please choose a date on or after {minimum_booking_date.strftime('%Y-%m-%d')}.")
                booking_date_obj = None 

        except ValueError:
            print("Error: Invalid date format. Please use YYYY-MM-DD.")
            booking_date_obj = None 

    try:
        cursor.execute(
            "INSERT INTO orders(customer_id, serv_id, provider_id, booking_date) VALUES(%s, %s, %s, %s)",
            (userID, service_id, provider_id, booking_date_str)
        )
        connection.commit()
        print("\nBooking created successfully! The provider will review your request shortly.")

    except Exception as e:
        connection.rollback()
        print(f"A database error occurred while completing the booking: {e}")



def leave_review(customer_id):
    cursor.execute("""
        SELECT o.serv_id, s.category, s.location, p.companyName
        FROM orders o
        JOIN services s ON o.serv_id = s.service_id
        JOIN providers p ON s.provider_id = p.id
        WHERE o.customer_id = %s
    """, (customer_id,))
    
    booked_services = cursor.fetchall()
    
    if not booked_services:
        print("You have not booked any services yet. Please book a service before leaving a review.")
        return
        
    print("\nServices you have booked:")
    print(tabulate.tabulate(booked_services, headers=["Service ID", "Category", "Location", "Provider"], tablefmt="pretty"))
    
    try:
        service_id = int(input("\nEnter the Service ID you wish to review: ").strip())
        
        booked_service_ids = [s[0] for s in booked_services]
        if service_id not in booked_service_ids:
            print("Error: You can only review services you have booked.")
            return

        rating = int(input("Enter your rating (1-10): ").strip())
        if not 1 <= rating <= 10:
            print("Error: Rating must be a number between 1 and 10.")
            return
            
        review_text = input("Enter your review (optional, press Enter to skip): ").strip()
        review_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO reviews(customer_id, service_id, rating, review_text, review_date) VALUES(%s, %s, %s, %s, %s)",
            (customer_id, service_id, rating, review_text, review_date)
        )
        connection.commit()
        print("\nReview submitted successfully!")
        
        rating_update(service_id)

    except ValueError:
        connection.rollback()
        print("Invalid input. Please enter a numerical Service ID and a rating between 1 and 10.")
    except Exception as e:
        connection.rollback()
        print(f"An error occurred while submitting the review: {e}")

def view_reviews():
    cursor.execute("SELECT review_id,customer_id,service_id, rating, review_text, review_date FROM reviews")
    reviews = cursor.fetchall()
    if reviews:
        print(tabulate.tabulate(reviews,headers=["Review ID","Customer ID","Service ID","Rating","Feedback","Review Date"],tablefmt="pretty"))
    else:
        print("There are no reviews currently!")

def review_system(user_id):
    while True:
        print("Do you want to: \n1. See Reviews \n2. Add Reviews \n3. Exit")
        try:
            rev_choice = int(input("Enter your Choice(1-3): "))
        except ValueError:
            print("Invalid input. Please enter a number from 1-3.")
            continue

        if rev_choice==1:
            view_reviews()
        elif rev_choice==2:
            leave_review(user_id)
        elif rev_choice==3:
            break
        else:
            print("Enter a Valid Choice!")

def flag_provider(provider_id, reason, details=""):
    """Adds a new flag for a provider."""
    try:
        flag_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO provider_flags(provider_id, reason, details, flag_date) VALUES(%s, %s, %s, %s)",
            (provider_id, reason, details, flag_date)
        )
        connection.commit()
        print(f"\nProvider ID {provider_id} has been flagged for: {reason}")
    except Exception as e:
        connection.rollback()
        print(f"Error flagging provider {provider_id}: {e}")

def report_provider(customer_id):
    print("-----Report a Provider-----")
    try:
        cursor.execute("SELECT username FROM providers")
        prov_names = cursor.fetchall()
        print(tabulate.tabulate(prov_names,headers=["Usernames"],tablefmt="pretty"))
        provider_username = input("Enter the username of the provider you wish to report: ").strip()
        cursor.execute("SELECT id FROM providers WHERE username = %s", (provider_username,))
        provider_id_info = cursor.fetchone()
        
        if not provider_id_info:
            print("Error: Provider not found.")
            return
            
        provider_id = provider_id_info[0]
        reason = "Customer Complaint"
        details = input("Please describe the issue in detail: ").strip()
        
        flag_provider(provider_id, reason, details)
        
    except Exception as e:
        print(f"An error occurred while reporting the provider: {e}")

def customer_interface(user):
    username = user[1]
    user_id = user[0]

    while True:
        print("-"*30)
        print("Customer Overview")
        print("-"*30)
        print(f"Welcome {username}")
        print("1. Explore Services \n2. Check out Providers \n3. Service Bookings \n4. Reviews and Ratings \n5. Report a Provider \n6. Exit")
        
        try:
            cust_choice = int(input("Enter your choice: "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue

        if cust_choice == 1:
            print("-"*30)
            print("Exploring Services")
            print("-"*30)
            service_view()
        elif cust_choice == 2:
            print("-"*30)
            print("Service Providers List")
            print("-"*30)
            prov_view()
        elif cust_choice == 3:
            print("-"*30)
            print("Book a Service")
            print("-"*30)
            service_book(user_id)

        elif cust_choice == 4:
            print("-"*30)
            print("Ratings & Review")
            print("-"*30)
            review_system(user_id)     
        
        elif cust_choice==5:
            report_provider(user_id)

        elif cust_choice == 6:
            print("Logging Off!")
            break

        else:
            print("Enter a Valid Choice!")

def customer_main():
    while True:
        print("-"*30)
        print("CUSTOMER MODULE")
        print("-"*30)
        print("1. Register \n2. Login \n3. Exit")

        try:
            user_choice=int(input("Enter your choice: "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue
            
        if user_choice==1:
            cust_register()
        elif user_choice==2:
            cust_info = cust_login()
            if cust_info:
                customer_interface(cust_info)
        elif user_choice == 3:
            print("Exiting Application!")
            break
        else:
            print("Enter a valid option!")
            continue


if __name__ == "__main__":
    try:
        customer_main()
    finally:
        if 'connection' in locals() and connection:
            connection.close()
            print("DB Connection Closed!")