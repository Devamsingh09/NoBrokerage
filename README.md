# NoBrokerage Chat Search — Assignment

Minimal Chat + Search prototype that reads CSV project data and lets a user query naturally.

## Stack
- Backend: FastAPI + Pandas
- Frontend: React + Vite (simple chat UI)
- No LLM required (rule-based parser). Optional to plug LLM.

## Setup

### Backend
1. `cd backend`
2. Create venv: `python -m venv .venv`
3. Activate: `source .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\activate` (Windows)
4. Install: `pip install -r requirements.txt`
5. Put your CSVs in `backend/data/`:
   - `project.csv`
   - `ProjectAddress.csv`
   - `ProjectConfiguration.csv`
   - `ProjectConfigurationVariant.csv`
6. Run server: `uvicorn app:app --reload --port 8000`
7. Health: `GET http://localhost:8000/health`

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm run dev`
4. Open `http://localhost:5173` (Vite dev)

## Example queries
- `3BHK flat in Pune under ₹1.2 Cr`
- `2BHK ready to move in Mumbai under ₹90 L`
- `3BHK near Wakad Pune`

## Notes
- Summaries are generated only from CSV data — no external data used.
- If CSV column names differ, adjust `backend/app.py` to map your columns.
- Optional improvements:
  - Add semantic search with embeddings (sentence-transformers + faiss)
  - Use a small HF model for more robust NER/parsing
  - Add images & pagination to cards

## Tests
`cd backend` and `pytest`

