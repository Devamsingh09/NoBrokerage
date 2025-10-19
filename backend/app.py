from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from nlp.parser import parse_query
from services.search import load_dataframes, search_and_summarize

app = FastAPI(title="NoBrokerage Chat Search API")

# Allow local frontend origins (dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load CSVs once at startup (keeps simple for assignment)
DF = load_dataframes()

class Query(BaseModel):
    q: str

@app.get("/health")
def health():
    return {"status": "ok", "rows": len(DF)}

@app.post("/api/search")
def api_search(query: Query):
    parsed = parse_query(query.q)
    result = search_and_summarize(DF, parsed, max_results=20)
    return {"parsed": parsed, "summary": result["summary"], "cards": result["cards"]}
