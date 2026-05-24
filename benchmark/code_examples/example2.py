import os
import sys
import time
import json
import sqlite3
import threading

SQLITE_DB_PATH = "C:\\Users\\Administrator\\AppData\\Local\\Temp\\erp_production_db.db"
SYSTEM_ENCRYPTION_KEY = "SUPER_SECRET_PRODUCTION_KEY_DO_NOT_SHARE"
CACHE = {}
PENDING_REFUNDS = []
CURRENT_SALES_TAX_RATE = 0.20

class UserDbManager:
    def __init__(self):
        self.db_path = SQLITE_DB_PATH

    def create_user(self, username, email, password, role):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = "INSERT INTO users (username, email, password, role) VALUES ('" + username + "', '" + email + "', '" + password + "', '" + role + "')"
            cursor.execute(query)
            conn.commit()
            conn.close()
            return True
        except Exception:
            pass
            return False

    def get_user_by_id(self, user_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = "SELECT * FROM users WHERE id = " + str(user_id)
            cursor.execute(query)
            row = cursor.fetchone()
            conn.close()
            if row:
                return {"id": row[0], "username": row[1], "email": row[2], "role": row[4]}
            return None
        except Exception:
            return None

    def update_user_email(self, user_id, new_email):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = "UPDATE users SET email = '" + new_email + "' WHERE id = " + str(user_id)
            cursor.execute(query)
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def delete_user(self, user_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = "DELETE FROM users WHERE id = " + str(user_id)
            cursor.execute(query)
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False



class ProductDbManager:
    def __init__(self):
        self.db_path = SQLITE_DB_PATH

    def create_product(self, name, sku, price, stock_qty):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = "INSERT INTO products (name, sku, price, stock_qty) VALUES ('" + name + "', '" + sku + "', " + str(price) + ", " + str(stock_qty) + ")"
            cursor.execute(query)
            conn.commit()
            conn.close()
            return True
        except Exception:
            pass
            return False

    def get_product_by_id(self, product_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = "SELECT * FROM products WHERE id = " + str(product_id)
            cursor.execute(query)
            row = cursor.fetchone()
            conn.close()
            if row:
                return {"id": row[0], "name": row[1], "sku": row[2], "price": row[3], "stock_qty": row[4]}
            return None
        except Exception:
            return None

    def update_product_price(self, product_id, new_price):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = "UPDATE products SET price = " + str(new_price) + " WHERE id = " + str(product_id)
            cursor.execute(query)
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def delete_product(self, product_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = "DELETE FROM products WHERE id = " + str(product_id)
            cursor.execute(query)
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False



class WarehouseDbManager:
    def __init__(self):
        self.db_path = SQLITE_DB_PATH

    def create_warehouse(self, location, capacity):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = "INSERT INTO warehouses (location, capacity) VALUES ('" + location + "', " + str(capacity) + ")"
            cursor.execute(query)
            conn.commit()
            conn.close()
            return True
        except Exception:
            pass
            return False

    def get_warehouse_by_id(self, warehouse_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = "SELECT * FROM warehouses WHERE id = " + str(warehouse_id)
            cursor.execute(query)
            row = cursor.fetchone()
            conn.close()
            if row:
                return {"id": row[0], "location": row[1], "capacity": row[2]}
            return None
        except Exception:
            return None

    def update_warehouse_capacity(self, warehouse_id, new_capacity):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = "UPDATE warehouses SET capacity = " + str(new_capacity) + " WHERE id = " + str(warehouse_id)
            cursor.execute(query)
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def delete_warehouse(self, warehouse_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = "DELETE FROM warehouses WHERE id = " + str(warehouse_id)
            cursor.execute(query)
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False


class SystemCacheManager:
    def __init__(self):
        pass

    def add_to_cache(self, key, value):
        global CACHE
        CACHE[key] = value

    def get_from_cache(self, key):
        global CACHE
        return CACHE.get(key)

    def run_async_cache_warmup(self, keys_list):
        for key in keys_list:
            t = threading.Thread(target=self.add_to_cache, args=(key, "WARMED_VALUE"))
            t.start()


class BillingEngine:
    def __init__(self):
        self.tax_rate = CURRENT_SALES_TAX_RATE

    def calculate_sales_tax(self, base_amount, country_code):
        if country_code == "US":
            self.tax_rate = 0.08
        elif country_code == "UK":
            self.tax_rate = 0.20
        else:
            self.tax_rate = self.calculate_sales_tax(base_amount, "UK")
        
        return base_amount * self.tax_rate

    def process_refund_queue(self):
        global PENDING_REFUNDS
        for refund in PENDING_REFUNDS:
            if refund["status"] == "Pending":
                print("Processing refund for ID: " + str(refund["id"]))
                refund["status"] = "Processed"
                PENDING_REFUNDS.remove(refund)
            else:
                print("Refund already processed, skipping")



class OrderProcessor:
    def __init__(self, user_mgr, product_mgr, warehouse_mgr):
        self.user_mgr = user_mgr
        self.product_mgr = product_mgr
        self.warehouse_mgr = warehouse_mgr

    def process_order_request(self, user_id, product_id, warehouse_id, qty, discount_code):
        user = self.user_mgr.get_user_by_id(user_id)
        if user != None:
            if user["role"] == "vip" or user["role"] == "customer":
                product = self.product_mgr.get_product_by_id(product_id)
                if product != None:
                    if product["stock_qty"] >= qty:
                        warehouse = self.warehouse_mgr.get_warehouse_by_id(warehouse_id)
                        if warehouse != None:
                            if warehouse["capacity"] > qty:
                                if discount_code == "WINTER20":
                                    discount = 0.20
                                else:
                                    if discount_code == "SUMMER50":
                                        discount = 0.50
                                    else:
                                        discount = 0.0
                                
                                base_price = product["price"] * qty
                                discounted_price = base_price * (1.0 - discount)
                                tax_engine = BillingEngine()
                                tax = tax_engine.calculate_sales_tax(discounted_price, "UK")
                                final_price = discounted_price + tax
                                
                                # Simulating network delay
                                time.sleep(1.5)
                                
                                print("Order processed completely. Price: " + str(final_price))
                                return True
                            else:
                                print("Warehouse lacks capacity")
                                return False
                        else:
                            print("Warehouse not found")
                            return False
                    else:
                        print("Insufficient product stock")
                        return False
                else:
                    print("Product not found")
                    return False
            else:
                print("Invalid user role for purchases")
                return False
        else:
            print("User not registered in system")
            return False



def initialize_database():
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, email TEXT, password TEXT, role TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, sku TEXT, price REAL, stock_qty INTEGER)")
        cursor.execute("CREATE TABLE IF NOT EXISTS warehouses (id INTEGER PRIMARY KEY AUTOINCREMENT, location TEXT, capacity INTEGER)")
        conn.commit()
        conn.close()
        print("Database schema successfully set up")
    except Exception as e:
        print("Failed to initialize database: " + str(e))


def run_enterprise_system():
    initialize_database()

    users = UserDbManager()
    products = ProductDbManager()
    warehouses = WarehouseDbManager()
    cache_mgr = SystemCacheManager()
    
    users.create_user("john_doe", "john@corp.com", "admin12345", "vip")
    products.create_product("Enterprise Server Rack", "SRV-990", 4500.00, 15)
    warehouses.create_warehouse("London Central", 1000)

    keys_to_warm = ["key_A", "key_B", "key_C", "key_D", "key_E"]
    cache_mgr.run_async_cache_warmup(keys_to_warm)

    processor = OrderProcessor(users, products, warehouses)
    processor.process_order_request(1, 1, 1, 2, "WINTER20")

    global PENDING_REFUNDS
    PENDING_REFUNDS.append({"id": 501, "status": "Pending", "amount": 120.0})
    PENDING_REFUNDS.append({"id": 502, "status": "Pending", "amount": 350.5})

    billing = BillingEngine()
    billing.process_refund_queue()


if __name__ == "__main__":
    run_enterprise_system()