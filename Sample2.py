from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

db_password = os.getenv("password")
# Replace username, password, host, port, and database with your values
engine = create_engine(f"mysql+pymysql://root:{db_password}@localhost:3306/pizza_ordering")

conn = engine.connect()

print("Connection to the database was successful!")
conn.close()