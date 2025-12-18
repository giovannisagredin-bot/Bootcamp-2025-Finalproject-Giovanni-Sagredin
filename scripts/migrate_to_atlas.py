#!/usr/bin/env python3
"""Migrate data from local MongoDB to Atlas"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load Atlas credentials
load_dotenv('.env.production')

# Local MongoDB
local_client = MongoClient('mongodb://localhost:27017')
local_db = local_client['player-dataset']

# Atlas MongoDB
atlas_uri = os.getenv('MONGO_URI')
atlas_client = MongoClient(atlas_uri)
atlas_db = atlas_client['player-dataset']

print("🔄 Migrating data from local MongoDB to Atlas...")

# Migrate players collection
print("\n📊 Migrating players...")
players = list(local_db['final-project'].find({}))
if players:
    atlas_db['final-project'].delete_many({})  # Clear existing
    atlas_db['final-project'].insert_many(players)
    print(f"✅ Migrated {len(players)} players")
else:
    print("⚠️ No players found in local DB")

# Migrate scout reports
print("\n📝 Migrating scout reports...")
reports = list(local_db['scout_reports'].find({}))
if reports:
    atlas_db['scout_reports'].delete_many({})  # Clear existing
    atlas_db['scout_reports'].insert_many(reports)
    print(f"✅ Migrated {len(reports)} scout reports")
else:
    print("⚠️ No reports found in local DB")

print("\n🎉 Migration complete!")
print(f"\n📍 Atlas URI: {atlas_uri[:50]}...")
print(f"📍 Database: player-dataset")
print(f"📍 Collections: final-project ({len(players)} docs), scout_reports ({len(reports)} docs)")
