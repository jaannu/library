import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import mysql.connector
from datetime import date
from datetime import datetime, timedelta

# -------------------- UI Inline Status + Styling Helpers --------------------
from tkinter import messagebox as _orig_messagebox
from tkinter import simpledialog as _orig_simpledialog

# 🎨 Global style settings
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_LABEL = ("Segoe UI", 11)
FONT_BTN   = ("Segoe UI", 11, "bold")

BG_COLOR   = "#ffffff"
BTN_COLOR  = "#74b9ff"
ERR_COLOR  = "#ff7675"
OK_COLOR   = "#55efc4"
INFO_COLOR = "#ffeaa7"
STATUS_FONT = ("Segoe UI", 10)

# Keep originals
_orig_showinfo = _orig_messagebox.showinfo
_orig_showerror = _orig_messagebox.showerror
_orig_showwarning = _orig_messagebox.showwarning
_orig_askokcancel = _orig_messagebox.askokcancel
_orig_askyesno = _orig_messagebox.askyesno

# Patch Toplevel to auto-attach status label
_original_Toplevel = tk.Toplevel
def _patched_Toplevel(*args, **kwargs):
    win = _original_Toplevel(*args, **kwargs)
    try:
        status = tk.Label(win, text="", font=STATUS_FONT, fg="gray", bg=BG_COLOR, anchor="w")
        status.pack(side="bottom", fill="x", pady=(4,4))
        win._inline_status_label = status
    except Exception:
        pass
    return win
tk.Toplevel = _patched_Toplevel

# Helper: set inline message
def _set_inline_status(parent, text, color=None):
    try:
        if parent:
            top = parent.winfo_toplevel()
        else:
            top = tk._default_root
        if top and hasattr(top, "_inline_status_label"):
            lbl = getattr(top, "_inline_status_label")
            lbl.config(text=text, fg=color if color else "black")
            return True
    except Exception:
        pass
    return False

# Monkeypatch messagebox
def _showinfo(title, message, **kwargs):
    if _set_inline_status(kwargs.get("parent"), f"✅ {message}", OK_COLOR):
        return None
    return _orig_showinfo(title, message, **kwargs)

def _showerror(title, message, **kwargs):
    if _set_inline_status(kwargs.get("parent"), f"⚠ {message}", ERR_COLOR):
        return None
    return _orig_showerror(title, message, **kwargs)

def _showwarning(title, message, **kwargs):
    if _set_inline_status(kwargs.get("parent"), f"🔔 {message}", INFO_COLOR):
        return None
    return _orig_showwarning(title, message, **kwargs)

def _askokcancel(title, message, **kwargs):
    _set_inline_status(kwargs.get("parent"), f"Confirm: {message}", INFO_COLOR)
    return _orig_askokcancel(title, message, **kwargs)

def _askyesno(title, message, **kwargs):
    _set_inline_status(kwargs.get("parent"), f"Confirm: {message}", INFO_COLOR)
    return _orig_askyesno(title, message, **kwargs)

# Apply monkeypatches
messagebox.showinfo = _showinfo
messagebox.showerror = _showerror
messagebox.showwarning = _showwarning
messagebox.askokcancel = _askokcancel
messagebox.askyesno = _askyesno

# Simpledialog remains same, just keep original behavior
simpledialog.askstring = _orig_simpledialog.askstring

# Optional helper for your panels
def set_panel_status(widget, text, color=None):
    try:
        top = widget.winfo_toplevel()
        if hasattr(top, "_inline_status_label"):
            top._inline_status_label.config(text=text, fg=color if color else "black")
            return True
    except Exception:
        pass
    return False
# ------------------ Database Connection ------------------
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="Jananii@Harinii27",
    database="Library"
)
mycursor = mydb.cursor()

# ------------------ Shared Popup Table Display ------------------
def show_popup(title, records, root=None, headers=None):
    popup = tk.Toplevel(root)
    popup.title(title)
    popup.geometry("1000x500")
    popup.configure(bg="white")

    if not records:
        tk.Label(popup, text="No records found.", font=("Segoe UI", 12)).pack(pady=20)
        return

    # Default headers if not provided
    if not headers:
        headers = ["BookID", "BookName", "Author", "Publisher", "PublishingDate", "Language", "Genre"]

    # Frame and canvas setup
    main_frame = tk.Frame(popup, bg="white")
    main_frame.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(main_frame, bg="white")
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Scrollbars
    v_scroll = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
    v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    h_scroll = tk.Scrollbar(popup, orient=tk.HORIZONTAL, command=canvas.xview)
    h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

    canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
    canvas.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # Scrollable frame
    scroll_frame = tk.Frame(canvas, bg="white")
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

    # Headers
    for col_index, header in enumerate(headers):
        tk.Label(scroll_frame, text=header, font=("Segoe UI", 10, "bold"),
                 bg="#dfe6e9", borderwidth=1, relief="solid", width=20).grid(row=0, column=col_index, sticky="nsew")

    # Data Rows
    for row_index, row in enumerate(records, start=1):
        for col_index, cell in enumerate(row):
            value = str(cell) if cell is not None else "N/A"
            tk.Label(scroll_frame, text=value, font=("Segoe UI", 10),
                     bg="white", borderwidth=1, relief="solid", width=20, wraplength=160, justify="center"
                     ).grid(row=row_index, column=col_index, sticky="nsew")

def issue_book_to_user(user_id, book_id, parent):
    # Fetch user info
    mycursor.execute("SELECT UserType, BorrowedBooks, NoOfBooksBorrowed FROM UserRecord WHERE UserID = %s", (user_id,))
    result = mycursor.fetchone()

    if not result:
        messagebox.showerror("Error", "User not found or user type missing.", parent=parent)
        return

    user_type, borrowed_str, book_count = result
    borrowed_books = [b.strip() for b in borrowed_str.split(",") if b.strip()] if borrowed_str else []

    # Check borrowing limit
    if len(borrowed_books) >= 3:
        messagebox.showwarning("Limit Reached", "User has already borrowed 3 books. Return one to borrow more.", parent=parent)
        return

    # Check if the book exists
    mycursor.execute("SELECT * FROM BookRecord WHERE BookID = %s", (book_id,))
    book_exists = mycursor.fetchone()
    if not book_exists:
        messagebox.showerror("Error", "Book not found.", parent=parent)
        return

    # Check if the book is already borrowed by ANYONE
    mycursor.execute("SELECT UserID FROM UserRecord WHERE BorrowedBooks IS NOT NULL AND BorrowedBooks LIKE %s", (f"%{book_id}%",))
    borrowed_by = mycursor.fetchone()
    if borrowed_by:
        messagebox.showerror("Unavailable", f"Book '{book_id}' is already borrowed by another user.", parent=parent)
        return

    # Prevent same user re-borrowing same book
    if book_id in borrowed_books:
        messagebox.showinfo("Already Borrowed", f"Book '{book_id}' is already borrowed by this user.", parent=parent)
        return

    # Append book to list
    borrowed_books.append(book_id)
    updated_borrowed = ",".join(borrowed_books)

    # Dates
    today = date.today()
    due_days = 14 if user_type.lower() == "teacher" else 7
    due_date = today + timedelta(days=due_days)

    mycursor.execute("""
        UPDATE UserRecord
        SET BorrowedBooks = %s, DateBorrowed = %s, DueDate = %s, NoOfBooksBorrowed = %s
        WHERE UserID = %s
    """, (updated_borrowed, today, due_date, len(borrowed_books), user_id))

    mydb.commit()
    messagebox.showinfo("Book Issued", f"Book '{book_id}' issued to '{user_id}'\nDue on: {due_date}", parent=parent)
    status_label = tk.Label(root, text="", font=("Segoe UI", 10), fg="gray", bg=BG_COLOR)
    status_label.pack(side="bottom", pady=5)

# ------------------ Admin Functions ------------------
def open_admin_panel(root):
    panel = tk.Toplevel(root)
    panel.title("Admin Panel")
    panel.geometry("300x400")
    panel.configure(bg="#FFC0CB")  # pink background

    tk.Label(panel, text="Admin Panel", font=FONT_TITLE, bg="#FFC0CB").pack(pady=10)

    # --- Admin Management ---
    def open_admin_management():
        subpanel = tk.Toplevel(panel)
        subpanel.title("Admin Management")
        subpanel.geometry("450x400")
        subpanel.configure(bg="#FFC0CB")

        tk.Label(subpanel, text="Admin Management", font=FONT_TITLE, bg="#FFC0CB").pack(pady=10)

        # Result Display (always visible)
        result_label = tk.Label(subpanel, text="", font=("Segoe UI", 11), bg="#FFC0CB", fg="blue", justify="left")
        result_label.pack(pady=10)

        # --- Function to open action-specific input popups ---
        def open_input_panel(action):
            input_window = tk.Toplevel(subpanel)
            input_window.title(f"{action} Admin")
            input_window.geometry("300x200")
            input_window.configure(bg="#FFC0CB")

            tk.Label(input_window, text=f"{action} Admin", font=FONT_TITLE, bg="#FFC0CB").pack(pady=10)

            # Input fields
            admin_id_entry = tk.Entry(input_window, font=FONT_LABEL)
            tk.Label(input_window, text="Admin ID", font=FONT_LABEL, bg="#FFC0CB").pack(pady=5)
            admin_id_entry.pack(pady=5)

            password_entry = None
            if action in ["Insert", "Update"]:
                password_entry = tk.Entry(input_window, font=FONT_LABEL, show="*")
                tk.Label(input_window, text="Password", font=FONT_LABEL, bg="#FFC0CB").pack(pady=5)
                password_entry.pack(pady=5)

            # Perform the action
            def perform_action():
                admin_id = admin_id_entry.get().strip()
                password = password_entry.get().strip() if password_entry else None

                if action == "Insert":
                    if not admin_id or not password:
                        messagebox.showerror("Error", "Enter Admin ID and Password", parent=input_window)
                        return
                    mycursor.execute("INSERT INTO AdminRecord (AdminID, Password) VALUES (%s,%s)", (admin_id, password))
                    mydb.commit()
                    result_label.config(text=f"✅ Inserted Admin '{admin_id}'")

                elif action == "Search":
                    if not admin_id:
                        messagebox.showerror("Error", "Enter Admin ID", parent=input_window)
                        return
                    mycursor.execute("SELECT * FROM AdminRecord WHERE AdminID=%s", (admin_id,))
                    record = mycursor.fetchone()
                    if record:
                        result_label.config(text=f"🔎 Found → ID: {record[0]}, Password: {record[1]}")
                    else:
                        result_label.config(text="❌ No Admin found")

                elif action == "Update":
                    if not admin_id or not password:
                        messagebox.showerror("Error", "Enter Admin ID and New Password", parent=input_window)
                        return
                    mycursor.execute("UPDATE AdminRecord SET Password=%s WHERE AdminID=%s", (password, admin_id))
                    mydb.commit()
                    result_label.config(text=f"✏ Updated password for Admin '{admin_id}'")

                input_window.destroy()

            tk.Button(input_window, text=action, font=FONT_BTN, bg="#D2B48C", command=perform_action).pack(pady=10, fill="x", padx=20)

        # Buttons for actions in Admin Management
        actions = ["Insert", "Search", "Update", "View All"]
        for act in actions:
            if act == "View All":
                tk.Button(subpanel, text=act, font=FONT_BTN, bg="#D2B48C",
                          command=lambda: [mycursor.execute("SELECT * FROM AdminRecord"),
                                           result_label.config(text="\n".join([f"ID: {r[0]}, Password: {r[1]}" for r in mycursor.fetchall()]) or "No admins found.")]).pack(pady=5, fill="x", padx=30)
            else:
                tk.Button(subpanel, text=act, font=FONT_BTN, bg="#D2B48C",
                          command=lambda a=act: open_input_panel(a)).pack(pady=5, fill="x", padx=30)

    # --- Main Panel Buttons ---
    tk.Button(panel, text="Admin Management", font=("Segoe UI", 12), bg="#D2B48C",
              command=open_admin_management).pack(pady=10, fill="x", padx=30)

    tk.Button(panel, text="User Management", font=("Segoe UI", 12), bg="#ff8b94",
              command=lambda: open_user_panel(panel)).pack(pady=10, fill="x", padx=30)

    tk.Button(panel, text="Book Management", font=("Segoe UI", 12), bg="#d1c4e9",
              command=lambda: open_book_panel(panel)).pack(pady=10, fill="x", padx=30)

# ------------------ User Functions ------------------
def show_popup(title, data, parent, headers=None):
    popup = tk.Toplevel(parent)
    popup.title(title)
    popup.geometry("700x400")
    popup.configure(bg="white")

    # Scrollable frame
    container = tk.Frame(popup, bg="white")
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container, bg="white")
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="white")

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Headers
    if headers:
        for col, header in enumerate(headers):
            tk.Label(scrollable_frame, text=header, font=("Segoe UI", 11, "bold"),
                     bg="lightgrey", borderwidth=1, relief="solid", width=15).grid(row=0, column=col)

    # Data
    for row_idx, row in enumerate(data, start=1):
        for col_idx, val in enumerate(row):
            tk.Label(scrollable_frame, text=str(val), font=("Segoe UI", 11),
                     bg="white", borderwidth=1, relief="solid", width=15).grid(row=row_idx, column=col_idx)

def open_user_panel(root):
    panel = tk.Toplevel(root)
    panel.title("User Panel")
    panel.geometry("350x450")
    panel.configure(bg="#FFC0CB")  # pink bg

    # --- Show total users ---
    def show_total_users():
        mycursor.execute("SELECT COUNT(*) FROM UserRecord")
        total = mycursor.fetchone()[0]
        tk.Label(panel, text=f"👤 Total Registered Users: {total}",
                 font=("Segoe UI", 13, "bold"), bg="#FFC0CB", fg="blue").pack(pady=5)

    # --- View Users ---
    def display_users():
        today = date.today()
        mycursor.execute("SELECT * FROM UserRecord")
        records = mycursor.fetchall()
        formatted = []
        overdue_summary = []

        for user in records:
            user_id = user[0]
            user_name = user[1]
            borrowed_books_raw = user[7]
            due_date = user[6]
            fine = 0

        # --- Borrowed books ---
            borrowed = borrowed_books_raw.split(",") if borrowed_books_raw else []
            book_names = []
            for b in borrowed:
                mycursor.execute("SELECT BookName FROM BookRecord WHERE BookID = %s", (b.strip(),))
                result = mycursor.fetchone()
                if result:
                    book_names.append(result[0])

        # --- Fine + reminder ---
            if due_date:
                try:
                    if isinstance(due_date, str):
                        due_date = datetime.strptime(due_date, "%Y-%m-%d").date()

                    if today > due_date:
                        fine_days = (today - due_date).days
                        fine = fine_days * 5
                        overdue_summary.append(f"{user_name} → ₹{fine}")

                    elif today == due_date:
                        borrowed_books = ", ".join(book_names) if book_names else "None"
                        overdue_summary.append(f"⚠ Due today: {user_name} must return {borrowed_books}")

                except Exception as e:
                    print("Date parsing error:", e)

        # --- Update fine in DB ---
            try:
                mycursor.execute("UPDATE UserRecord SET Fine = %s WHERE UserID = %s", (fine, user_id))
            except Exception as e:
                print(f"DB Update Error for {user_id}: {e}")

        # --- Prepare display data ---
            formatted.append((
            user_id,
            user_name,
            user[2],  # Password
            ", ".join(book_names) if book_names else "None",
            user[3] or "N/A",  # DateBorrowed
            user[4],           # NoOfBooksBorrowed
            user[5] or "N/A",  # DueDate
            fine               # Fine
        ))

        mydb.commit()  # ✅ Commit all at once

    # --- Show summary of overdue/due users ---
        if overdue_summary:
            messagebox.showinfo("📅 Fine Summary", "\n".join(overdue_summary))
        else:
            messagebox.showinfo("✅ Status", "No overdue fines today!")

    # --- Display updated table ---
        show_popup(
        "User Records",
        formatted,
        root,
        headers=[
            "UserID", "UserName", "Password", "BooksIssued",
            "DateBorrowed", "NoOfBooksBorrowed", "DueDate", "Fine"
        ]
    )


    # --- Insert User ---
    def insert_user():
        popup = tk.Toplevel(root)
        popup.title("Insert New User")
        popup.geometry("350x400")
        popup.configure(bg="#FFC0CB")

        tk.Label(popup, text="Insert User", font=("Segoe UI", 14, "bold"), bg="#FFC0CB").pack(pady=10)

        tk.Label(popup, text="User ID", font=("Segoe UI", 11), bg="#FFC0CB").pack()
        uid_entry = tk.Entry(popup, font=("Segoe UI", 11))
        uid_entry.pack(pady=5)

        tk.Label(popup, text="User Name", font=("Segoe UI", 11), bg="#FFC0CB").pack()
        uname_entry = tk.Entry(popup, font=("Segoe UI", 11))
        uname_entry.pack(pady=5)

        tk.Label(popup, text="Password", font=("Segoe UI", 11), bg="#FFC0CB").pack()
        pwd_entry = tk.Entry(popup, font=("Segoe UI", 11), show="*")
        pwd_entry.pack(pady=5)

        tk.Label(popup, text="User Type", font=("Segoe UI", 11), bg="#FFC0CB").pack()
        usertype_var = tk.StringVar(value="Student")
        tk.OptionMenu(popup, usertype_var, "Student", "Teacher").pack(pady=5)

        def save():
            uid = uid_entry.get().strip()
            uname = uname_entry.get().strip()
            pwd = pwd_entry.get().strip()
            utype = usertype_var.get()

            if not uid or not uname or not pwd or not utype:
                messagebox.showerror("Error", "All fields are required.", parent=popup)
                return

            mycursor.execute("""INSERT INTO UserRecord 
                                (UserID, UserName, Password, DateBorrowed, NoOfBooksBorrowed, DueDate, UserType, BorrowedBooks) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                             (uid, uname, pwd, None, 0, None, utype, None))
            mydb.commit()
            messagebox.showinfo("Success", "User inserted successfully.", parent=popup)
            popup.destroy()

        tk.Button(popup, text="Save User", font=("Segoe UI", 11), bg="#D2B48C", command=save).pack(pady=15)

    # --- Issue Book ---
    def issue_book_popup():
        popup = tk.Toplevel(root)
        popup.title("Issue Book")
        popup.geometry("300x250")
        popup.configure(bg="#FFC0CB")

        tk.Label(popup, text="Issue Book to User", font=("Segoe UI", 14, "bold"), bg="#FFC0CB").pack(pady=10)
        tk.Label(popup, text="User ID", bg="#FFC0CB").pack()
        uid_entry = tk.Entry(popup, width=25)
        uid_entry.pack(pady=5)

        tk.Label(popup, text="Book ID", bg="#FFC0CB").pack()
        book_entry = tk.Entry(popup, width=25)
        book_entry.pack(pady=5)

        tk.Button(popup, text="Issue Book", font=("Segoe UI", 11), bg="#D2B48C",
                  command=lambda: issue_book_to_user(uid_entry.get().strip(), book_entry.get().strip(), popup)
                  ).pack(pady=15)

    # --- Update Due Date ---
    def update_due_date():
        popup = tk.Toplevel(root)
        popup.title("Update Due Date")
        popup.geometry("300x250")
        popup.configure(bg="#FFC0CB")

        tk.Label(popup, text="Update Due Date", font=("Segoe UI", 14, "bold"), bg="#FFC0CB").pack(pady=10)
        tk.Label(popup, text="User ID", bg="#FFC0CB").pack()
        uid_entry = tk.Entry(popup)
        uid_entry.pack(pady=5)

        tk.Label(popup, text="New Due Date (YYYY-MM-DD)", bg="#FFC0CB").pack()
        due_entry = tk.Entry(popup)
        due_entry.pack(pady=5)

        def update():
            uid = uid_entry.get().strip()
            new_due = due_entry.get().strip()
            try:
                datetime.strptime(new_due, "%Y-%m-%d")  # validate date
                mycursor.execute("UPDATE UserRecord SET DueDate = %s WHERE UserID = %s", (new_due, uid))
                mydb.commit()
                messagebox.showinfo("Success", f"Due date updated for User '{uid}'.", parent=popup)
            except ValueError:
                messagebox.showerror("Invalid", "Enter date in YYYY-MM-DD format", parent=popup)

        tk.Button(popup, text="Update", font=("Segoe UI", 11), bg="#D2B48C", command=update).pack(pady=15)

    # --- Book Search (exclude borrowed) ---
    def open_book_search_popup():
        popup = tk.Toplevel(root)
        popup.title("Search Book")
        popup.geometry("400x350")
        popup.configure(bg="#FFC0CB")

        tk.Label(popup, text="Search Book By", font=("Segoe UI", 13, "bold"), bg="#FFC0CB").pack(pady=10)

        def search_by_field(field):
            value = simpledialog.askstring("Search", f"Enter {field} to search:", parent=popup)
            if not value:
                return

            query = f"""
                SELECT * FROM BookRecord 
                WHERE {field} LIKE %s 
                AND BookID NOT IN (
                    SELECT TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(BorrowedBooks, ',', n.n), ',', -1))
                    FROM UserRecord
                    JOIN (SELECT 1 n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 
                          UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10) n
                    ON CHAR_LENGTH(BorrowedBooks) - CHAR_LENGTH(REPLACE(BorrowedBooks, ',', '')) >= n.n-1
                    WHERE BorrowedBooks IS NOT NULL AND BorrowedBooks != ''
                )
            """
            mycursor.execute(query, (f"%{value}%",))
            records = mycursor.fetchall()

            if records:
                headers = [desc[0] for desc in mycursor.description]
                formatted = [list(record) for record in records]
                show_popup(f"Search Results - {field}", formatted, popup, headers=headers)
            else:
                messagebox.showinfo("Oops!", "Oops! No such book in our library!", parent=popup)

        tk.Button(popup, text="Book ID", font=("Segoe UI", 11),
                  bg="#D2B48C", command=lambda: search_by_field("BookID")).pack(pady=4, fill="x", padx=30)
        tk.Button(popup, text="Book Name", font=("Segoe UI", 11),
                  bg="#D2B48C", command=lambda: search_by_field("BookName")).pack(pady=4, fill="x", padx=30)
        tk.Button(popup, text="Language", font=("Segoe UI", 11),
                  bg="#D2B48C", command=lambda: search_by_field("Language")).pack(pady=4, fill="x", padx=30)
        tk.Button(popup, text="Genre", font=("Segoe UI", 11),
                  bg="#D2B48C", command=lambda: search_by_field("Genre")).pack(pady=4, fill="x", padx=30)

    # ------------------ Main User Panel Buttons ------------------
    tk.Label(panel, text="User Panel", font=("Segoe UI", 14, "bold"), bg="#FFC0CB").pack(pady=10)
    tk.Button(panel, text="👤 Show Total Users", font=("Segoe UI", 12), bg="#D2B48C",
              command=show_total_users).pack(pady=10, fill="x", padx=30)
    tk.Button(panel, text="View Users", font=("Segoe UI", 12), bg="#D2B48C",
              command=display_users).pack(pady=10, fill="x", padx=30)
    tk.Button(panel, text="Insert User", font=("Segoe UI", 12), bg="#D2B48C",
              command=insert_user).pack(pady=10, fill="x", padx=30)
    tk.Button(panel, text="Issue Book", font=("Segoe UI", 12), bg="#D2B48C",
              command=issue_book_popup).pack(pady=10, fill="x", padx=30)
    tk.Button(panel, text="Update Due Date", font=("Segoe UI", 12), bg="#D2B48C",
              command=update_due_date).pack(pady=10, fill="x", padx=30)
# ------------------ Book Panel ------------------
def open_book_panel(root):
    def show_book_stats():
        stats_popup = tk.Toplevel(root)
        stats_popup.title("📊 Book Statistics")
        stats_popup.geometry("400x250")
        stats_popup.configure(bg="ffe0ac")

        today = date.today()

        mycursor.execute("SELECT COUNT(*) FROM BookRecord")
        total_books = mycursor.fetchone()[0]

        mycursor.execute("SELECT COUNT(*) FROM UserRecord WHERE DueDate < %s AND BorrowedBooks IS NOT NULL AND BorrowedBooks != ''", (today,))
        overdue_books = mycursor.fetchone()[0]

        mycursor.execute("SELECT COUNT(*) FROM UserRecord WHERE DateBorrowed != %s AND DueDate = %s", (today, today))
        returned_today = mycursor.fetchone()[0]

        tk.Label(stats_popup, text=f"📚 Total Books: {total_books}", font=("Segoe UI", 12), bg="white").pack(pady=10)
        tk.Label(stats_popup, text=f"⏳ Overdue Books: {overdue_books}", font=("Segoe UI", 12), bg="white").pack(pady=10)
        tk.Label(stats_popup, text=f"🔁 Returned Today: {returned_today}", font=("Segoe UI", 12), bg="white").pack(pady=10)

    def insert_book():
        popup = tk.Toplevel(root)
        popup.title("Insert New Book")
        popup.geometry("400x500")
        popup.configure(bg="white")

        tk.Label(popup, text="Insert New Book", font=("Segoe UI", 14, "bold"), bg="white").pack(pady=10)

        fields = [
            ("Book ID", "book_id"),
            ("Book Name", "book_name"),
            ("Author", "author"),
            ("Publisher", "publisher"),
            ("Publishing Date (YYYY-MM-DD)", "pub_date"),
            ("Language", "language"),
            ("Genre", "genre"),
            ("StarRating","StarRating")
        ]

        entries = {}

        for label_text, var_name in fields:
            tk.Label(popup, text=label_text, font=("Segoe UI", 11), bg="white").pack(pady=2)
            entry = tk.Entry(popup, font=("Segoe UI", 11), width=35)
            entry.pack(pady=2)
            entries[var_name] = entry

        def save_book():
            book_id = entries["book_id"].get().strip()
            book_name = entries["book_name"].get().strip()
            author = entries["author"].get().strip()
            publisher = entries["publisher"].get().strip()
            pub_date = entries["pub_date"].get().strip()
            language = entries["language"].get().strip()
            genre = entries["genre"].get().strip()

            if not all([book_id, book_name, author, publisher, pub_date, language, genre]):
                messagebox.showerror("Error", "All fields are required.", parent=popup)
                return

            try:
                pub_date_obj = datetime.strptime(pub_date, "%Y-%m-%d").date()
                if pub_date_obj < date.today():
                    messagebox.showerror("Invalid Date", "Publishing date cannot be in the past.", parent=popup)
                    return
            except ValueError:
                messagebox.showerror("Invalid Format", "Publishing Date must be YYYY-MM-DD.", parent=popup)
                return

            mycursor.execute("""
                INSERT INTO BookRecord (BookID, BookName, Author, Publisher, PublishingDate, Language, Genre)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (book_id, book_name, author, publisher, pub_date, language, genre))
            mydb.commit()
            messagebox.showinfo("Success", f"Book '{book_name}' inserted successfully!", parent=popup)
            popup.destroy()

        tk.Button(popup, text="Save Book", font=("Segoe UI", 11), bg="#a8e6cf", command=save_book).pack(pady=20)

    def delete_book():
        field = simpledialog.askstring("Delete Book", "Enter field name (BookID, BookName, Author, etc.):")
        if not field:
            return
        value = simpledialog.askstring("Delete Book", f"Enter value for {field}:")
        if not value:
            return

        try:
            query = f"DELETE FROM BookRecord WHERE {field} = %s"
            mycursor.execute(query, (value,))
            mydb.commit()
            messagebox.showinfo("Deleted", f"Book(s) where {field} = '{value}' deleted successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete book(s).\n{str(e)}")

    def update_book():
        book_id = simpledialog.askstring("Update Book", "Enter Book ID of book to update:")
        if not book_id:
            return

        mycursor.execute("SELECT * FROM BookRecord WHERE BookID = %s", (book_id,))
        book = mycursor.fetchone()
        if not book:
            messagebox.showerror("Not Found", "No book found with that ID.")
            return

        popup = tk.Toplevel(root)
        popup.title("Update Book")
        popup.geometry("400x500")
        popup.configure(bg="white")

        tk.Label(popup, text="Update Book Info", font=("Segoe UI", 14, "bold"), bg="white").pack(pady=10)

        labels = ["Book Name", "Author", "Publisher", "Publishing Date (YYYY-MM-DD)", "Language", "Genre"]
        db_fields = ["BookName", "Author", "Publisher", "PublishingDate", "Language", "Genre"]
        entries = {}

        for i, label in enumerate(labels):
            tk.Label(popup, text=label, font=("Segoe UI", 11), bg="white").pack(pady=2)
            entry = tk.Entry(popup, font=("Segoe UI", 11), width=35)
            entry.pack(pady=2)
            entry.insert(0, book[i + 1])
            entries[db_fields[i]] = entry

        def save_changes():
            updates = []
            values = []
            for field, entry in entries.items():
                val = entry.get().strip()
                if val:
                    updates.append(f"{field} = %s")
                    values.append(val)

            if not updates:
                messagebox.showinfo("No Update", "No changes were made.", parent=popup)
                popup.destroy()
                return

            values.append(book_id)
            query = f"UPDATE BookRecord SET {', '.join(updates)} WHERE BookID = %s"
            mycursor.execute(query, values)
            mydb.commit()
            messagebox.showinfo("Success", "Book updated successfully!", parent=popup)
            popup.destroy()

        tk.Button(popup, text="Update Book", font=("Segoe UI", 11), bg="#a8e6cf", command=save_changes).pack(pady=15)

    def view_books():
        popup = tk.Toplevel(root)
        popup.title("All Books")
        popup.geometry("1100x600")
        popup.configure(bg="white")

        tk.Label(popup, text="📚 View All Books", font=("Segoe UI", 14, "bold"), bg="white").pack(pady=10)

        # --- Search bar ---
        search_frame = tk.Frame(popup, bg="white")
        search_frame.pack(pady=5)

        tk.Label(search_frame, text="Search:", font=("Segoe UI", 11), bg="white").pack(side="left", padx=5)
        search_entry = tk.Entry(search_frame, width=50, font=("Segoe UI", 11))
        search_entry.pack(side="left", padx=5)

        # --- Table frame ---
        table_frame = tk.Frame(popup, bg="white")
        table_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(table_frame, bg="white")
        scrollbar_y = tk.Scrollbar(table_frame, orient="vertical", command=canvas.yview)
        scrollbar_x = tk.Scrollbar(popup, orient="horizontal", command=canvas.xview)
        scrollable_frame = tk.Frame(canvas, bg="white")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")

        # --- Display function ---
        def display_books_in_popup(keyword=""):
            for widget in scrollable_frame.winfo_children():
                widget.destroy()

            # Headers
            headers = ["BookID", "BookName", "Author", "Publisher", "PublishingDate", "Language", "Genre", "Status"]
            for col, header in enumerate(headers):
                tk.Label(scrollable_frame, text=header, font=("Segoe UI", 11, "bold"),
                         borderwidth=1, relief="solid", width=20, bg="#dfe6e9").grid(row=0, column=col)

            # Query books
            fields = ["BookID", "BookName", "Author", "Publisher", "Language", "Genre"]
            query = "SELECT * FROM BookRecord"
            values = []
            if keyword:
                keyword = keyword.lower()
                conditions = [f"LOWER({field}) LIKE %s" for field in fields]
                query += " WHERE " + " OR ".join(conditions)
                values = [f"%{keyword}%"] * len(fields)

            mycursor.execute(query, values)
            book_records = mycursor.fetchall()

            # Borrowed mapping
            borrowed_map = {}
            mycursor.execute("SELECT UserID, BorrowedBooks FROM UserRecord WHERE BorrowedBooks IS NOT NULL AND BorrowedBooks != ''")
            for user_id, borrowed_books in mycursor.fetchall():
                if borrowed_books:
                    for book_id in borrowed_books.split(","):
                        borrowed_map[book_id.strip()] = user_id

            # Display rows
            for row_index, row in enumerate(book_records, start=1):
                book_id = row[0]
                is_borrowed = book_id in borrowed_map
                row_bg = "#f11414" if is_borrowed else "white"

                # Book fields
                for col_index, cell in enumerate(row):
                    tk.Label(scrollable_frame, text=cell, font=("Segoe UI", 10),
                             borderwidth=1, relief="solid", width=20, bg=row_bg).grid(row=row_index, column=col_index)

                # Status column
                status = f"Borrowed by {borrowed_map[book_id]}" if is_borrowed else "Available"
                status_bg = "#bb072b" if is_borrowed else "#b8e994"
                tk.Label(scrollable_frame, text=status, font=("Segoe UI", 10, "bold"),
                         borderwidth=1, relief="solid", width=20, bg=status_bg).grid(row=row_index, column=7)

        # Search button
        def perform_search():
            keyword = search_entry.get().strip()
            display_books_in_popup(keyword)

        tk.Button(search_frame, text="Search", font=("Segoe UI", 10), bg="#a8e6cf",
                  command=perform_search).pack(side="left", padx=10)

        display_books_in_popup()

       

    # Main Book Panel Window
    panel = tk.Toplevel(root)
    panel.title("Book Panel")
    panel.geometry("1100x600")
    panel.configure(bg="white")

    tk.Label(panel, text="Book Management", font=("Segoe UI", 14, "bold"), bg="white").pack(pady=10)
    tk.Button(panel, text="📊 Show Book Stats", font=("Segoe UI", 12), command=show_book_stats).pack(pady=5, fill="x", padx=30)
    tk.Button(panel, text="View Books", font=("Segoe UI", 12), command=view_books).pack(pady=5, fill="x", padx=30)
    tk.Button(panel, text="Insert Book", font=("Segoe UI", 12), command=insert_book).pack(pady=5, fill="x", padx=30)
    tk.Button(panel, text="Delete Book", font=("Segoe UI", 12), command=delete_book).pack(pady=5, fill="x", padx=30)
    tk.Button(panel, text="Update Book", font=("Segoe UI", 12), command=update_book).pack(pady=5, fill="x", padx=30)

# ------------------ Login GUI Setup ------------------
root = tk.Tk()
root.title("Library Login")
root.geometry("800x600")
root.resizable(False, False)

try:
    bg_img = Image.open(r"C:\Users\S Jananii\OneDrive\Desktop\codetantra\Library-Management-System-main\library_bg.png")  # ✅ Replace with actual path if needed
    bg_img = bg_img.resize((800, 600), Image.Resampling.LANCZOS)
    bg_photo = ImageTk.PhotoImage(bg_img)
    bg_label = tk.Label(root, image=bg_photo)
    bg_label.image = bg_photo  # 
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
except Exception as e:
    print("Background image error:", e)
    root.configure(bg="#ffe6f0")

label_font = ("Segoe UI", 13, "bold")
entry_font = ("Segoe UI", 14)
base_y = 250
center_x = 400

tk.Label(root, text="User ID", font=label_font, bg="#eac4d5").place(x=center_x, y=base_y, anchor='center')
user_entry = tk.Entry(root, width=35, font=entry_font)
user_entry.place(x=center_x - 120, y=base_y + 30)

tk.Label(root, text="Password", font=label_font, bg="#eac4d5").place(x=center_x, y=base_y + 80, anchor='center')

pass_entry = tk.Entry(root, show="*", width=35, font=entry_font)
pass_entry.place(x=center_x - 120, y=base_y + 110)

def toggle_password():
    if pass_entry.cget('show') == '':
        pass_entry.config(show='*')
        toggle_btn.config(text="🔒")
    else:
        pass_entry.config(show='')
        toggle_btn.config(text="👁️")

toggle_btn = tk.Button(root, text="🔒", bd=0, bg="#eac4d5", font=("Segoe UI", 12), command=toggle_password)
toggle_btn.place(x=center_x + 200, y=base_y + 108)
toggle_var = tk.StringVar(value="user")

tk.Radiobutton(root, text="User", variable=toggle_var, value="user", font=("Segoe UI", 12),
               bg="#ffe6f0", fg="blue", selectcolor="#fdf5ce",
               command=lambda: usertype_frame.place(x=center_x - 120, y=base_y + 160)
              ).place(x=center_x - 120, y=base_y - 40)  # Moved farther left

tk.Radiobutton(root, text="Admin", variable=toggle_var, value="admin", font=("Segoe UI", 12),
               bg="#ffe6f0", fg="green", selectcolor="#a8e6cf",
               command=lambda: usertype_frame.place_forget()
              ).place(x=center_x + 80, y=base_y - 40)  # Moved farther right

usertype_frame = tk.Frame(root, bg="#ffe6f0")

tk.Label(usertype_frame, text="User Type", font=("Segoe UI", 11), bg="#ffe6f0").pack(anchor="w")
usertype_var = tk.StringVar(value="Student")  # default value
tk.OptionMenu(usertype_frame, usertype_var, "Student", "Teacher").pack()

def open_logged_in_user_panel(user_id):
    panel = tk.Toplevel(root)
    panel.title("User Dashboard")
    panel.geometry("400x500")
    panel.configure(bg="white")

    tk.Label(panel, text=f"Welcome {user_id}", font=("Segoe UI", 14, "bold"), bg="white").pack(pady=10)

    # -------- View Books --------
    def view_available_books():
        popup = tk.Toplevel(panel)
        popup.title("Available Books")
        popup.geometry("900x500")
        popup.configure(bg="white")

        search_frame = tk.Frame(popup, bg="white")
        search_frame.pack(pady=5)
        search_entry = tk.Entry(search_frame, width=40, font=("Segoe UI", 11))
        search_entry.pack(side="left", padx=5)

        table_frame = tk.Frame(popup, bg="white")
        table_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(table_frame, bg="white")
        scrollbar_y = tk.Scrollbar(table_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_y.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")

        def display_available_books(keyword=""):
            for widget in scrollable_frame.winfo_children():
                widget.destroy()

            fields = ["BookID", "BookName", "Author", "Language", "Genre","StarRating"]
            query = "SELECT BookId,Bookname,Author,Language,Genre,StarRating FROM BookRecord"
            values = []
            if keyword:
                keyword = keyword.lower()
                conditions = [f"LOWER({field}) LIKE %s" for field in fields]
                query += " WHERE " + " OR ".join(conditions)
                values = [f"%{keyword}%"] * len(fields)

            mycursor.execute(query, values)
            all_books = mycursor.fetchall()
            mycursor.execute("SELECT BorrowedBooks FROM UserRecord WHERE BorrowedBooks IS NOT NULL AND BorrowedBooks != ''")
            borrowed_ids = set()
            for row in mycursor.fetchall():
                if row[0]:
                    borrowed_ids.update([b.strip().lower() for b in row[0].split(",") if b.strip()])
            available_books = [book for book in all_books if str(book[0]).strip().lower() not in borrowed_ids]


            headers = ["BookID", "BookName", "Author", "Language", "Genre","Rating"]

            if not available_books:
                tk.Label(scrollable_frame, text="Oops! no such book in our library!",
                        font=("Segoe UI", 12, "bold"), fg="red", bg="white").pack(pady=20)
                return

            # headers
            for col, header in enumerate(headers):
                tk.Label(scrollable_frame, text=header, font=("Segoe UI", 11, "bold"),
                        borderwidth=1, relief="solid", width=20, bg="#dfe6e9").grid(row=0, column=col)

            # rows
            for row_index, row in enumerate(available_books, start=1):
                for col_index, cell in enumerate(row):
                    tk.Label(scrollable_frame, text=cell, font=("Segoe UI", 10),
                            borderwidth=1, relief="solid", width=20, bg="white").grid(row=row_index, column=col_index)

        def do_search():
            display_available_books(search_entry.get().strip())

        tk.Button(search_frame, text="Search", font=("Segoe UI", 10), bg="#a8e6cf",
                command=do_search).pack(side="left", padx=5)

        display_available_books()

    # -------- Borrow Book --------
    def borrow_book():
        book_id = simpledialog.askstring("Borrow Book", "Enter Book ID to borrow:", parent=panel)
        if not book_id:
            return
        mycursor.execute("SELECT BorrowedBooks FROM UserRecord WHERE UserID=%s", (user_id,))
        record = mycursor.fetchone()
        borrowed_books = record[0].split(",") if record and record[0] else []
        if len(borrowed_books) >= 3:
            messagebox.showerror("Limit Reached", "Max 3 books allowed.", parent=panel)
            return
        issue_book_to_user(user_id, book_id, panel)

    # -------- Return Book --------
    def return_book():
        mycursor.execute("SELECT BorrowedBooks FROM UserRecord WHERE UserID=%s", (user_id,))
        book_info = mycursor.fetchone()
        if not book_info or not book_info[0]:
            messagebox.showerror("No Book", "No books borrowed.", parent=panel)
            return
        borrowed_books = [b.strip() for b in book_info[0].split(",") if b.strip()]
        if len(borrowed_books) == 1:
            mycursor.execute("UPDATE UserRecord SET BorrowedBooks=NULL, DateBorrowed=NULL, DueDate=NULL, NoOfBooksBorrowed=0 WHERE UserID=%s", (user_id,))
            mydb.commit()
            messagebox.showinfo("Returned", f"Book '{borrowed_books[0]}' returned successfully!", parent=panel)
        else:
            book_id = simpledialog.askstring("Return Book", f"Enter Book ID to return:\n{', '.join(borrowed_books)}", parent=panel)
            if not book_id or book_id not in borrowed_books:
                messagebox.showerror("Invalid", "Book ID not in your list.", parent=panel)
                return
            borrowed_books.remove(book_id)
            new_borrowed = ",".join(borrowed_books)
            today = date.today()
            mycursor.execute("SELECT UserType FROM UserRecord WHERE UserID = %s", (user_id,))
            utype = mycursor.fetchone()[0].lower()
            due_days = 14 if utype == "teacher" else 7
            new_due = today + timedelta(days=due_days)
            mycursor.execute("UPDATE UserRecord SET BorrowedBooks=%s, NoOfBooksBorrowed=%s, DateBorrowed=%s, DueDate=%s WHERE UserID=%s",
                             (new_borrowed, len(borrowed_books), today, new_due, user_id))
            mydb.commit()
            messagebox.showinfo("Returned", f"Book '{book_id}' returned successfully!", parent=panel)

    # -------- My Book Details --------
    def my_book_details():
        mycursor.execute("SELECT BorrowedBooks, DateBorrowed, DueDate FROM UserRecord WHERE UserID=%s", (user_id,))
        result = mycursor.fetchone()
        if not result:
            messagebox.showinfo("No Record", "User not found.", parent=panel)
            return
        borrowed_str, date_borrowed, due_date = result
        if not borrowed_str:
            messagebox.showinfo("No Books", "You haven't borrowed any books.", parent=panel)
            return
        book_ids = [b.strip() for b in borrowed_str.split(",") if b.strip()]
        today = date.today()
        fine = 0
        if due_date and today > due_date:
            fine = (today - due_date).days * 5
        records = []
        for book_id in book_ids:
            mycursor.execute("SELECT BookID, BookName FROM BookRecord WHERE BookID=%s", (book_id,))
            book = mycursor.fetchone()
            if book:
                records.append((book[0], book[1], date_borrowed, due_date, f"₹{fine}" if fine else "No Fine"))
        show_popup("My Book Details", records, panel, headers=["BookID", "BookName", "Borrowed On", "Due Date", "Fine"])

    # -------- Buttons --------
    tk.Button(panel, text="View Books", font=("Segoe UI", 12), bg="#a8e6cf", command=view_available_books).pack(pady=10, fill="x", padx=30)
    tk.Button(panel, text="Borrow Book", font=("Segoe UI", 12), bg="#ffe0ac", command=borrow_book).pack(pady=10, fill="x", padx=30)
    tk.Button(panel, text="Return Book", font=("Segoe UI", 12), bg="#ff8b94", command=return_book).pack(pady=10, fill="x", padx=30)
    tk.Button(panel, text="My Book Details", font=("Segoe UI", 12), bg="#d1c4e9", command=my_book_details).pack(pady=10, fill="x", padx=30)

# ------------------- Replace your login() with this -------------------
def login():
    uid = user_entry.get().strip()
    pwd = pass_entry.get().strip()
    role = toggle_var.get()

    if not uid or not pwd:
        messagebox.showerror("Error", "Please enter both User ID and Password.")
        return

    if role == "admin":
        mycursor.execute("SELECT Password FROM AdminRecord WHERE AdminID = %s", (uid,))
    else:
        mycursor.execute("SELECT Password FROM UserRecord WHERE UserID = %s", (uid,))
    result = mycursor.fetchone()

    if result and result[0] == pwd:
        messagebox.showinfo("Success", f"Welcome {uid}!")

        if role == "admin":
            open_admin_panel(root)
        else:
            #Fine Alert for Due Books
            mycursor.execute("SELECT BorrowedBooks, DueDate FROM UserRecord WHERE UserID = %s", (uid,))
            user_data = mycursor.fetchone()
            borrowed_books, due_date = user_data[0], user_data[1]
            
            if borrowed_books and due_date:
                today = date.today()
                due_date = due_date if isinstance(due_date, date) else due_date.date()
                
                if today > due_date:
                    fine_days = (today - due_date).days
                    fine = fine_days * 5  # ₹5 per day
                    messagebox.showwarning("Fine Alert", f"You have an overdue book.\nFine: ₹{fine}")
                elif today == due_date:
                    messagebox.showinfo("Reminder", f"Today is the DUE DATE to return your books ({borrowed_books}). Please return them today:)")

            
            open_logged_in_user_panel(uid)

    else:
        messagebox.showerror("Login Failed", "Incorrect credentials.")

def new_user_popup():
    popup = tk.Toplevel(root)
    popup.title("Register New User")
    popup.geometry("350x420")
    popup.configure(bg="white")
    popup.grab_set()

    tk.Label(popup, text="New User Registration", font=("Segoe UI", 14, "bold"), bg="#ffe6f0", fg="#0099cc").pack(pady=10)

    tk.Label(popup, text="User ID", bg="white", font=("Segoe UI", 11)).pack()
    uid_entry = tk.Entry(popup, width=30, font=("Segoe UI", 11))
    uid_entry.pack()

    tk.Label(popup, text="User Name", bg="white", font=("Segoe UI", 11)).pack()
    uname_entry = tk.Entry(popup, width=30, font=("Segoe UI", 11))
    uname_entry.pack()

    tk.Label(popup, text="Password", bg="white", font=("Segoe UI", 11)).pack()
    pwd_entry = tk.Entry(popup, width=30, font=("Segoe UI", 11), show="*")
    pwd_entry.pack()

    #Add User Type
    tk.Label(popup, text="User Type", bg="white", font=("Segoe UI", 11)).pack()
    usertype_var = tk.StringVar(value="Student")  # Default value
    tk.OptionMenu(popup, usertype_var, "Student", "Teacher").pack()

    def save_user():
        uid = uid_entry.get().strip()
        uname = uname_entry.get().strip()
        pwd = pwd_entry.get().strip()
        utype = usertype_var.get()

        if not uid or not uname or not pwd or not utype:
            messagebox.showerror("Error", "All fields are required.", parent=popup)
            return

        mycursor.execute("""
            INSERT INTO UserRecord 
            (UserID, UserName, Password, DateBorrowed, NoOfBooksBorrowed, DueDate, UserType, BorrowedBooks)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (uid, uname, pwd, None, None, 0, None, utype))
        mydb.commit()
        messagebox.showinfo("Success", "User registered successfully!", parent=popup)
        popup.destroy()

    tk.Button(popup, text="Register", bg="#fdf5ce", fg="black", font=("Segoe UI", 11), command=save_user).pack(pady=15)

login_button = tk.Button(root, text="Login", command=login, font=("Segoe UI", 12),
                         bg="#a8e6cf", fg="black", width=15)
login_button.place(x=center_x - 110, y=base_y + 220)

register_button = tk.Button(root, text="New User?", command=new_user_popup, font=("Segoe UI", 12),
                            bg="#fdf5ce", fg="black", width=15)
register_button.place(x=center_x + 20, y=base_y + 220)
if toggle_var.get() == "user":
    usertype_frame.place(x=center_x - 120, y=base_y + 160)

root.mainloop()

