import mysql.connector
from datetime import datetime, timedelta

# ------------------------ CONNECT ------------------------
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="Jananii@Harinii27"
)
mycursor = mydb.cursor()

# -------------------- CREATE DATABASE --------------------
mycursor.execute("CREATE DATABASE IF NOT EXISTS Library")
mycursor.execute("USE Library")

# -------------------- CREATE BookRecord --------------------
mycursor.execute("SHOW TABLES LIKE 'BookRecord'")
if not mycursor.fetchone():
    mycursor.execute("""
        CREATE TABLE BookRecord(
            BookID VARCHAR(10) PRIMARY KEY,
            BookName VARCHAR(35),
            Author VARCHAR(30),
            Publisher VARCHAR(30),
            PublishingDate DATE,
            Language VARCHAR(20),
            Genre VARCHAR(30)
        )
    """)
    print("✅ BookRecord table created.")
else:
    print("ℹ️ BookRecord already exists.")
    # Add missing columns
    columns = {
        'PublishingDate': "DATE",
        'Language': "VARCHAR(20)",
        'Genre': "VARCHAR(30)"
    }
    for col, dtype in columns.items():
        mycursor.execute(f"SHOW COLUMNS FROM BookRecord LIKE '{col}'")
        if not mycursor.fetchone():
            mycursor.execute(f"ALTER TABLE BookRecord ADD {col} {dtype}")
            print(f"✅ Column '{col}' added.")

mydb.commit()

# -------------------- CREATE UserRecord --------------------
mycursor.execute("SHOW TABLES LIKE 'UserRecord'")
if not mycursor.fetchone():
    mycursor.execute("""
        CREATE TABLE UserRecord(
            UserID VARCHAR(10) PRIMARY KEY,
            UserName VARCHAR(20),
            Password VARCHAR(20),
            BorrowedBooks TEXT,
            DateBorrowed DATE,
            NoOfBooksBorrowed INT DEFAULT 0,
            DueDate DATE,
            UserType VARCHAR(10)
        )
    """)
    print("✅ UserRecord table created.")

    default_users = [
        ("101", "Kunal", "1234", None, None, 0, None, "Student"),
        ("102", "Vishal", "3050", None, None, 0, None, "Teacher"),
        ("103", "Siddhesh", "5010", None, None, 0, None, "Student")
    ]
    mycursor.executemany("""
        INSERT INTO UserRecord 
        (UserID, UserName, Password, BorrowedBooks, DateBorrowed, NoOfBooksBorrowed, DueDate, UserType)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, default_users)
    mydb.commit()
    print("✅ Default users inserted.")
else:
    print("ℹ️ UserRecord already exists.")

    # --- Convert BookID → BorrowedBooks (if not yet done) ---
    mycursor.execute("SHOW COLUMNS FROM UserRecord LIKE 'BorrowedBooks'")
    if not mycursor.fetchone():
        # Step 1: Drop foreign key if exists
        try:
            mycursor.execute("ALTER TABLE UserRecord DROP FOREIGN KEY UserRecord_ibfk_1")
        except:
            pass  # If no such foreign key, skip

        # Step 2: Drop BookID column if exists
        mycursor.execute("SHOW COLUMNS FROM UserRecord LIKE 'BookID'")
        if mycursor.fetchone():
            mycursor.execute("ALTER TABLE UserRecord DROP COLUMN BookID")
            print("✅ Dropped old 'BookID' column.")

        # Step 3: Add BorrowedBooks column
        mycursor.execute("ALTER TABLE UserRecord ADD BorrowedBooks TEXT")
        print("✅ Added 'BorrowedBooks' TEXT column.")
    else:
        print("ℹ️ 'BorrowedBooks' already exists.")

    # Ensure other required columns
    other_cols = {
        'DateBorrowed': "DATE",
        'NoOfBooksBorrowed': "INT DEFAULT 0",
        'DueDate': "DATE",
        'UserType': "VARCHAR(10)"
    }
    for col, dtype in other_cols.items():
        mycursor.execute(f"SHOW COLUMNS FROM UserRecord LIKE '{col}'")
        if not mycursor.fetchone():
            mycursor.execute(f"ALTER TABLE UserRecord ADD {col} {dtype}")
            print(f"✅ Column '{col}' added.")

    mydb.commit()

# -------------------- CREATE AdminRecord --------------------
mycursor.execute("SHOW TABLES LIKE 'AdminRecord'")
if not mycursor.fetchone():
    mycursor.execute("""
        CREATE TABLE AdminRecord(
            AdminID VARCHAR(10) PRIMARY KEY,
            Password VARCHAR(20)
        )
    """)
    admins = [
        ("Kunal1020", "123"),
        ("Siddesh510", "786"),
        ("Vishal305", "675")
    ]
    mycursor.executemany("INSERT INTO AdminRecord VALUES (%s, %s)", admins)
    mydb.commit()
    print("✅ AdminRecord created and default admins added.")
else:
    print("ℹ️ AdminRecord already exists.")

# -------------------- CREATE Feedback Table --------------------
mycursor.execute("SHOW TABLES LIKE 'Feedback'")
if not mycursor.fetchone():
    mycursor.execute("""
        CREATE TABLE Feedback(
            Feedback VARCHAR(100) PRIMARY KEY,
            Rating VARCHAR(10)
        )
    """)
    print("✅ Feedback table created.")
else:
    print("ℹ️ Feedback table already exists.")

# -------------------- END --------------------
print("✅ Setup completed successfully.")
