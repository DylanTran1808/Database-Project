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

        # Save to database
        query("""
            INSERT INTO Customer (name, postcode, birth_date, address)
            VALUES (%s, %s, %s, %s)
        """, (name, postcode, birthday, address), commit=True)

        # Redirect to menu page after successful form submission
        return redirect(url_for('render_menu_page'))

    # If GET request, show the customer login page
    return render_template('customer_login.html')


@app.route("/menu")
def render_menu_page():
    return render_template('menu.html')

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
        
#@app.route("/order", methods=["POST"])
def calculate_order(customer_id, items):
    #data = request.json
    #customer_id = data["customer_id"]
    #items = data["items"]
    amount =0
    total = 0
    discount = 0
    order_items = []

    for item in items: 
        quantity = item.get("quantity", 1)
       
        if item["type"] == "pizza":
            row = query("""
                SELECT SUM(pi.price * pi.quantity) AS price
                FROM Ingredient AS pi
                JOIN Pizza AS p ON p.product_id = pi.product_id
                JOIN Product AS pr ON p.product_id = pr.product_id
                WHERE pr.name = %s
            """, (item["name"],), one=True)
            price = row[0] * item.get("quantity", 1)
            name = item["name"]

        elif item["type"] == "drink":
            row = query("""
                SELECT pr.price FROM Product AS pr
                JOIN Drink AS d ON pr.product_id = d.product_id
                WHERE pr.name = %s
            """, (item["name"],), one=True)
            price = row[0] * item.get("quantity", 1)
            name = item["name"]
            amount += quantity

        elif item["type"] == "dessert":
            row = query("""
                SELECT pr.price FROM Product AS pr
                JOIN Dessert AS d ON pr.product_id = d.product_id
                WHERE pr.name = %s
            """, (item["name"],), one=True)
            price = row[0] * item.get("quantity", 1)
            name = item["name"]
            amount += quantity

        else:
            continue 

        total += price
        order_items.append({
            "type": item["type"],
            "name": name,
            "quantity": quantity,
            "price": float(price)  # convert Decimal to float for JSON
        })



    
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
    SELECT SUM(oi.quantity)
    FROM Orders AS o
    JOIN Customer AS c ON c.customer_id = o.customer_id
    JOIN OrderItem AS oi ON oi.order_id = o.order_id
    JOIN Product AS pr ON oi.product_id = pr.product_id
    WHERE o.customer_id=%s AND pr.is_pizza = 1;
""", (customer_id,), one=True)[0] or 0
    
    if total_pizzas >= 10:
        discount += 0.10 * float(total)

    final_total = max(float(total) - discount, 0)
    return {
        "items": order_items,
        "total": float(total),
        "discount": float(discount),
        "final_total": float(final_total),
        "amount": amount
    }


    #delivery = query("SELECT delivery_person_id FROM DeliveryPerson WHERE is_available = TRUE LIMIT 1", one=True)
    #delivery_person_id = delivery[0] if delivery else None
'''
    order_id = query(
        "INSERT INTO Orders (customer_id, delivery_person_id, total_amount, total_price) VALUES (%s, %s, %s, %s)",
        (customer_id, delivery_person_id, amount, final_total),
        commit=True
    )

    for product_id, quantity, price in order_items:
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
'''

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
    delivery_person_id = data.get("delivery_person_id")

    # Recalculate order to validate totals
    summary = calculate_order(customer_id, items)
    customer = query("SELECT postcode FROM Customer WHERE customer_id = %s", (customer_id,), one=True)
    # if not customer:
    #     return jsonify({"error": "Customer not found"}), 400

    # customer_postcode = customer[0]

    # # Find available delivery person for same postcode
    # delivery_person = query("""
    #     SELECT delivery_person_id FROM DeliveryPerson
    #     WHERE is_available = TRUE AND postcode = %s
    #     ORDER BY delivery_person_id ASC
    #     LIMIT 1
    # """, (customer_postcode,), one=True)

    # if delivery_person:
    #     delivery_person_id = delivery_person[0]
    #     assigned = True
    #     query("UPDATE DeliveryPerson SET is_available = FALSE WHERE delivery_person_id = %s",
    #           (delivery_person_id,), commit=True)
    #     threading.Thread(target=mark_available_after_30min, args=(delivery_person_id,)).start()
    # else:
    #     delivery_person_id = None
    #     assigned = False

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
    # if assigned:
    #     status_msg = f"Assigned to delivery person ID {delivery_person_id}"
    # else:
    #     status_msg = f"No available delivery person in postcode {customer_postcode}. Order pending."

    return jsonify({"order_id": order_id, "final_total": summary["final_total"], "delivery_status": status_msg})

# def mark_available_after_30min(delivery_person_id):
#     """Background thread to reset delivery person availability after 30 minutes."""
#     print(f"⏳ Delivery person {delivery_person_id} will become available in 30 minutes...")
#     time.sleep(1800)  # 30 minutes = 1800 seconds
#     query("UPDATE DeliveryPerson SET is_available = TRUE WHERE delivery_person_id = %s",
#         (delivery_person_id,), commit=True)
#     print(f"✅ Delivery person {delivery_person_id} is now available again.")
    
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
    
