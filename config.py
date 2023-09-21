import os

username=os.environ['DB_USERNAME']
password=os.environ['DB_PASSWORD']
dbname = "passData"
DATABASE_URI = f"postgresql://{username}:{password}@34.175.112.41:5432/{dbname}"