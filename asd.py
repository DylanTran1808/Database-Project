from dotenv import load_dotenv
import os
load_dotenv()
pw = os.getenv("password")

print(pw)