import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv('.env.production')
client = MongoClient(os.getenv('MONGO_URI'))
db = client[os.getenv('MONGO_DATABASE')]

print(f"Database: {os.getenv('MONGO_DATABASE')}")
print(f"\nAll collections:")
for name in db.list_collection_names():
    count = db[name].count_documents({})
    print(f"  - {name}: {count} documents")
    
    # Check if it has reports
    with_reports = db[name].count_documents({'scout_reports': {'$exists': True, '$ne': []}})
    if with_reports > 0:
        print(f"    → {with_reports} have scout_reports!")
