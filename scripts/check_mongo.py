import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv('.env.production')
client = MongoClient(os.getenv('MONGO_URI'))
db = client[os.getenv('MONGO_DATABASE')]
coll = db[os.getenv('MONGO_COLLECTION')]

print(f"Total players: {coll.count_documents({})}")
print(f"With 'reports': {coll.count_documents({'reports': {'$exists': True, '$ne': []}})}")
print(f"With 'scout_reports': {coll.count_documents({'scout_reports': {'$exists': True, '$ne': []}})}")

# Show one document structure
doc = coll.find_one()
if doc:
    print(f"\nSample document keys: {list(doc.keys())}")
