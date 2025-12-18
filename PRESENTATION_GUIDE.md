# 🎤 GUIDA PRESENTAZIONE FINAL PROJECT

## PITCH 

**"Ho sviluppato un sistema intelligente per scout calcistici che risolve 2 problemi:**

- **Problema 1**: I report degli scout contengono linguaggio inappropriato → **Soluzione**: Filtro automatico con toxicity detection
- **Problema 2**: Cercare info su 50k giocatori è impossibile → **Soluzione**: RAG con semantic search"

**Demo live**: Mostra il frontend (static/index.html)
- Tab "Submit Report" con toxicity che blocca
- Tab "Search Players" con domanda tipo "fast striker under 25"

---

## ARCHITETTURA 

**Stack tecnologico:**
- **Backend**: FastAPI con Python 3.12
- **Database**: MongoDB 100 giocatori + report    
- **Vector Store**: ChromaDB con sentence-transformers
- **LLM**: OpenAI GPT-4o-mini / Gemini 1.5 Flash
- **Frontend**: Vanilla JS (no framework)

**Flusso dati**:
```
User → FastAPI → ETL Pipeline → MongoDB + ChromaDB
User → Search → RAG Agent → LLM → Risposta
```

---

## DEEP CODEBASE WALKTHROUGH 



1. **app/pipeline/etl.py** - Pipeline ETL con 3 fasi:
   - Extract → Transform (toxicity + LLM standardization) → Load (dual storage)

2. **app/vectorstore/manager.py** - Wrapper ChromaDB con automatic embeddings

3. **app/agents/search_agent.py** - RAG orchestrator (vector search + LLM)

4. **app/api/routes_scouting.py** + **routes_search.py** - API endpoints separati

5. **src/llm/** - Strategy pattern per multi-provider LLM

---

## DESIGN PATTERNS 

**Pattern implementati:**
- **Strategy Pattern**: `GenerativeAIClient` con OpenAI/Gemini/Mock interscambiabili
- **Repository Pattern**: `VectorStoreManager` astrae ChromaDB
- **Pipeline Pattern**: ETL con Extract→Transform→Load
- **Dependency Injection**: Fixtures pytest per testing

---

## TESTING & QUALITY 

**Test Pyramid implementata:**
- **Unit**: tests/test_vectorstore.py (ChromaDB operations)
- **Integration**: test_search_agent.py (RAG flow completo)
- **E2E**: tests/test_api_endpoints.py (API HTTP)

**Observability**: Logging strutturato in app/core/logging.py

---

## DEPLOYMENT 

**Docker ready**: 
```bash
???????
```

---

# 📚 RIASSUNTO CODICE PER CLASSE/FUNZIONE

## 🔷 PIPELINE (app/pipeline/etl.py)

**Classe `ScoutReportETL`**:
- `__init__(db, llm_client, vector_store)` - Setup con dipendenze iniettate
- `process_report(player_id, text)` - Orchestrazione completa del flusso ETL
- `_extract(player_id, text)` - Crea oggetto domain model da input raw
- `_transform(report)` - Applica toxicity check + LLM standardization
- `_load(report)` - Salva su MongoDB + ChromaDB automaticamente

**Classe `ToxicityFilter` (app/pipeline/toxicity.py)**:
- `analyze(text)` - Detecta parolacce/linguaggio offensivo
- Ritorna `ToxicityAnalysis(is_toxic, severity, categories)`

---

## 🔷 VECTOR STORE (app/vectorstore/manager.py)

**Classe `VectorStoreManager`**:
- `__init__(persist_directory)` - Inizializza ChromaDB con persistenza su disco
- `add_documents(documents, metadatas, ids)` - Aggiunge documenti con embedding automatico
- `similarity_search(query, top_k)` - Cerca semanticamente usando embeddings
- `rebuild_index_from_mongodb(db)` - Ricostruisce indice completo da MongoDB
- `get_stats()` - Ritorna statistiche della collection (count, ecc)

---

## 🔷 RAG AGENT (app/agents/search_agent.py)

**Classe `SearchAgent`**:
- `__init__(vector_store, llm_client, db)` - Setup componenti RAG
- `search(query, top_k)` - Flusso RAG completo:
  1. Vector search su ChromaDB per trovare report rilevanti
  2. Enrich con dettagli completi da MongoDB
  3. LLM genera risposta contestuale usando i sources
- `_enrich_sources(results)` - Fetcha informazioni complete da MongoDB
- `_generate_answer(query, sources)` - Prompt engineering per LLM con context

---

## 🔷 LLM CLIENTS (src/llm/)

**Classe base `GenerativeAIClient` (Abstract Base Class)**:
- `generate(prompt, system)` - Interfaccia standard per generazione testo
- `count_tokens(text)` - Conta token per rate limiting e cost tracking

**Implementazioni concrete**:
- **`OpenAIClient`** - Usa GPT-4o-mini con streaming support
- **`GeminiClient`** - Usa Gemini 1.5 Flash con safety settings configurabili
- **`MockLLMClient`** - Fake LLM per testing senza chiamate API reali

---

## 🔷 API ROUTES

**app/api/routes_scouting.py**:
- `POST /api/reports` - Submit nuovo scout report con toxicity check automatico
- `GET /api/players/search?q={name}` - Autocomplete per cercare giocatori in MongoDB

**app/api/routes_search.py**:
- `POST /api/search` - RAG search semantico che ritorna risposta LLM + sources

---

## 🔷 DATABASE (app/core/database.py)

**Funzioni principali**:
- `get_database()` - Ritorna MongoDB database connection con pooling
- `get_players_collection()` - Getter per collection "final-project" (50k giocatori)
- `get_reports_collection()` - Getter per collection "scout_reports" (user submissions)

**Lifespan context manager** in app/main.py:
- Gestisce apertura/chiusura connection MongoDB automaticamente

---

## 🔷 MODELS

**app/models/domain.py** (Business logic layer):
- `ScoutReport` - Dataclass con validation delle business rules
- `Player` - Dataclass rappresentazione giocatore

**app/models/schemas.py** (API contracts / DTOs):
- `ScoutReportCreate` - DTO per validare POST request body
- `ToxicityAnalysis` - Response schema per toxicity check
- `PlayerSearchResult` - Response schema per autocomplete giocatori

---

## 🔷 TESTING

**tests/conftest.py**:
- `client` fixture - TestClient FastAPI per testare HTTP endpoints
- Setup mock temporanei per isolamento completo dei test

**tests/test_vectorstore.py**:
- `temp_vectorstore` fixture - ChromaDB temporaneo con cleanup automatico
- Test CRUD operations: add, search, empty collection handling

**tests/test_api_endpoints.py**:
- Test E2E su tutti gli endpoint HTTP
- Validation di status codes + response structure
- Test casi edge: toxic content, player non esistente, ecc

---



---

# 🎯 DOMANDE PROBABILI E RISPOSTE

**Q: Perché hai scelto ChromaDB invece di Pinecone/Weaviate?**
A: ChromaDB è open-source, gira local senza servizi esterni, e ha persistenza su disco. Per un progetto didattico è perfetto perché non serve setup cloud.

**Q: Come gestisci il rate limiting delle API LLM?**
A: Ho un `RateLimiter` in src/utils/rate_limiter.py che traccia le chiamate e blocca se supero la soglia.

**Q: I test coprono casi edge?**
A: Sì, testo: toxic content, player inesistente, empty vector store, invalid ObjectId MongoDB.

**Q: Come scali se i dati crescono?**
A: MongoDB ha sharding built-in, ChromaDB supporta indici distribuiti. Per ora con  docs va veloce.

**Q: Hai considerato la privacy dei dati scout?**
A: Non salvo dati sensibili. I report sono anonimi tranne player_id. In produzione aggiungerei auth JWT.

---

# 🚀 CHECKLIST PRE-PRESENTAZIONE

- [ ] MongoDB running su localhost:27017
- [ ]  giocatori caricati in collection "final-project"
- [ ] ChromaDB vectorstore popolato (almeno qualche report di test)
- [ ] Frontend aperto in browser (http://localhost:8000/static/index.html)
- [ ] VS Code aperto con i file chiave bookmarkati
- [ ] Terminal con `uvicorn app.main:app --reload` attivo
- [ ] Hai provato almeno 2-3 query di esempio che funzionano bene

**Buona presentazione! 🎉**
