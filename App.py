from flask import Flask, request, jsonify, redirect, url_for
import mysql.connector
from flask import render_template
from dotenv import load_dotenv
import os
from datetime import date, datetime
import threading
import time
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

@app.route('/', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        name = request.form.get('name')
        postcode = request.form.get('postcode')
        birthday = request.form.get('birthday')
        address = request.form.get('address')

        # check exsiting customer
        existing_customer = query("""
            SELECT customer_id FROM Customer
            WHERE name=%s AND postcode=%s AND birth_date=%s AND address=%s
        """, (name, postcode, birthday, address), one=True)
        if existing_customer:
            customer_id = existing_customer[0]
            return redirect(url_for('render_menu_page', customer_id=customer_id))
        
        # Save to database and get new customer_id
        customer_id = query("""
            INSERT INTO Customer (name, postcode, birth_date, address)
            VALUES (%s, %s, %s, %s)
        """, (name, postcode, birthday, address), commit=True)

        # Redirect to menu page after successful form submission
        return redirect(url_for('render_menu_page', customer_id=customer_id))

    # If GET request, show the customer login page
    return render_template('customer_login.html')


@app.route("/menu")
def render_menu_page():
    customer_id = request.args.get('customer_id', None)
    return render_template('menu.html', customer_id=customer_id)

@app.route("/menu/get_menu")
def get_menu():
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

     # Keep the data you had in jsonify — just pass it to the template
    return jsonify({
        "pizzas": [{"name": n, "price": float(p)} for (n, p) in pizzas],
        "drinks": [{"name": n, "price": float(p)} for (n, p) in drinks],
        "desserts": [{"name": n, "price": float(p)} for (n, p) in desserts]
    })
        
def calculate_order(customer_id, items, discount_percent=0):
    total = 0
    discount_amount = 0
    order_items = []

    for item in items:
        quantity = item.get("quantity", 1)
        name = item["name"]
        item_type = item["type"]

        if item_type == "pizza":
            row = query("""
                SELECT SUM(pi.price * pi.quantity) AS price
                FROM Ingredient AS pi
                JOIN Pizza AS p ON p.product_id = pi.product_id
                JOIN Product AS pr ON p.product_id = pr.product_id
                WHERE pr.name = %s
            """, (name,), one=True)
            price = float(row[0]) * quantity

        elif item_type == "drink":
            row = query("""
                SELECT pr.price FROM Product AS pr
                JOIN Drink AS d ON pr.product_id = d.product_id
                WHERE pr.name = %s
            """, (name,), one=True)
            price = float(row[0]) * quantity

        elif item_type == "dessert":
            row = query("""
                SELECT pr.price FROM Product AS pr
                JOIN Dessert AS de ON pr.product_id = de.product_id
                WHERE pr.name = %s
            """, (name,), one=True)
            price = float(row[0]) * quantity
        else:
            continue

        order_items.append({
            "type": item_type,
            "name": name,
            "quantity": quantity,
            "price": price
        })
        total += price

    # Birthday discount
    customer = query("SELECT birth_date FROM Customer WHERE customer_id=%s", (customer_id,), one=True)
    birth_date = customer[0]
    today = date.today()

    birthday_discount = 0
    if birth_date.month == today.month and birth_date.day == today.day:
        pizzas = [it for it in order_items if it["type"] == "pizza"]
        drinks = [it for it in order_items if it["type"] == "drink"]
        if pizzas:
            birthday_discount += min(p["price"] for p in pizzas)
        if drinks:
            birthday_discount += min(d["price"] for d in drinks)

    # Percentage discount (from discount code)
    discount_amount = total * (discount_percent / 100.0)

    # 10 pizzas offer
    total_pizzas = sum(it["quantity"] for it in order_items if it["type"] == "pizza")
    if total_pizzas >= 10:
        discount_amount += total * 0.10

    final_total = max(total - discount_amount - birthday_discount, 0)

    return {
        "items": order_items,
        "total": round(total, 2),
        "discount": round(discount_amount + birthday_discount, 2),
        "final_total": round(final_total, 2)
    }


@app.route("/order/summary", methods=["POST"])
def order_summary():
    data = request.json
    print("Received summary request:", data)  # log incoming payload
    summary = calculate_order(data["customer_id"], data["items"])
    print("Calculated summary:", summary)     # log result
    
    return jsonify(summary)

@app.route("/order/confirm", methods=["POST"])
def order_confirm():
    data = request.json
    customer_id = data["customer_id"]
    items = data["items"]

    # Recalculate order to validate totals
    summary = calculate_order(customer_id, items)
    customer = query("SELECT postcode FROM Customer WHERE customer_id = %s", (customer_id,), one=True)
    if not customer:
        return jsonify({"error": "Customer not found"}), 400

    customer_postcode = customer[0]

     # Find available delivery person for same postcode
    delivery_person = query("""
        SELECT delivery_person_id FROM DeliveryPerson
        WHERE is_available = TRUE AND postcode = %s
        ORDER BY delivery_person_id ASC
        LIMIT 1
    """, (customer_postcode,), one=True)
    
    if delivery_person:
        delivery_person_id = delivery_person[0]
        assigned = True
        query("UPDATE DeliveryPerson SET is_available = FALSE WHERE delivery_person_id = %s",
              (delivery_person_id,), commit=True)
        threading.Thread(target=mark_available_after_30min, args=(delivery_person_id,)).start()
    else:
        delivery_person_id = None
        assigned = False

    order_id = query(
        "INSERT INTO Orders (customer_id, delivery_person_id, total_amount, total_price) VALUES (%s, %s, %s, %s)",
        (customer_id, delivery_person_id, sum(it["quantity"] for it in summary["items"]), summary["final_total"]),
        commit=True
    )

    for it in summary["items"]:
        product_id = query("SELECT product_id FROM Product WHERE name=%s LIMIT 1", (it["name"],), one=True)[0]
        query(
            "INSERT INTO OrderItem (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
            (order_id, product_id, it["quantity"], it["price"]),
            commit=True
        )
        
    if assigned:
        status_msg = f"Assigned to delivery person ID {delivery_person_id}"
    else:
        status_msg = f"No available delivery person in postcode {customer_postcode}. Order pending."


    return jsonify({"customer_id": customer_id,"order_id": order_id, "final_total": summary["final_total"], "delivery_status": status_msg})
    

def mark_available_after_30min(delivery_person_id):
    """Background thread to reset delivery person availability after 30 minutes."""
    print(f"⏳ Delivery person {delivery_person_id} will become available in 30 minutes...")
    time.sleep(1800)  # 30 minutes = 1800 seconds
    query("UPDATE DeliveryPerson SET is_available = TRUE WHERE delivery_person_id = %s",
        (delivery_person_id,), commit=True)
    print(f"✅ Delivery person {delivery_person_id} is now available again.")
    
# def assign_oldest_unassigned(delivery_person_id):
#     """If any undelivered orders exist for this postcode, assign the oldest one."""
#     # Get delivery person postcode
#     person = query("SELECT postcode FROM DeliveryPerson WHERE delivery_person_id = %s", (delivery_person_id,), one=True)
#     if not person:
#         return
#     dp_postcode = person[0]

#     order = query("""
#         SELECT o.order_id
#         FROM Orders o
#         JOIN Customer c ON o.customer_id = c.customer_id
#         WHERE o.delivery_person_id IS NULL AND c.postcode = %s
#         ORDER BY o.order_time ASC
#         LIMIT 1
#     """, (dp_postcode,), one=True)
    
#     if order:
#         order_id = order[0]
#         print(f"🚚 Reassigning available delivery person {delivery_person_id} to pending order {order_id}")
#         query("""
#             UPDATE Orders
#             SET delivery_person_id = %s
#             WHERE order_id = %s
#         """, (delivery_person_id, order_id), commit=True)
#         query("UPDATE DeliveryPerson SET is_available = FALSE WHERE delivery_person_id = %s",
#               (delivery_person_id,), commit=True)
#         threading.Thread(target=mark_available_after_30min, args=(delivery_person_id,)).start()


if __name__ == "__main__":
    app.run(debug=True)
    
