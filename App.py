from flask import Flask, request, jsonify
import mysql.connector
from flask import render_template
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

@app.route('/')
def home():
    return render_template('menu.html')

@app.route("/menu", methods=["GET"])
def menu():
    pizzas = query("""
        SELECT 
            pr.name,
            SUM(pi.price * pi.quantity) AS total_price
        FROM Product AS pr
        JOIN Pizza AS p ON p.product_id = pr.product_id
        JOIN Ingredient AS pi ON p.product_id = pi.product_id
        GROUP BY pr.name
    """)

    drinks = query("SELECT pr.name, pr.price FROM Drink AS d JOIN Product AS pr ON pr.product_id = d.product_id")
    desserts = query("SELECT pr.name, pr.price FROM Dessert AS de JOIN Product AS pr ON pr.product_id=de.product_id")

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
    amount =0
    total = 0
    discount = 0
    order_items = []

    for item in items: 
        quantity = item.get("quantity", 1)
       
        if item["type"] == "pizza": #UPDATD COLUMN
            row = query("""
                SELECT SUM(pi.price * pi.quantity) AS price
                FROM Ingredient AS pi
                JOIN Pizza AS p ON p.product_id = pi.product_id
                JOIN Product AS pr ON p.product_id = pr.product_id
                WHERE pr.product_id = %s
                GROUP BY pr.product_id
            """, (item["id"],), one=True)
            price = row[0] * quantity
            amount += quantity
            name = query("SELECT pr.name FROM Product AS pr JOIN Pizza AS p ON p.product_id = pr.product_id WHERE pr.product_id=%s", (item["id"],), one=True)[0]

        elif item["type"] == "drink":
            row = query("SELECT pr.name, pr.price FROM Product AS pr JOIN Drink AS d ON pr.product_id = d.product_id WHERE pr.product_id=%s", (item["id"],), one=True)
            name, price = row
            price *= quantity
            amount += quantity

        elif item["type"] == "dessert":
            row = query("SELECT pr.name, pr.price FROM Product AS pr JOIN Dessert AS d ON pr.product_id = d.product_id WHERE pr.product_id=%s", (item["id"],), one=True)
            name, price = row
            price *= quantity
            amount += quantity

        else:
            continue 

        total += price
        order_items.append((item["type"], name, quantity, price))


    
    customer = query("SELECT birth_date FROM Customer WHERE customer_id=%s", (customer_id,), one=True)
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


    total_pizzas = query("""
    SELECT SUM(quantity)
    FROM OrderItem AS oi
    JOIN Orders AS o ON oi.order_id = o.order_id
    JOIN Product AS pr ON oi.product_id = pr.product_id
    WHERE o.customer_id=%s AND pr.is_pizza = 1;
""", (customer_id,), one=True)[0] or 0
    
    if total_pizzas >= 10:
        discount += 0.10 * total

    final_total = max(total - discount, 0)

    delivery = query("SELECT delivery_person_id FROM DeliveryPerson WHERE is_available = TRUE LIMIT 1", one=True)
    delivery_person_id = delivery[0] if delivery else None

    order_id = query(
        "INSERT INTO Orders (customer_id, delivery_person_id, total_amount, total_price) VALUES (%s, %s, %s, %s)",
        (customer_id, delivery_person_id, total, final_total),
        commit=True
    )

    for type, name, quantity, price in order_items:
        query(
            f"INSERT INTO Orders (customer_id, delivery_person_id,discount_id, total_amount, total_price) VALUES ({data['customer_id']},{data['delivery_person_id']},{amount}, {total})"
        )
        query(
            """
            INSERT INTO OrderItem (order_id, product_id, quantity, price) 
            VALUES (
                %s, 
                (SELECT pr.product_id FROM Product AS pr WHERE pr.name=%s LIMIT 1), 
                %s, 
                %s
            )
            """,
            (order_id, name, quantity, price),
            commit=True
        )

    return jsonify({"order_id": order_id, "total": final_total, "discount": discount})

if __name__ == "__main__":
    app.run(debug=True)
    
print(app.url_map)