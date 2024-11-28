import customtkinter as ctk
import sqlite3
from tkinter import filedialog
from PIL import Image, ImageTk
import os

app = ctk.CTk()
app.title("Inventory Management")

width= app.winfo_screenwidth() 
height= app.winfo_screenheight()
app.geometry("%dx%d" % (width, height))

# Database setup
conn = sqlite3.connect("inventory.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    image_path TEXT,
    cargo_fee REAL,
    original_price REAL,
    selling_price REAL,
    quantity INTEGER,
    sold_quantity INTEGER DEFAULT 0
)
""")
conn.commit()

# Sidebar Menu
menu_frame = ctk.CTkFrame(app, width=300, corner_radius=0)
menu_frame.grid(row=0, column=0, sticky="ns")

menu_buttons = ["All Products", "Inventory", "Add New Product", "Calculation"]
selected_tab = ctk.StringVar(value="All Products")

def switch_tab(tab_name):
    selected_tab.set(tab_name)
    for widget in content_frame.winfo_children():
        widget.destroy()
    if tab_name == "All Products":
        display_all_products()
    elif tab_name == "Inventory":
        display_inventory()
    elif tab_name == "Add New Product":
        display_add_new_product()
    elif tab_name == "Calculation":
        display_calculation()
        
    for btn in menu_buttons:
            button = menu_frame.winfo_children()[menu_buttons.index(btn)]
            if btn == tab_name:
                button.configure(fg_color="royalblue")
            else:
                button.configure(fg_color=("darkslategray", "darkslategray"))

for btn in menu_buttons:
    ctk.CTkButton(menu_frame, text=btn, command=lambda b=btn: switch_tab(b), width=150).pack(pady=10, padx=10)

# Main Content Area
content_frame = ctk.CTkScrollableFrame(app)
content_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
app.grid_rowconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=1)

# Helper Function: Display Product Image
def display_product_image(image_path, parent_frame):
    try:
        img = Image.open(image_path)
        img = img.resize((300, 150))
        img_tk = ImageTk.PhotoImage(img)
        label = ctk.CTkLabel(parent_frame, image=img_tk)
        label.image = img_tk
        label.pack(side="left", padx=10)
    except Exception:
        ctk.CTkLabel(parent_frame, text="No Image", text_color="gray").pack(side="left", padx=10)

# Functions for Tabs
def display_all_products():
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    for product in products:
        frame = ctk.CTkFrame(content_frame, height=100)
        frame.pack(pady=5, fill="x")

        display_product_image(product[2], frame)

        original_quantity = product[6] + product[7]
        details = f"Name: {product[1]} | Price: ₮{product[5]} | Quantity: {product[6]}"
        ctk.CTkLabel(frame, text=details, font=("Arial", 12)).pack(side="left", padx=15)

        if original_quantity > 0:
            progress_percent = (product[6] / original_quantity)
            progress_bar = ctk.CTkProgressBar(frame, width=200, progress_color="cyan", fg_color="royalblue" )
            progress_bar.set(progress_percent)
            progress_bar.pack(side="left", padx=15)
            
        details1 = f"Sold: {product[7]}"
        ctk.CTkLabel(frame, text=details1, font=("Arial", 12)).pack(side="left", padx=15)
        
        if original_quantity > 0:
            progress_percent1 = (product[7] / original_quantity)
            progress_bar = ctk.CTkProgressBar(frame, width=200, progress_color="lawngreen", fg_color="forestgreen" )
            progress_bar.set(progress_percent1)
            progress_bar.pack(side="left", padx=15)
            
def display_inventory():
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    for product in products:
        frame = ctk.CTkFrame(content_frame, height=200)
        frame.pack(pady=5, fill="x", padx=10)

        display_product_image(product[2], frame)

        original_quantity = product[6] + product[7]

        details = (
            f"Name: {product[1]}\nCargo Fee: ₮{product[3]}\nOriginal Price: ₮{product[4]}\n"
            f"Selling Price: ₮{product[5]}\nOriginal Quantity: {original_quantity}\n"
            f"Quantity Left: {product[6]} | Sold: {product[7]}"
        )
        ctk.CTkLabel(frame, text=details, font=("Arial", 12)).pack(side="left", padx=10)

        # Entry for sold quantity - now inside the loop!
        sold_entry = ctk.CTkEntry(frame, placeholder_text="Enter sold quantity", width=150)
        sold_entry.pack(side="right", padx=10, pady=10)

        def update_sold_quantity(product_id, current_quantity, current_sold_quantity, entry):
            try:
                sold_qty = int(entry.get())
                if sold_qty <= 0:
                    raise ValueError("Quantity must be greater than 0.")
                if sold_qty > current_quantity:
                    ctk.CTkLabel(frame, text="Insufficient stock!", text_color="red").pack(side="bottom", pady=5)
                    return

                # Update database
                new_quantity = current_quantity - sold_qty
                new_sold_quantity = current_sold_quantity + sold_qty
                cursor.execute(
                    "UPDATE products SET quantity = ?, sold_quantity = ? WHERE id = ?",
                    (new_quantity, new_sold_quantity, product_id)
                )
                conn.commit()

                # Refresh the inventory tab
                switch_tab("Inventory")

            except ValueError:
                ctk.CTkLabel(frame, text="Invalid input! Enter a valid number.", text_color="red").pack(side="bottom", pady=5)

        ctk.CTkButton(
            frame,
            text="Sold",
            command=lambda pid=product[0], qty=product[6], sold=product[7], e=sold_entry: update_sold_quantity(pid, qty, sold, e)
        ).pack(side="right", padx=10)

        ctk.CTkButton(frame, text="Delete", command=lambda pid=product[0]: delete_product(pid)).pack(side="left", padx=10)

def display_add_new_product():
    def upload_image():
        file_path = filedialog.askopenfilename(
            title="Select Product Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        if file_path:
            # Display selected image path in the UI
            image_path_entry.configure(state="normal")
            image_path_entry.delete(0, "end")
            image_path_entry.insert(0, file_path)
            image_path_entry.configure(state="readonly")

    def save_product():
        name = name_entry.get()
        cargo_fee = float(cargo_fee_entry.get())
        original_price = float(original_price_entry.get())
        selling_price = float(selling_price_entry.get())
        quantity = int(quantity_entry.get())
        image_path = image_path_entry.get()

        # Check if the image file exists before saving
        if not os.path.isfile(image_path):
            ctk.CTkLabel(content_frame, text="Invalid image path. Please upload a valid image.", text_color="red").pack(pady=10)
            return

        # Save to the database
        cursor.execute(
            "INSERT INTO products (name, image_path, cargo_fee, original_price, selling_price, quantity) VALUES (?, ?, ?, ?, ?, ?)",
            (name, image_path, cargo_fee, original_price, selling_price, quantity),
        )
        conn.commit()

        # Clear the form and refresh the tab
        switch_tab("All Products")

    # Components for adding a product
    ctk.CTkLabel(content_frame, text="Add New Product", font=("Arial", 18, "bold")).pack(pady=10)
    
    name_entry = ctk.CTkEntry(content_frame, placeholder_text="Product Name")
    name_entry.pack(pady=5)

    cargo_fee_entry = ctk.CTkEntry(content_frame, placeholder_text="Cargo Fee")
    cargo_fee_entry.pack(pady=5)

    original_price_entry = ctk.CTkEntry(content_frame, placeholder_text="Original Price")
    original_price_entry.pack(pady=5)

    selling_price_entry = ctk.CTkEntry(content_frame, placeholder_text="Selling Price")
    selling_price_entry.pack(pady=5)

    quantity_entry = ctk.CTkEntry(content_frame, placeholder_text="Quantity")
    quantity_entry.pack(pady=5)

    # Image upload section
    ctk.CTkLabel(content_frame, text="Product Image:").pack(pady=5)
    image_path_entry = ctk.CTkEntry(content_frame, placeholder_text="Image Path", state="readonly", width=400)
    image_path_entry.pack(pady=5)
    ctk.CTkButton(content_frame, text="Upload Image", command=upload_image).pack(pady=10)

    ctk.CTkButton(content_frame, text="Save Product", command=save_product).pack(pady=20)

def display_calculation():
    cursor.execute("SELECT * FROM products WHERE sold_quantity > 0")
    products = cursor.fetchall()

    total_income = 0
    total_expense = 0
    total_profit = 0

    for product in products:
        income = product[7] * product[5]
        expense = product[7] * (product[4] + product[3])
        original_quantity = product[6] + product[7]
        total_expense_product = original_quantity * (product[4] + product[3])

        total_income += income
        total_expense += total_expense_product

        frame = ctk.CTkFrame(content_frame, height=100)
        frame.pack(pady=5, fill="x")
        display_product_image(product[2], frame)
        ctk.CTkLabel(frame, text=f"Name: {product[1]} | Sold: {product[7]} | Income: ₮{income:.2f} | Expense: ₮{expense:.2f} | Profit: ₮{income - expense:.2f} | Total Expense (Original Qty): ₮{total_expense_product:.2f}", font=("Arial", 12)).pack()

    # Calculate total profit AFTER the loop
    total_profit = total_income - total_expense

    # Displaying total values
    total_frame = ctk.CTkFrame(content_frame, height=50)
    total_frame.pack(pady=10, fill="x")
    ctk.CTkLabel(total_frame, text=f"Total Income: ₮{total_income:.2f} | Total Expense: ₮{total_expense:.2f} | Total Profit: ₮{total_profit:.2f}", font=("Arial", 14, "bold")).pack()

def delete_product(product_id):
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    switch_tab("Inventory")

switch_tab("All Products")

# Run the application
app.mainloop()

# Close the database
conn.close()
