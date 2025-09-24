from flask import Flask, request, jsonify
import mysql.connector
from dotenv import load_dotenv
import os
from datetime import date
load_dotenv()
db_user = os.getenv("password")
app = Flask(__name__)
conn = mysql.connector.connect(
    host="localhost",       # or your MySQL server IP
    user="root",            # your MySQL username
    password=db_user,# your MySQL password
    database="pizza_ordering"       # database name
)
db = conn.cursor()

# --- DB helper ---
def query(sql, params=None, one=False, commit=False):
    cur = conn.cursor(buffered=True, dictionary=False)
    cur.execute(sql, params or ())
    result = None
    if commit:
        conn.commit()
        result = cur.lastrowid  # return inserted id if needed
    else:
        result = cur.fetchone() if one else cur.fetchall()
    cur.close()
    return result

# @app.route("/menu", methods=["GET"])
# def menu():
#     pizzas = db.execute("""
#         SELECT 
#             p.name,
#             SUM(pi.price * pi.quantity) AS total_price
#         FROM Pizza p
#         JOIN Ingredient pi ON p.pizza_id = pi.pizza_id
#         GROUP BY p.name
#     """)
#     drinks = db.execute("SELECT dr.name, price FROM Drink dr") # add drinks and desserts table
#     desserts = db.execute("SELECT de.name, price FROM Dessert de")
#     return jsonify(
#         { "pizzas": [ {"name": n, "price": float(p), "label": ("vegan" if v else ("vegetarian" if veg else "non-vegetarian"))} for n, p, v, veg in pizzas], 
#                     "drinks": [{"name": n, "price": float(p)} for n, p in drinks], 
#                     "desserts": [{"name": n, "price": float(p)} for n, p in desserts] } )

@app.route("/menu", methods=["GET"])
def menu():
    pizzas = query("""
        SELECT 
            p.name,
            SUM(pi.price * pi.quantity) AS total_price
        FROM Pizza p
        JOIN Ingredient pi ON p.pizza_id = pi.pizza_id
        GROUP BY p.name
    """)

    drinks = query("SELECT name, price FROM Drink")
    desserts = query("SELECT name, price FROM Dessert")

    return jsonify({
        "pizzas": [{"name": n, "price": float(p)} for (n, p) in pizzas],
        "drinks": [{"name": n, "price": float(p)} for (n, p) in drinks],
        "desserts": [{"name": n, "price": float(p)} for (n, p) in desserts]
    })
                    
@app.route("/order", methods=["POST"])
def order():
    data = request.json
    customer_id = data["customer_id"]
    items = data["items"]

    total = 0
    order_items = []

    for item in items: 
        quantity = item.get("quantity", 1)

        if item["type"] == "pizza":
            row = db.db.execute("""
                SELECT SUM(pi.price * pi.quantity) AS price
                FROM Pizza p
                JOIN Ingredient pi ON p.pizza_id = pi.pizza_id
                WHERE p.pizza_id = %s
                GROUP BY p.pizza_id
            """, (item["id"],), one=True)
            price = row[0] * quantity
            name = db.db.execute("SELECT name FROM Pizza WHERE pizza_id=%s", (item["id"],), one=True)[0]

        elif item["type"] == "drink":
            row = db.db.execute("SELECT name, price FROM Drink WHERE drink_id=%s", (item["id"],), one=True)
            name, price = row
            price *= quantity

        elif item["type"] == "dessert":
            row = db.db.execute("SELECT name, price FROM Dessert WHERE dessert_id=%s", (item["id"],), one=True)
            name, price = row
            price *= quantity

        else:
            continue 

        total += price
        order_items.append((item["type"], name, quantity, price))


    
    customer = db.execute("SELECT birth_date FROM Customer WHERE customer_id=%s", (customer_id,), one=True)
    birth_date = customer[0]

    today = date.today()


    if birth_date.month == today.month and birth_date.day == today.day:
    # find cheapest pizza
        pizzas = [item for item in order_items if item[0] == 'pizza']
    if pizzas:
        cheapest_pizza_price = min([item[2] for item in pizzas])
        discount += cheapest_pizza_price
    # find cheapest drink
    drinks = [item for item in order_items if item[0] == 'drink']
    if drinks:
        cheapest_drink_price = min([item[2] for item in drinks])
        discount += cheapest_drink_price


    total_pizzas = db.db.execute("""
    SELECT SUM(quantity)
    FROM OrderItem oi
    JOIN Orders o ON oi.order_id = o.order_id
    WHERE o.customer_id=%s AND oi.type='pizza';
""", (customer_id,), one=True)[0] or 0
    
    if total_pizzas >= 10:
        discount += 0.10 * total

    final_total = max(total - discount, 0)

    delivery = db.execute("SELECT delivery_person_id FROM DeliveryPerson WHERE is_available = TRUE LIMIT 1", one=True)
    delivery_person_id = delivery[0] if delivery else None

    order_id = db.execute(
        "INSERT INTO Orders (customer_id, delivery_person_id, total_amount, total_price) VALUES (%s, %s, %s, %s)",
        (customer_id, delivery_person_id, total, final_total),
        commit=True
    )

    for pizza_id, quantity, price in order_items:
        db.execute(
            "INSERT INTO OrderItem (order_id, pizza_id, type, quantity, price) VALUES (%s, %s, %s, %s, %s)",
            (order_id, pizza_id, "pizza", quantity, price),
            commit=True
        )

    return jsonify({"order_id": order_id, "total": final_total, "discount": discount})
