#!/usr/bin/env python3
"""Export both players and scout reports for Docker import"""

from pymongo import MongoClient
import json
from datetime import datetime
from bson import ObjectId

# Connect to local MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client['player-dataset']

# Export players
print("Exporting players...")
players = list(db['final-project'].find({}))
for player in players:
    player['_id'] = str(player['_id'])

with open('data/raw/players_export.json', 'w', encoding='utf-8') as f:
    for player in players:
        f.write(json.dumps(player, ensure_ascii=False) + '\n')
print(f"✓ Exported {len(players)} players")

# Export scout reports
print("Exporting scout reports...")
reports = list(db['scout_reports'].find({}))
for report in reports:
    # Convert all non-JSON-serializable types
    for key, value in list(report.items()):
        if isinstance(value, ObjectId):
            report[key] = str(value)
        elif isinstance(value, datetime):
            report[key] = value.isoformat()

with open('data/raw/reports_export.json', 'w', encoding='utf-8') as f:
    for report in reports:
        f.write(json.dumps(report, ensure_ascii=False) + '\n')
print(f"✓ Exported {len(reports)} scout reports")

print("\n✅ Export complete!")
