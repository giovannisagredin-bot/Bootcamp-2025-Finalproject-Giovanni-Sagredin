"""
Migrate scout reports from MongoDB Atlas to ChromaDB Cloud via HTTP API
"""
import os
import sys
from pathlib import Path
import requests
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from pymongo import MongoClient

# Load production environment
env_path = project_root / '.env.production'
load_dotenv(env_path)

print("🔧 Migration: MongoDB Atlas → ChromaDB Cloud (HTTP API)")
print("=" * 60)

# MongoDB Atlas
mongo_uri = os.getenv('MONGO_URI')
mongo_db = os.getenv('MONGO_DATABASE')
mongo_collection = os.getenv('MONGO_COLLECTION')

# ChromaDB Cloud
chroma_api_key = os.getenv('CHROMA_API_KEY')
chroma_tenant = os.getenv('CHROMA_TENANT')
chroma_database = os.getenv('CHROMA_DATABASE')

print(f"📊 MongoDB: {mongo_db}/{mongo_collection}")
print(f"🔮 ChromaDB: {chroma_tenant}/{chroma_database}")
print()

# Connect to MongoDB
print("⏳ Connecting to MongoDB Atlas...")
mongo_client = MongoClient(mongo_uri)
db = mongo_client[mongo_db]

# Get scout reports from dedicated collection
reports_collection = db['scout_reports']
total_reports = reports_collection.count_documents({})
print(f"✓ Found {total_reports} scout reports in 'scout_reports' collection")
print()

# ChromaDB Cloud API endpoint (using Python client instead of HTTP)
print("⏳ Connecting to ChromaDB Cloud...")
import chromadb

try:
    chroma_client = chromadb.CloudClient(
        api_key=chroma_api_key,
        tenant=chroma_tenant,
        database=chroma_database
    )
    scout_collection = chroma_client.get_or_create_collection(name="scout_reports")
    print(f"✓ Connected to ChromaDB Cloud (current count: {scout_collection.count()})")
except Exception as e:
    print(f"❌ Error connecting to ChromaDB Cloud: {e}")
    sys.exit(1)

print()



# Prepare documents
print("⏳ Preparing documents...")
documents = []
metadatas = []
ids = []

for report in reports_collection.find():
    report_id = str(report['_id'])
    player_name = report.get('player_name', 'Unknown')
    
    # Create search text
    search_text = f"""Player: {player_name}
Position: {report.get('player_position', 'N/A')}
Scout: {report.get('scout_name', 'N/A')}
Report: {report.get('report_text', 'N/A')}
Standardized: {report.get('standardized_report', 'N/A')}"""
    
    documents.append(search_text)
    ids.append(report_id)
    metadatas.append({
        'player_id': str(report.get('player_id', '')),
        'player_name': player_name,
        'player_position': report.get('player_position', ''),
        'scout_name': report.get('scout_name', ''),
        'timestamp': str(report.get('timestamp', ''))
    })
    
    print(f"  • {player_name} - {report_id[:8]}...")

# Add documents to ChromaDB
print()
print(f"⏳ Uploading {len(documents)} reports to ChromaDB Cloud...")

try:
    scout_collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    print(f"✅ Successfully uploaded {len(documents)} reports!")
except Exception as e:
    print(f"❌ Error uploading: {e}")
    sys.exit(1)

# Verify
final_count = scout_collection.count()

print()
print("=" * 60)
print(f"✅ Migration Complete!")
print(f"   ChromaDB Cloud: {final_count} documents")
print("=" * 60)

mongo_client.close()
