import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import mysql.connector
from tkinter import simpledialog

# ------------------ Database Connection ------------------
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="Jananii@Harinii27",
    database="Library"
)
mycursor = mydb.cursor()

# ------------------ Main Window ------------------
root = tk.Tk()
root.title("Library Login")
root.geometry("800x600")
root.resizable(False, False)

# ------------------ Background Image ------------------
try:
    bg_img = Image.open(r"C:\Users\S Jananii\OneDrive\Desktop\codetantra\Library-Management-System-main\library_bg.png")
    bg_img = bg_img.resize((800, 600), Image.Resampling.LANCZOS)
    bg_photo = ImageTk.PhotoImage(bg_img)
    bg_label = tk.Label(root, image=bg_photo)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
except:
    root.configure(bg="#ffe6f0")

# ------------------ Fonts and Colors ------------------
label_font = ("Segoe UI", 13, "bold")
entry_font = ("Segoe UI", 13)

# ------------------ Positioning ------------------
base_y = 250  # Lowered for visibility of background logo/title
center_x = 400

# ------------------ User ID and Password ------------------
tk.Label(root, text="User ID", font=label_font, bg="#eac4d5", fg="black").place(x=center_x, y=base_y, anchor='center')
user_entry = tk.Entry(root, width=30, font=entry_font)
user_entry.place(x=center_x - 100, y=base_y + 30)

tk.Label(root, text="Password", font=label_font, bg="#eac4d5", fg="black").place(x=center_x, y=base_y + 80, anchor='center')
pass_entry = tk.Entry(root, show="*", width=30, font=entry_font)
pass_entry.place(x=center_x - 100, y=base_y + 110)

# ------------------ Login Function ------------------
def login():
    uid = user_entry.get().strip()
    pwd = pass_entry.get().strip()
    role = toggle_var.get()

    if not uid or not pwd:
        messagebox.showerror("Error", "Please enter both User ID and Password.")
        return

    try:
        if role == "admin":
            mycursor.execute("SELECT Password FROM AdminRecord WHERE AdminID = %s", (uid,))
        else:
            mycursor.execute("SELECT Password FROM UserRecord WHERE UserID = %s", (uid,))
        result = mycursor.fetchone()

        if result and result[0] == pwd:
            messagebox.showinfo("Success", f"Welcome {uid}!")
            if role == "admin":
                open_admin_panel()  # Call to admin panel from the second script
            else:
                root.destroy()
        else:
            messagebox.showerror("Login Failed", "Incorrect credentials.")
    except Exception as e:
        messagebox.showerror("Database Error", str(e))

# ------------------ Register Function ------------------
def new_user_popup():
    popup = tk.Toplevel(root)
    popup.title("Register New User")
    popup.geometry("350x300")
    popup.configure(bg="white")
    popup.grab_set()

    tk.Label(popup, text="New User Registration", font=("Segoe UI", 14, "bold"), bg="white", fg="#0099cc").pack(pady=10)

    tk.Label(popup, text="User ID", bg="white", font=("Segoe UI", 11)).pack()
    uid_entry = tk.Entry(popup, width=30, font=("Segoe UI", 11))
    uid_entry.pack()

    tk.Label(popup, text="User Name", bg="white", font=("Segoe UI", 11)).pack()
    uname_entry = tk.Entry(popup, width=30, font=("Segoe UI", 11))
    uname_entry.pack()

    tk.Label(popup, text="Password", bg="white", font=("Segoe UI", 11)).pack()
    pwd_entry = tk.Entry(popup, width=30, font=("Segoe UI", 11), show="*")
    pwd_entry.pack()

    def save_user():
        uid = uid_entry.get().strip()
        uname = uname_entry.get().strip()
        pwd = pwd_entry.get().strip()

        if not uid or not uname or not pwd:
            messagebox.showerror("Error", "All fields are required.", parent=popup)
            return

        try:
            mycursor.execute("INSERT INTO UserRecord (UserID, UserName, Password, BookID) VALUES (%s, %s, %s, NULL)",
                             (uid, uname, pwd))
            mydb.commit()
            messagebox.showinfo("Success", "User registered successfully!", parent=popup)
            popup.destroy()
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Could not register user.\n{err}", parent=popup)

    tk.Button(popup, text="Register", bg="#fdf5ce", fg="black",
              font=("Segoe UI", 11), command=save_user).pack(pady=15)

# ------------------ Buttons ------------------
tk.Button(root, text="Login", width=20, font=("Segoe UI", 12, "bold"),
          bg="#a8e6cf", fg="black", command=login).place(x=center_x - 100, y=base_y + 160)

tk.Button(root, text="New User? Register", width=20, font=("Segoe UI", 11),
          bg="#fdf5ce", command=new_user_popup).place(x=center_x - 100, y=base_y + 200)

# ------------------ User/Admin Toggle ------------------
toggle_var = tk.StringVar(value="user")
toggle_frame = tk.Frame(root, bg="white")
toggle_frame.place(x=center_x - 70, y=base_y + 250)

tk.Radiobutton(toggle_frame, text="User", variable=toggle_var, value="user",
               bg="white", font=("Segoe UI", 12), fg="darkblue",
               selectcolor="#d1c4e9", activebackground="#ffffff").pack(side=tk.LEFT, padx=15)

tk.Radiobutton(toggle_frame, text="Admin", variable=toggle_var, value="admin",
               bg="white", font=("Segoe UI", 12), fg="darkgreen",
               selectcolor="#ffe0b2", activebackground="#ffffff").pack(side=tk.LEFT, padx=15)
def display_admin():
    try:
        mycursor.execute("SELECT * FROM AdminRecord")
        records = mycursor.fetchall()
        if not records:
            messagebox.showinfo("No Records", "No admin records found.")
            return

        result = ""
        for idx, row in enumerate(records, 1):
            result += f"Admin {idx}:\n  ID: {row[0]}\n  Password: {row[1]}\n\n"

        show_popup("Admin Records", result)
    except Exception as e:
        messagebox.showerror("Error", str(e))
        
def insert_admin():
    admin_id = simpledialog.askstring("Insert Admin", "Enter new Admin ID:")
    password = simpledialog.askstring("Insert Admin", "Enter password:", show="*")
    if not admin_id or not password:
        return
    try:
        mycursor.execute("INSERT INTO AdminRecord (AdminID, Password) VALUES (%s, %s)", (admin_id, password))
        mydb.commit()
        messagebox.showinfo("Success", "Admin inserted successfully.")
    except mysql.connector.Error as err:
        messagebox.showerror("Error", str(err))

def delete_admin():
    admin_id = simpledialog.askstring("Delete Admin", "Enter Admin ID to delete:")
    if not admin_id:
        return
    mycursor.execute("DELETE FROM AdminRecord WHERE AdminID=%s", (admin_id,))
    mydb.commit()
    messagebox.showinfo("Deleted", f"Admin '{admin_id}' deleted successfully.")

def search_admin():
    admin_id = simpledialog.askstring("Search Admin", "Enter Admin ID to search:")
    if not admin_id:
        return
    mycursor.execute("SELECT * FROM AdminRecord WHERE AdminID=%s", (admin_id,))
    record = mycursor.fetchone()
    if record:
        show_popup("Admin Found", f"Admin ID: {record[0]}\nPassword: {record[1]}")
    else:
        messagebox.showerror("Not Found", "Admin not found.")

def update_admin():
    admin_id = simpledialog.askstring("Update Admin", "Enter Admin ID to update:")
    new_password = simpledialog.askstring("Update Password", "Enter new password:", show="*")
    if not admin_id or not new_password:
        return
    mycursor.execute("UPDATE AdminRecord SET Password=%s WHERE AdminID=%s", (new_password, admin_id))
    mydb.commit()
    messagebox.showinfo("Updated", f"Password updated for Admin '{admin_id}'.")

def show_popup(title, content):
    popup = tk.Toplevel(root)
    popup.title(title)
    popup.geometry("400x300")
    popup.configure(bg="white")

    text = tk.Text(popup, font=("Segoe UI", 11), wrap="word", bg="white")
    text.insert("1.0", content)
    text.config(state="disabled")
    text.pack(padx=10, pady=10, fill="both", expand=True)

    # These ensure it shows properly
    popup.transient(root)
    popup.grab_set()
    popup.focus_force()

# ------------------ Admin Panel ------------------
def open_admin_panel():
    panel = tk.Toplevel(root)
    panel.title("Admin Panel")
    panel.geometry("300x400")
    panel.configure(bg="#fff")

    tk.Label(panel, text="Admin Management", font=("Segoe UI", 14, "bold"), bg="white").pack(pady=10)

    tk.Button(panel, text="View Admins", font=("Segoe UI", 12), command=display_admin).pack(pady=10, fill="x", padx=30)
    tk.Button(panel, text="Insert Admin", font=("Segoe UI", 12), command=insert_admin).pack(pady=10, fill="x", padx=30)
    tk.Button(panel, text="Delete Admin", font=("Segoe UI", 12), command=delete_admin).pack(pady=10, fill="x", padx=30)
    tk.Button(panel, text="Search Admin", font=("Segoe UI", 12), command=search_admin).pack(pady=10, fill="x", padx=30)
    tk.Button(panel, text="Update Admin", font=("Segoe UI", 12), command=update_admin).pack(pady=10, fill="x", padx=30)
root.mainloop()