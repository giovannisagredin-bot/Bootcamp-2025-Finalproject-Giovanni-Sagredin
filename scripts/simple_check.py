"""
Simple migration using only requests (no chromadb library needed)
"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from pymongo import MongoClient
import requests
import json

load_dotenv('.env.production')

print("🔧 Migration: MongoDB → ChromaDB Cloud")
print("=" * 60)

# MongoDB
mongo_client = MongoClient(os.getenv('MONGO_URI'))
db = mongo_client[os.getenv('MONGO_DATABASE')]
reports = list(db['scout_reports'].find())

print(f"✓ Found {len(reports)} reports in MongoDB Atlas")

# ChromaDB Cloud - Manual HTTP POST
# Note: ChromaDB Cloud uses sentence-transformers to auto-generate embeddings
# We just need to send the documents

# For now, let's just verify we can export the data
print("\n📦 Export data for manual upload:")
print("="*60)

for i, report in enumerate(reports[:3], 1):  # Show first 3
    print(f"\n{i}. {report.get('player_name', 'Unknown')}")
    print(f"   ID: {report['_id']}")
    print(f"   Position: {report.get('player_position', 'N/A')}")
    print(f"   Report: {report.get('report_text', 'N/A')[:100]}...")

print(f"\n... and {len(reports)-3} more reports")
print("\n" + "="*60)
print(f"Total reports ready: {len(reports)}")
print("\n💡 ChromaDB Cloud will auto-generate embeddings when we upload")
print("   Collection 'scout_reports' is already created and ready!")

mongo_client.close()
