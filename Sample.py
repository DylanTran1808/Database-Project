from dotenv import load_dotenv
import os
import mysql.connector
from faker import Faker
import random
load_dotenv()  # looks for .env file in the current directory

# Access variables
db_user = os.getenv("password")

conn = mysql.connector.connect(
    host="localhost",       # or your MySQL server IP
    user="root",            # your MySQL username
    password=db_user,# your MySQL password
    database="pizza_ordering"       # database name
)
fake = Faker()
def generate_customer():
    return {
        "customer_id": random.randint(1000, 9999),  # random 4-digit ID
        "name": fake.name(),
        "postcode": fake.postcode(),
        "birth_date": fake.date_of_birth(minimum_age=18, maximum_age=90).strftime("%Y-%m-%d"),
        "address": fake.address().replace("\n", ", ")  # clean multi-line
    }

customers = [generate_customer() for _ in range(2)]

cursor = conn.cursor()

for i in range(2):
    cursor.execute(f"INSERT INTO Customer (name, postcode, birth_date, address) VALUES ('{customers[i]['name']}', '{customers[i]['postcode']}', '{customers[i]['birth_date']}', '{customers[i]['address']}')")

conn.commit()

cursor.execute("SELECT * FROM Customer")
rows = cursor.fetchall()
for row in rows:
    print(row)
    
cursor.close()
conn.close()