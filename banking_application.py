import re
import sqlite3
import hashlib
import random
import time

from getpass import getpass

DB_FILE = "users.db"

with sqlite3.connect(DB_FILE) as conn:
    cursor = conn.cursor()
    cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL CHECK (full_name <> ''),
    username TEXT NOT NULL UNIQUE CHECK (username <> ''),
    password TEXT NOT NULL CHECK (password <> ''),
    current_balance FLOAT DEFAULT 0,
    account_number INTEGER NOT NULL UNIQUE
);
""")
    

# transactions -> ID, transactoin_type [deposit, transafer, withdrawal], created_at, receiver_

cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_number TEXT,
                type TEXT,
                amount REAL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    

def is_valid_name(name):
    return name.isalpha() and len(name) >= 4 and len(name) <= 255


def sign_up():
    print("************************************signup***********************************")
    while True:

        first_name = input("Enter your firt name: ").strip()
        if not is_valid_name(first_name):
            print("first name must be only alphabetical letters")
            continue
        break

    while True:
        last_name = input("Enter your last name: ").strip()
        if not is_valid_name(last_name):
            print("last name must be only alphabetical letters")
            continue
        break

    full_name = f"{first_name} {last_name}".title()
    
    while True:
        username = input("Enter your username: ").strip()
        if not username:
            print("username already exist.")
            continue

        if len(username) < 3 or len(username) > 20:
            print("username must be between 3 and 20 characters")
            continue

        if not re.match(r'^[A-Za-z0-9_]+$', username):
            print("username can only contain alphanumeric and underscores")
            continue

        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users where username = ?",
                        (username,))
            
            user = cursor.fetchone()

            if user is None:
                break
            else:
                print("Username is empty.")
                continue

    while True:
        password1 = getpass("Enter your password: ").strip()
        if not password1:
            print("Enter a correct password: ")
            continue

        password2 = getpass("Confirm your password: ").strip()
        if not password1:
            print("Confirm Password field cannot be blank")
            continue

        if not re.match(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*\W).{8,}$", password1):
            print("password can only contains uppercase letter, lowercase letter, number, and special character")
            continue
    
        if password1 != password2:
            print("Passwords do not match")
            continue

        if len(password1) < 8 or len(password1) > 30:
            print("password must be between 3 and 30 characters")
            continue
        break

    hashed_password = hashlib.sha256(password1.encode()).hexdigest()

    while True:
        initial_deposit = input("Enter your initial deposit: ").strip()
        if not initial_deposit:
            print("initial deposit cannot be empty")
            continue

        if not initial_deposit.isdigit():
            print("initial deposit must be digit")
            continue

        if float(initial_deposit) < 2000 or float(initial_deposit) <= 0:
            print("Initial deposit must be 2000 or more.")
            continue
        break

    initial_deposit = float(initial_deposit)

    user_account_number = get_account_number()

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (full_name, username, password, current_balance, account_number) VALUES (?, ?, ?, ?, ?)", (full_name, username, hashed_password, initial_deposit, user_account_number))
        except sqlite3.IntegrityError as exc:
            exc = str(exc)
            if exc == "UNIQUE constraint failed: users.username":
                print("A user with that username already exists")
            elif exc == "UNIQUE constraint failed: users.account_number":
                print("A user with that account_number already exists")
            else:
                print(exc)
        else:
            conn.commit()
            print("Account created successfully 🥳")
            log_in()







def get_account_number():
    while True:
        account_number = random.randint(111_111_11, 99_999_999)
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users where account_number = ?",
                        (account_number,))
            
            user = cursor.fetchone()
            if user:
                continue
            break
    
    return account_number
       

def log_in():
    print("*********************************Login************************************")
    while True:
        username = input("Enter your username: ").strip()

        if not username:
            print("Username cannot be empty.")
            continue

        if not re.match(r'^[A-Za-z0-9_]+$', username):
            print("username can only contain alphanumeric and underscores")
            continue
        break
        


    while True:
            password1 = getpass("Enter your password: ").strip()

            if not password1:
                print("Password field cannot be blank")
                continue
            break

    hashed_password = hashlib.sha256(password1.encode()).hexdigest()

    with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            user = cursor.execute("SELECT id, full_name, username, account_number, current_balance FROM users WHERE username=? AND password=?", (username, hashed_password)).fetchone()
            if user is None:
                print("Invalid credentials")  
                return
            print("Log In Successful")
            deposit()
    

def deposit(account_number):

    while True:
        deposit = input("Enter the amount you want to deposit: ").strip()

        if deposit == "":
            print("Deposit amount cannot be blank.")
            continue
        try:
            deposit = float(deposit)
            if deposit < 0:
                print("Invalid amount. please enter a positive amount.")
                continue

            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                # Get current balance
                cursor.execute("SELECT current_balance FROM users WHERE account_number = ?", (account_number,))
                result = cursor.fetchone()
                if not result:
                    print("Account not found.")
                    return
                
                new_balance = result[0] + deposit

                # Update balance
                cursor.execute("UPDATE users SET current_balance = ? WHERE account_number = ?", (new_balance, account_number))

                # Record transaction
                cursor.execute("""
                INSERT INTO transactions (account_number, type, amount)
                VALUES (?, 'deposit', ?)""", (account_number, new_balance))
                conn.commit()
            print(f"Deposit of ₦{deposit} accepted and added to your balance!")
            break 
        except ValueError:
                print("Please enter a valid amount.")
        withdrawal()

def withdrawal(account_number):

    while True:
        withdrawal= input("Enter the amount you want to withdraw.").strip()

        if withdrawal =="":
            print("Withdrawal amount cannot be blank.")
            continue
        try:
            withdrawal_amount = float(withdrawal)

            if withdrawal_amount < 0:
                print("Invalid amount. Please enter a positive number.")
                continue

            with sqlite3.connect(DB_FILE) as conn:
                    cursor = conn.cursor()
                    # Get users current balance
                    cursor.execute("SELECT balance FROM users WHERE account_number = ?", (account_number,))
                    result = cursor.fetchone()

                    if result is None:
                        print("Account not found")
                        break

                    current_balance = result[0]

                    if withdrawal_amount > current_balance:
                        print("Insufficient fund. Your current balance is #{current_balance:.2f}")

                        new_balance =current_balance - withdrawal_amount
                        # update balance
                        cursor.execute("""
                        UPDATE users
                        SET balance = ?
                        WHERE account_number = ?
                    """, (new_balance, account_number))
                        
                        # --- Record transaction ---
                        cursor.execute("""INSERT INTO transactions (account_number, type, amount) VALUES (?, 'withdraw', ?)""", (account_number, withdrawal_amount))
                    conn.commit()

                    print(f"Withdrawal of ₦{withdrawal_amount:.2f} successful!")
                    print(f"New balance: ₦{new_balance:.2f}")
                    break 
         
        except ValueError:
            print("Please enter a valid amount.")
            view_transaction_history()

def view_transaction_history(account_number):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT type, amount, Date
            FROM transactions
            WHERE account_number = ?
            ORDER BY Date DESC
            LIMIT 10
        """, (account_number,))

        transactions = cursor.fetchall()

        if not transactions:
            print("No transactions found for this account.")
        else:
            print("\n=== Transaction History ===")
            print(f"{'Type':<15}{'Amount':<12}{'Date'}")
            print("-" * 45)
            for t_type, amount, date in transactions:
                print(f"{t_type:<15}₦{amount:<10.2f}{date}")
            print("-" * 45) 
            transfer()

def transfer(sender_account):

    recipient = input("Enter the recipient's account number: ").strip()
    # validate recipient
    if recipient == "":
        print("Recipient account number cannot be blank.")
        return
    
    if not recipient.isdigit():
        print("Account number must contain only digits.")
        return
    
    if recipient == sender_account:
        print("You cannot transfer money to your own account.")
        return
    
    
    amount = input("Enter the amount you want to transfer: ").strip()

    if amount =="":
        print("Amount cannot be blank.")
        return
    
    try:
        amount = float(amount)
    except ValueError:
        print("Please enter a valid numeric amount.")

    if amount < 0:
        print("Transfer amount cannot be negative.")
        # perform transfer
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            # check if recipient exist
            cursor.execute("SELECT current_balance FROM users WHERE account_number = ?", (recipient,))
            recipient_result = cursor.fetchone()

        if not recipient_result:
            print("Recipient account not found.")
            return
        
            # check sender balance
        cursor.execute("SELECT balance FROM users WHERE account_number = ?", (sender_account,))
        sender_data = cursor.fetchone()

        if not sender_data:
            print("Sender account not found.")
            return
        
        sender_balance = sender_data[0]

        # Check if sender has enough money
        if amount > sender_balance:
            print(f"Insufficient funds. Your current balance is ₦{sender_balance:.2f}.")
            return
        
        # --- Update balances ---
        new_sender_balance = sender_balance - amount
        new_recipient_balance = recipient_result[0] + amount

        # --- Perform Transfer ---
        cursor.execute("UPDATE users SET balance = balance - ? WHERE account_number = ?", (new_sender_balance, sender_account))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE account_number = ?", (new_recipient_balance, recipient))

        # Record transactions
        cursor.execute("INSERT INTO transactions (account_number, type, amount) VALUES (?, 'transfer_out', ?)",
                        (sender_account, amount))
        cursor.execute("INSERT INTO transactions (account_number, type, amount) VALUES (?, 'transfer_in', ?)",
                        (recipient, amount))

        conn.commit()

        print(f"Transfer of ₦{amount:.2f} to account {recipient} was successful!")

        





        



    




sign_up()