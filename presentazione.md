POST /api/reports 
  ↓
routes_scouting.py (route layer)
  ↓
ToxicityAnalyzer (validation)
  ↓
ScoutReportPipeline (service/ETL)
  ↓
GenerativeAIClient (LLM extraction)
  ↓
MongoDB + VectorStoreManager (repositories)
  ↓
Response (report_id, summary)



POST /api/search
  ↓
routes_search.py (route layer)
  ↓
SearchAgent (service/orchestration)
  ↓
VectorStoreManager (similarity search)
  ↓
MongoDB (enrichment con dati completi)
  ↓
GenerativeAIClient (LLM answer generation)
  ↓
Response (answer + sources)




next steps


service  toxcity filter perspective api 
processing asincrono
evaluation su quality delle rag
add new player on mongodb
scout scoring 
file upload for scout system
last news on internet for that player
correttore grammaticale e traduttore 