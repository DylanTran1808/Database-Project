import pandas as pd
import mysql.connector
from dotenv import load_dotenv
import os
from faker import Faker
import random
load_dotenv()

menu = pd.read_csv('data/menu.csv')
ingredients = pd.read_csv('data/ingredient.csv')

db_user = os.getenv('password')
conn = mysql.connector.connect(
    host="localhost",       # or your MySQL server IP
    user="root",            # your MySQL username
    password=db_user,# your MySQL password
    database="pizza_ordering"       # database name
)

cursor = conn.cursor()

ingredient_lookup = {
    row.name: {'type': row.type, 'price': row.price} 
    for row in ingredients.itertuples()
}
# Load products' data

for item in menu.itertuples():
    if item.Category == 'Pizza':
        # 1. Securely insert into Product table
        sql_product = "INSERT INTO Product (name, is_pizza, price) VALUES (%s, %s, %s)"
        val_product = (item.Name, 1, -1)  # Using -1 for pizza base price as in your code
        cursor.execute(sql_product, val_product)
        
        # 2. Get the new product_id
        product_id = cursor.lastrowid
        
        # 3. Insert into Pizza subtype table
        cursor.execute("INSERT INTO Pizza (product_id) VALUES (%s)", (product_id,))
        
        # 4. NEW: Loop through and insert each ingredient
        ingredients_list = [ing.strip() for ing in item.Ingredients.split(',')]
        for ingredient_name in ingredients_list:
            if ingredient_name in ingredient_lookup:
                ing_details = ingredient_lookup[ingredient_name]
                sql_ingredient = """
                    INSERT INTO Ingredient (product_id, name, type, price, quantity) 
                    VALUES (%s, %s, %s, %s, %s)
                """
                val_ingredient = (
                    product_id, 
                    ingredient_name, 
                    ing_details['type'], 
                    ing_details['price'], 
                    1  # Assuming a default quantity of 1 for each ingredient
                )
                cursor.execute(sql_ingredient, val_ingredient)
            else:
                # Optional: Log a warning for ingredients not found in your lookup table
                print(f"Warning: Ingredient '{ingredient_name}' not found for pizza '{item.Name}'.")

    else: # This block handles Drinks and Desserts
        # Securely insert into Product table
        sql_product = "INSERT INTO Product (name, is_pizza, price) VALUES (%s, %s, %s)"
        val_product = (item.Name, 0, item.Price)
        cursor.execute(sql_product, val_product)
        
        product_id = cursor.lastrowid
        
        # Securely insert into Drink or Dessert subtype table
        if item.Category == 'Drink':
            cursor.execute("INSERT INTO Drink (product_id) VALUES (%s)", (product_id,))
        else: # Dessert
            cursor.execute("INSERT INTO Dessert (product_id) VALUES (%s)", (product_id,))
# Load ingredients' data
# Load customers' data
fake = Faker()
# def generate_customer():
#     return {
#         "name": fake.name(),
#         "postcode": fake.postcode(),
#         "birth_date": fake.date_of_birth(minimum_age=18, maximum_age=90).strftime("%Y-%m-%d"),
#         "address": f"{fake.building_number()} {fake.stre ter
# et_name()}, {fake.city()}"
#     }

# customers = [generate_customer() for _ in range(5)]
# for i in range(5):
#     cursor.execute(f"INSERT INTO Customer (name, postcode, birth_date, address) VALUES ('{customers[i]['name']}', '{customers[i]['postcode']}', '{customers[i]['birth_date']}', '{customers[i]['address']}')")
    
def generate_delivery_person():
    
    return {
        "gender": random.choice(['M', 'F']),
        "age": random.randint(18, 50),
    }
    
allowed_postcodes = ["AB12", "CD34", "EF56", "GH78"]
delivery_persons = [generate_delivery_person() for _ in range(len(allowed_postcodes))]
for i in range(len(allowed_postcodes)):
    cursor.execute(f"INSERT INTO DeliveryPerson (gender, age, postcode) VALUES ('{delivery_persons[i]['gender']}', {delivery_persons[i]['age']}, '{allowed_postcodes[i]}')")
    
sample_discounts = ["OFF10","OFF20","OFF18"]
discount_percentages = [10.0,20.0,18.0]
for code in sample_discounts:
    cursor.execute(f"INSERT INTO discountCode (code, percentage) VALUES ('{code}','{discount_percentages[sample_discounts.index(code)]}')")
conn.commit()
cursor.close()
conn.close()