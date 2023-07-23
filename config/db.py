# config/db.py
import os
from pymongo import MongoClient

def get_mongo_client():
    mongo_url = os.getenv("URL")  # Replace with your MongoDB connection string
    return MongoClient(mongo_url)

