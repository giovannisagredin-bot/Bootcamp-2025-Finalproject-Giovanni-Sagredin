"""
Migrate existing scout reports from MongoDB Atlas to ChromaDB Cloud
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from pymongo import MongoClient
import chromadb

def create_search_text(player, report):
    """Create searchable text from player and report data"""
    parts = [
        f"Player: {player.get('short_name', '')}",
        f"Position: {report.get('player_position', '')}",
        f"Scout: {report.get('scout_name', '')}",
        f"Report: {report.get('report_text', '')}"
    ]
    return " ".join(parts)

# Load production environment
env_path = project_root / '.env.production'
load_dotenv(env_path)

print("🔧 Migration Script: MongoDB Atlas → ChromaDB Cloud")
print("=" * 60)

# MongoDB Atlas Connection
mongo_uri = os.getenv('MONGO_URI')
mongo_db = os.getenv('MONGO_DATABASE')
mongo_collection = os.getenv('MONGO_COLLECTION')

if not mongo_uri or not mongo_db or not mongo_collection:
    raise ValueError("Missing required MongoDB environment variables")

print(f"📊 MongoDB Atlas: {mongo_db}/{mongo_collection}")

# ChromaDB Cloud Connection
chroma_api_key = os.getenv('CHROMA_API_KEY')
chroma_tenant = os.getenv('CHROMA_TENANT')
chroma_database = os.getenv('CHROMA_DATABASE')

print(f"🔮 ChromaDB Cloud: {chroma_tenant}/{chroma_database}")
print()

# Connect to MongoDB Atlas
print("⏳ Connecting to MongoDB Atlas...")
mongo_client = MongoClient(mongo_uri)
db = mongo_client[mongo_db]
collection = db[mongo_collection]

# Count reports
total_reports = collection.count_documents({"reports": {"$exists": True, "$ne": []}})
print(f"✓ Found {total_reports} players with reports")

# Connect to ChromaDB Cloud
print("⏳ Connecting to ChromaDB Cloud...")
chroma_client = chromadb.CloudClient(
    api_key=chroma_api_key,
    tenant=chroma_tenant,
    database=chroma_database
)

# Get or create collection
chroma_collection = chroma_client.get_or_create_collection(
    name="scout_reports",
    metadata={"description": "Football scout reports"}
)

current_count = chroma_collection.count()
print(f"✓ ChromaDB collection ready (current count: {current_count})")
print()

# Migrate reports
print("⏳ Migrating reports to ChromaDB Cloud...")
documents_to_add = []
ids_to_add = []
metadatas_to_add = []

players_with_reports = collection.find({"reports": {"$exists": True, "$ne": []}})

for player in players_with_reports:
    player_id = str(player['_id'])
    player_name = player.get('short_name', 'Unknown')
    
    for report in player.get('reports', []):
        report_id = str(report['_id'])
        
        # Create search text (same format as ETL pipeline)
        search_text = create_search_text(player, report)
        
        # Prepare document for ChromaDB
        documents_to_add.append(search_text)
        ids_to_add.append(report_id)
        metadatas_to_add.append({
            'player_id': player_id,
            'player_name': player_name,
            'player_position': report.get('player_position', ''),
            'scout_name': report.get('scout_name', ''),
            'timestamp': report.get('timestamp', '')
        })
        
        print(f"  • {player_name} - Report {report_id[:8]}...")

# Add all documents to ChromaDB Cloud in batch
if documents_to_add:
    print()
    print(f"⏳ Uploading {len(documents_to_add)} reports to ChromaDB Cloud...")
    chroma_collection.add(
        documents=documents_to_add,
        ids=ids_to_add,
        metadatas=metadatas_to_add
    )
    print(f"✅ Successfully migrated {len(documents_to_add)} reports to ChromaDB Cloud!")
else:
    print("⚠️ No reports to migrate")

# Verify migration
final_count = chroma_collection.count()
print()
print("=" * 60)
print(f"✅ Migration Complete!")
print(f"   ChromaDB Cloud collection: {final_count} documents")
print("=" * 60)

mongo_client.close()
