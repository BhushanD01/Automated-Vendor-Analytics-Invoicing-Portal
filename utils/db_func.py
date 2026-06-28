import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def connect_to_database():

    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"))


def get_basic_info(cursor):

    queries = {
        "Total Suppliers": "SELECT COUNT(*) AS count FROM suppliers",

        "Total Products": "SELECT COUNT(*) AS count FROM products",

        "Total Categories Dealing": "SELECT COUNT(DISTINCT category) AS count FROM products",

        "Total Sale Value (Last Month)": """
        SELECT ROUND(SUM(ABS(se.change_quantity) * p.price), 2) AS total_sale
        FROM stock_entries se
        JOIN products p ON se.product_id = p.product_id
        WHERE se.change_type = 'Sale'
        AND se.entry_date >= (
        SELECT DATE_SUB(MAX(entry_date), INTERVAL 1 MONTH) FROM stock_entries)
        """,

        "Total Restock Value (Last 3 Months)": """
        SELECT ROUND(SUM(se.change_quantity * p.price), 2) AS total_restock
        FROM stock_entries se
        JOIN products p ON se.product_id = p.product_id
        WHERE se.change_type = 'Restock'
        AND se.entry_date >= (
        SELECT DATE_SUB(MAX(entry_date), INTERVAL 3 MONTH) FROM stock_entries)
        """,

        "Below Reorder & No Pending Reorders": """
        SELECT COUNT(*) AS below_reorder
        FROM products p
        WHERE p.stock_quantity < p.reorder_level
        AND p.product_id NOT IN (
        SELECT DISTINCT product_id FROM reorders WHERE status = 'Pending')
        """
    }

    result = {}
    for label, query in queries.items():
        cursor.execute(query)
        row = cursor.fetchone()
        result[label] = list(row.values())[0]

    return result


def get_info_tables(cursor):

    queries = {

        "Suppliers Contact Details": "SELECT supplier_name, contact_name, email, phone FROM suppliers",

        "Product Details with Supplier and Stock": """
            SELECT 
                p.product_name,
                s.supplier_name,
                p.stock_quantity,
                p.reorder_level
            FROM products p
            JOIN suppliers s ON p.supplier_id = s.supplier_id
            ORDER BY p.product_name ASC
        """,

        "Products Needing Restock": """
            SELECT 
                product_id, 
                product_name, 
                stock_quantity, 
                reorder_level 
            FROM products;
        """
    }

    tables = {}
    for label, query in queries.items():
    
        cursor.execute(query)
        tables[label] = cursor.fetchall()

    return tables
        

def add_product(cursor, db, p_name, p_category, p_price, p_stock, p_reorder, p_supplier):
    
    procedure_call = "CALL AddNewProduct(%s, %s, %s, %s, %s, %s)"
    params = (p_name, p_category, p_price, p_stock, p_reorder, p_supplier)
    cursor.execute(procedure_call, params)
    db.commit()


def get_categories(cursor):

    cursor.execute("SELECT DISTINCT category from products ORDER BY category ASC")
    rows = cursor.fetchall()
    return [row["category"] for row in rows]


def get_suppliers(cursor):

    cursor.execute("SELECT supplier_id, supplier_name from suppliers ORDER BY supplier_name ASC")
    return cursor.fetchall() 


def get_all_products(cursor):

    cursor.execute("SELECT product_id, product_name from products ORDER BY product_name ASC")
    return cursor.fetchall() 


def get_product_history(cursor, product_id):

    query = "SELECT * FROM product_history WHERE product_id = (%s) ORDER BY record_date DESC"
    cursor.execute(query, (product_id,))
    return cursor.fetchall()


def place_reorder(cursor, db, product_id , reorder_quantity):
    query= """
         insert into reorders (reorder_id,product_id ,reorder_quantity,reorder_date ,status)
         SELECT max(reorder_id)+1,%s, %s, curdate(), "Ordered" FROM reorders;"""

    cursor.execute(query,(product_id, reorder_quantity))
    db.commit()


def get_pending_reorders(cursor):

    query = """
        SELECT
            r.reorder_id,
            p.product_name
        FROM reorders r
        JOIN products p 
        ON r.product_id = p.product_id
        WHERE r.status = 'Ordered'
        ORDER BY r.reorder_date DESC;
    """

    cursor.execute(query)
    return cursor.fetchall() 


def mark_reorder_as_received(cursor, db, reorder_id):
    cursor.callproc("MarkReorderasReceived",[reorder_id])
    db.commit()