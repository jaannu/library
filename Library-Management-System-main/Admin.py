import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import mysql.connector

# ------------------ Database Connection ------------------
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="Jananii@Harinii27",
    database="Library"
)
mycursor = mydb.cursor()

# ------------------ Admin Functions ------------------
def display_admin():
    mycursor.execute("SELECT * FROM AdminRecord")
    records = mycursor.fetchall()
    if not records:
        messagebox.showinfo("No Records", "No admin records found.")
        return
    result = ""
    for idx, row in enumerate(records, 1):
        result += f"Admin {idx}:\n  ID: {row[0]}\n  Password: {row[1]}\n\n"
    show_popup("Admin Records", result)

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
    text = tk.Text(popup, font=("Segoe UI", 11), wrap="word")
    text.insert("1.0", content)
    text.config(state="disabled")
    text.pack(padx=10, pady=10, fill="both", expand=True)

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