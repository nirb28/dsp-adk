"""
Setup script for sample SQLite database.

Creates a realistic e-commerce database with customers, orders, and products.
"""
import sqlite3
import os
from datetime import datetime, timedelta
import random


def create_sample_database(db_path: str = './data/databases/sample.db'):
    """Create and populate sample database."""
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Creating database: {db_path}")
    
    # Create tables
    cursor.execute("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            country TEXT NOT NULL,
            signup_date DATE NOT NULL,
            total_spent REAL DEFAULT 0
        )
    """)
    
    cursor.execute("""
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL,
            supplier TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            order_date DATE NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            product_category TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)
    
    print("Tables created successfully")
    
    # Sample data
    countries = ['USA', 'UK', 'Canada', 'Germany', 'France', 'Australia', 'Japan', 'Brazil']
    categories = ['electronics', 'clothing', 'books', 'home', 'sports', 'toys']
    statuses = ['completed', 'pending', 'cancelled']
    
    # Insert customers
    customers_data = [
        ('John Smith', 'john.smith@email.com', 'USA'),
        ('Emma Johnson', 'emma.j@email.com', 'UK'),
        ('Michael Brown', 'mbrown@email.com', 'Canada'),
        ('Sophia Davis', 'sophia.d@email.com', 'Germany'),
        ('James Wilson', 'jwilson@email.com', 'USA'),
        ('Olivia Martinez', 'olivia.m@email.com', 'France'),
        ('William Anderson', 'wanderson@email.com', 'Australia'),
        ('Ava Taylor', 'ava.t@email.com', 'UK'),
        ('Robert Thomas', 'rthomas@email.com', 'Canada'),
        ('Isabella Garcia', 'isabella.g@email.com', 'USA'),
        ('David Rodriguez', 'drodriguez@email.com', 'Brazil'),
        ('Mia Hernandez', 'mia.h@email.com', 'USA'),
        ('Joseph Lopez', 'jlopez@email.com', 'Germany'),
        ('Charlotte Gonzalez', 'charlotte.g@email.com', 'France'),
        ('Daniel Perez', 'dperez@email.com', 'Japan'),
        ('Amelia Sanchez', 'amelia.s@email.com', 'Australia'),
        ('Matthew Ramirez', 'mramirez@email.com', 'UK'),
        ('Harper Torres', 'harper.t@email.com', 'Canada'),
        ('Christopher Rivera', 'crivera@email.com', 'USA'),
        ('Evelyn Flores', 'evelyn.f@email.com', 'Germany'),
    ]
    
    for i, (name, email, country) in enumerate(customers_data, 1):
        signup_date = datetime.now() - timedelta(days=random.randint(30, 365))
        cursor.execute(
            "INSERT INTO customers (name, email, country, signup_date, total_spent) VALUES (?, ?, ?, ?, ?)",
            (name, email, country, signup_date.strftime('%Y-%m-%d'), 0)
        )
    
    print(f"Inserted {len(customers_data)} customers")
    
    # Insert products
    products_data = [
        ('Laptop Pro 15', 'electronics', 1299.99, 15, 'TechCorp'),
        ('Wireless Mouse', 'electronics', 29.99, 50, 'TechCorp'),
        ('USB-C Cable', 'electronics', 12.99, 100, 'CableWorld'),
        ('Bluetooth Headphones', 'electronics', 89.99, 30, 'AudioMax'),
        ('4K Monitor', 'electronics', 399.99, 20, 'DisplayTech'),
        ('Cotton T-Shirt', 'clothing', 19.99, 200, 'FashionCo'),
        ('Denim Jeans', 'clothing', 49.99, 80, 'FashionCo'),
        ('Running Shoes', 'clothing', 79.99, 60, 'SportWear'),
        ('Winter Jacket', 'clothing', 129.99, 40, 'FashionCo'),
        ('Python Programming', 'books', 39.99, 50, 'BookWorld'),
        ('Data Science Handbook', 'books', 44.99, 35, 'BookWorld'),
        ('Fiction Novel', 'books', 14.99, 100, 'BookWorld'),
        ('Coffee Maker', 'home', 79.99, 25, 'HomeGoods'),
        ('Blender', 'home', 59.99, 30, 'HomeGoods'),
        ('Vacuum Cleaner', 'home', 199.99, 15, 'HomeGoods'),
        ('Yoga Mat', 'sports', 24.99, 70, 'FitGear'),
        ('Dumbbells Set', 'sports', 89.99, 40, 'FitGear'),
        ('Tennis Racket', 'sports', 119.99, 25, 'SportPro'),
        ('LEGO Set', 'toys', 49.99, 60, 'ToyMart'),
        ('Board Game', 'toys', 29.99, 80, 'ToyMart'),
    ]
    
    for name, category, price, stock, supplier in products_data:
        cursor.execute(
            "INSERT INTO products (name, category, price, stock, supplier) VALUES (?, ?, ?, ?, ?)",
            (name, category, price, stock, supplier)
        )
    
    print(f"Inserted {len(products_data)} products")
    
    # Insert orders
    order_count = 0
    for customer_id in range(1, 21):
        # Each customer has 0-10 orders
        num_orders = random.randint(0, 10)
        customer_total = 0
        
        for _ in range(num_orders):
            order_date = datetime.now() - timedelta(days=random.randint(1, 180))
            amount = round(random.uniform(15.0, 500.0), 2)
            status = random.choices(statuses, weights=[0.7, 0.2, 0.1])[0]
            category = random.choice(categories)
            
            cursor.execute(
                "INSERT INTO orders (customer_id, order_date, amount, status, product_category) VALUES (?, ?, ?, ?, ?)",
                (customer_id, order_date.strftime('%Y-%m-%d'), amount, status, category)
            )
            
            if status == 'completed':
                customer_total += amount
            
            order_count += 1
        
        # Update customer total_spent
        cursor.execute(
            "UPDATE customers SET total_spent = ? WHERE customer_id = ?",
            (round(customer_total, 2), customer_id)
        )
    
    print(f"Inserted {order_count} orders")
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print(f"\nDatabase created successfully at: {db_path}")
    print("\nDatabase Statistics:")
    print(f"  - Customers: {len(customers_data)}")
    print(f"  - Products: {len(products_data)}")
    print(f"  - Orders: {order_count}")
    
    return db_path


def verify_database(db_path: str):
    """Verify database contents."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("DATABASE VERIFICATION")
    print("="*60)
    
    # Check customers
    cursor.execute("SELECT COUNT(*) FROM customers")
    customer_count = cursor.fetchone()[0]
    print(f"\nCustomers: {customer_count}")
    
    cursor.execute("SELECT name, email, country, total_spent FROM customers ORDER BY total_spent DESC LIMIT 5")
    print("\nTop 5 Customers by Spending:")
    for row in cursor.fetchall():
        print(f"  - {row[0]} ({row[2]}): ${row[3]:.2f}")
    
    # Check products
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]
    print(f"\nProducts: {product_count}")
    
    cursor.execute("SELECT category, COUNT(*) FROM products GROUP BY category")
    print("\nProducts by Category:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]} products")
    
    # Check orders
    cursor.execute("SELECT COUNT(*) FROM orders")
    order_count = cursor.fetchone()[0]
    print(f"\nOrders: {order_count}")
    
    cursor.execute("SELECT status, COUNT(*), SUM(amount) FROM orders GROUP BY status")
    print("\nOrders by Status:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]} orders (${row[2]:.2f})")
    
    cursor.execute("SELECT product_category, COUNT(*), SUM(amount) FROM orders WHERE status='completed' GROUP BY product_category ORDER BY SUM(amount) DESC")
    print("\nRevenue by Category (Completed Orders):")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]} orders (${row[2]:.2f})")
    
    conn.close()
    print("\n" + "="*60)


if __name__ == '__main__':
    db_path = create_sample_database()
    verify_database(db_path)
