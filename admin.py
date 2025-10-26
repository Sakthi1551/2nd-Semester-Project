import psycopg2
from psycopg2 import errors 
import tabulate
import stdiomask
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
    print("Successfully connected to PostgreSQL database.")
except Exception as e:
    print(f"Error connecting to the PostgreSQL database: {e}")
    sys.exit(1)
connection.commit()
def admin_login():
    print("-"*30)
    print("Admin Login")
    print("-"*30)
    password = stdiomask.getpass("Enter your passcode: ") 
    if password!="sakthi123":
        print("Wrong Passcode!")
        return False
    else:
        print("You have Logged in!")
        return True
def view_unvalidated_providers():
    cursor.execute("SELECT id, username, companyName, socialId, contactNo FROM providers WHERE isValid = 'Pending'")
    unvalidated_list = cursor.fetchall()
    if unvalidated_list:
        headers = ["Provider ID", "Username", "Company Name","Social Media ID","Contact No."]
        print(tabulate.tabulate(unvalidated_list, headers=headers, tablefmt="pretty"))
        return unvalidated_list
    else:
        print("No providers are currently awaiting approval.")
        return None
def prov_approve():
    unvalidated_list = view_unvalidated_providers()
    if not unvalidated_list:
        return
    try:
        provider_id = int(input("\nEnter the Provider ID to manage: ").strip())
    except ValueError:
        print("Invalid input. Please enter a number.")
        return
    if not any(provider[0] == provider_id for provider in unvalidated_list):
        print("Invalid Provider ID. Please select a provider from the list.")
        return
    try:
        action = int(input("Enter 1 to validate or 2 to reject and delete the application: "))
    except ValueError:
        print("Invalid action input.")
        return
    if action == 1:
        try:
            cursor.execute("UPDATE providers SET isValid = 'Approved' WHERE id = %s AND isValid = 'Pending'", (provider_id,))
            if cursor.rowcount > 0:
                connection.commit()
                print(f"\nProvider ID {provider_id} has been approved.")
            else:
                connection.rollback()
                print("\nProvider not found or has already been approved.")
        except Exception as e:
            connection.rollback()
            print(f"\nAn error occurred while approving the provider: {e}")

    elif action == 2:
        try:
            cursor.execute("DELETE FROM providers WHERE id = %s AND isValid = 'Pending'", (provider_id,))
            if cursor.rowcount > 0:
                connection.commit()
                print(f"\nProvider ID {provider_id} has been rejected and deleted.")
            else:
                connection.rollback()
                print("\nProvider not found or has already been approved.")
        except Exception as e:
            connection.rollback()
            print(f"\nAn error occurred while rejecting the provider: {e}")

    else:
        print("\nInvalid action. Please enter 1 or 2.")
def view_users():
    cursor.execute("""
        SELECT id, username, companyName, 'Provider' AS user_type
        FROM providers
        UNION ALL
        SELECT cust_id, username, NULL, 'Customer' AS user_type
        FROM customers
        ORDER BY user_type, username
    """)
    all_users = cursor.fetchall()
    if all_users:
        headers = ["ID", "Username", "Company Name", "User Type"]
        print(tabulate.tabulate(all_users, headers=headers, tablefmt="pretty"))
    else:
        print("No users have been registered yet.")
def manage_termination_requests():
    print("-----Termination Requests-----")
    cursor.execute("""
        SELECT t.request_id, p.companyName, p.username, t.reason, t.request_date, t.provider_id
        FROM termination_requests t
        JOIN providers p ON t.provider_id = p.id
    """)
    requests = cursor.fetchall()
    if not requests:
        print("No account termination requests at this time.")
        return
    headers = ["Request ID", "Company Name", "Username", "Reason", "Request Date"]
    display_requests = [row[:-1] for row in requests] 
    print(tabulate.tabulate(display_requests, headers=headers, tablefmt="pretty"))
    try:
        request_id = int(input("\nEnter the Request ID to manage: ").strip())
        selected_request = next((req for req in requests if req[0] == request_id), None)
        if not selected_request:
            print("Invalid Request ID.")
            return
        provider_id_to_terminate = selected_request[5]
        action = input("Enter 'terminate' to confirm or 'delete' to ignore the request: ").strip().lower()
        if action == 'terminate':
            try:
                cursor.execute("DELETE FROM providers WHERE id = %s", (provider_id_to_terminate,))
                cursor.execute("DELETE FROM services WHERE provider_id = %s", (provider_id_to_terminate,))
                cursor.execute("DELETE FROM termination_requests WHERE request_id = %s", (request_id,))
                
                connection.commit()
                print(f"\nProvider ID {provider_id_to_terminate} and their services have been terminated and deleted.")
            except Exception as e:
                connection.rollback()
                print(f"\nAn error occurred during termination: {e}")
        elif action == 'delete':
            try:
                cursor.execute("DELETE FROM termination_requests WHERE request_id = %s", (request_id,))
                connection.commit()
                print(f"\nTermination request ID {request_id} has been deleted.")
            except Exception as e:
                connection.rollback()
                print(f"\nAn error occurred while deleting the request: {e}")
        else:
            print("\nInvalid action. Please enter 'terminate' or 'delete'.")
    except ValueError:
        print("Invalid input. Please enter a numerical Request ID.")
def manage_provider_flags():
    print("-----Manage Provider Flags-----")
    cursor.execute("""
        SELECT f.flag_id, p.companyName, p.username, f.reason, f.details, f.flag_date, f.provider_id
        FROM provider_flags f
        JOIN providers p ON f.provider_id = p.id
        WHERE f.is_resolved = 0
        ORDER BY f.flag_date DESC
    """)
    flags = cursor.fetchall()
    if not flags:
        print("No unresolved flags at this time.")
        return
    headers = ["Flag ID", "Company Name", "Username", "Reason", "Details", "Flag Date"]
    display_flags = [row[:-1] for row in flags]
    print(tabulate.tabulate(display_flags, headers=headers, tablefmt="pretty"))
    try:
        flag_id = int(input("\nEnter the Flag ID to manage or '0' to exit: ").strip())
        if flag_id == 0:
            return
        selected_flag = next((flag for flag in flags if flag[0] == flag_id), None)
        if not selected_flag:
            print("Invalid Flag ID or flag is already resolved.")
            return
        provider_id_to_manage = selected_flag[6]
        action = input("Enter 'resolve' to mark this flag as resolved, or 'delete' to delete the provider: ").strip().lower()
        if action == 'resolve':
            try:
                cursor.execute("UPDATE provider_flags SET is_resolved = 1 WHERE flag_id = %s", (flag_id,))
                connection.commit()
                print(f"Flag ID {flag_id} has been marked as resolved.")
            except Exception as e:
                connection.rollback()
                print(f"An error occurred while resolving the flag: {e}")
        elif action == 'delete':
            try:
                cursor.execute("DELETE FROM providers WHERE id = %s", (provider_id_to_manage,))
                cursor.execute("DELETE FROM services WHERE provider_id = %s",(provider_id_to_manage,))
                connection.commit()
                print(f"\nProvider with ID {provider_id_to_manage} and all related data has been deleted.")
            except Exception as e:
                connection.rollback()
                print(f"An error occurred while deleting the provider: {e}")
        else:
            print("Invalid action.")
    except ValueError:
        print("Invalid input. Please enter a numerical Flag ID.")

def admin_interface():
    while True:
        print("-"*30)
        print("Admin Overview")
        print("-"*30)
        print("Welcome Administrator")
        print("1. Provider Approval \n2. User List \n3. Termination requests \n4. Manage Provider Flags \n5. Exit")
        try:
            admin_choice = int(input("Enter your choice: "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue
        if admin_choice==1:
            prov_approve()
        elif admin_choice==2:
            view_users()    
        elif admin_choice==3:
            manage_termination_requests()
        elif admin_choice==4:
            manage_provider_flags()
        elif admin_choice==5:
            print("Exiting!")
            break
        else:
            print("Enter a Valid Option!")
def admin_main():
    enter=admin_login()
    if enter:
        admin_interface()
if __name__ == "__main__":
    try:
        admin_main()
    finally:
        if 'connection' in locals() and connection: 
            connection.close()
            print("DB Connection Closed!")