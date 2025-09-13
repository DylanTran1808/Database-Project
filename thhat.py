from dotenv import load_dotenv
import os

load_dotenv()  # looks for .env file in the current directory

# Access variables
db_user = os.getenv("password")

print(db_user)