# Football Scout Report System

Sistema per gestire report di scouting calcistico con ricerca semantica e analisi AI.

## Cosa fa

Questo progetto permette di:
- Inserire report su giocatori con controllo automatico della tossicità 
- Cercare giocatori usando linguaggio naturale tipo "trova terzino veloce bravo nei cross"
- Ottenere risposte intelligenti dall'AI che analizza i report salvati

Il sistema usa un pipeline ETL che processa i report, li salva su MongoDB e li indicizza su ChromaDB per la ricerca vettoriale. Poi c'è un agente RAG (Retrieval-Augmented Generation) che cerca i report più rilevanti e usa GPT-4 o Gemini per generare risposte.

## Architettura

```
Player Report -> Toxicity Check -> ETL Pipeline -> MongoDB + ChromaDB
                                                         
                                              Vector Search + LLM → AI Answer
```

**Stack:**
- Backend: FastAPI (per le API REST)
- Database: MongoDB (50k giocatori da Kaggle + i report)
- Vector Store: ChromaDB con sentence-transformers per gli embeddings
- LLM: OpenAI GPT-4 o Google Gemini (c'è anche un client Mock per testare)
- Frontend: HTML/CSS/JS vanilla (no framework, tenuto semplice)

## Setup

### Prerequisiti
- Python 3.12 
- MongoDB in esecuzione (localhost:27017)
- Una API key di OpenAI o Google (oppure usa il provider "mock" per testare senza API)

### Installazione




2. **Crea virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. **Installa le dipendenze**
```bash
pip install -r requirements.txt
```

4. **Configura le variabili d'ambiente**

Crea un file `.env` nella root:
```env
# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=final-project

# LLM API Keys
OPENAI_API_KEY=your_openai_key_here
GOOGLE_API_KEY=your_google_key_here

# Vector Store
VECTORSTORE_PERSIST_DIR=./data/vectorstore
```

5. **Load player data** (50k players from Kaggle)
```baCarica i dati dei giocatori**
```bash
# Metti il CSV dei giocatori in data/raw/
# Deve essere caricato su MongoDB nella collection "final-project"
# (Io ho usato il dataset Kaggle con 50k giocatori)
```

### Avvio

```bash
uvicorn app.main:app --reload --port 8000
```

Apri il browser su **http://localhost:8000**

## Come si usa

### Inserire un report

1. Tab "Submit Report"
2. Cerca il giocatore (autocomplete dalla barra di ricerca)
3. Scrivi il report
4. Submit → il sistema controlla se ci sono parolacce → elabora con l'LLM → salva su MongoDB e ChromaDB

### Cercare giocatori

1. Tab "Search Players"
2. Scrivi una query in linguaggio naturale, tipo:
   - "Trova terzino destro veloce bravo nei cross"
   - "Centrocampista tecnico con visione di gioco"
3. Scegli quanti risultati vuoi (3/5/10)
4. Seleziona il provider LLM (OpenAI/Google/Mock)
5. L'AI ti dà una risposta con i report più rilevanti

```bash
pytest tests/ -v
```

Ho scritto test per:
- Vector store (add, search, metadata)
- Search agent (RAG flow)
- API endpoints (submit, search, validazione)

## Struttura progetto
## 📁 Project Structure

```
app/
├── agents/         # Search agent (RAG)
├── api/           # FastAPI routes
├── core/          # Config, database, logging
├── models/        # Pydantic schemas
├── pipeline/      # ETL with toxicity check
└── vectorstore/   # ChromaDB manager

src/
└── llm/           # LLM clients (OpenAI, Gemini, Mock)

static/
└── index.html     # Frontend UI (submit + search tabs)

tests/             # Pytest suite
data/
├── vectorstore/   # ChromaDB persistence
└── raw/           # Player CSV data
```

## 🎯 API Endpoints

### Submit Report
```API Endpoints

**Submit Report**
```
POST /api/reports
{
  "player_id": 123,
  "report_text": "Ottimo attaccante, ottimo posizionamento..."
}
```

**Search Players**
```
POST /api/search
{
  "query": "attaccante veloce bravo di testa",
  "top_k": 5,
  "provider": "openai"
}
```

**Autocomplete Giocatori**
```
GET /api/players/search?q=Messi
```

## Configurazione

Se vuoi cambiare qualcosa:

- Soglia tossicità: `app/pipeline/toxicity.py` (default 0.7)
- Modello embeddings: `app/vectorstore/manager.py` (uso all-MiniLM-L6-v2)
- Modelli LLM: OpenAI usa gpt-4o-mini, Google usa gemini-1.5-flash

## Problemi comuni

**MongoDB non si connette**
```bash
# Controlla che MongoDB sia avviato
mongod --version
net start MongoDB  # Windows
```

**Vector store vuoto quando cerchi**
- Devi prima inserire almeno un report
- I report vengono automaticamente aggiunti a ChromaDB quando li inserisci

**Errori API LLM**
- Controlla le API key nel `.env`
- Oppure usa `provider: "mock"` per testare senza chiamate API

## TODO (cose che vorrei aggiungere)

- Autenticazione utenti
- Export PDF dei report
- Filtri avanzati (posizione, età, nazionalità)
- Storico e modifica report
- Supporto multilingua

## Autore

Giovanni Sagredin - Progetto finale Bootcamp 2025