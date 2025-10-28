import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import create_document, get_documents, db
from schemas import Client, Invoice

app = FastAPI(title="SaaS Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Utilities ----

def _serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB types to JSON serializable ones."""
    from bson import ObjectId

    out: Dict[str, Any] = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            out[k] = str(v)
        elif isinstance(v, datetime):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


def _collection_name(model_cls: type[BaseModel]) -> str:
    return model_cls.__name__.lower()


# ---- Base routes ----

@app.get("/", tags=["base"]) 
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/health", tags=["base"]) 
def health():
    return {"status": "ok"}


@app.get("/test", tags=["base"]) 
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:  # pragma: no cover - informational
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:  # pragma: no cover - informational
        response["database"] = f"❌ Error: {str(e)[:80]}"

    return response


# ---- Schemas endpoint (for tooling/inspect) ----

@app.get("/schema", tags=["base"]) 
def get_schemas():
    """Expose Pydantic model JSON schemas for collections we use."""
    return {
        "client": Client.model_json_schema(),
        "invoice": Invoice.model_json_schema(),
    }


# ---- Client endpoints ----

@app.get("/clients", tags=["clients"]) 
def list_clients(limit: int = Query(50, ge=1, le=200)):
    docs = get_documents(_collection_name(Client), {}, limit)
    return [_serialize_doc(d) for d in docs]


@app.post("/clients", tags=["clients"], status_code=201) 
def create_client(payload: Client):
    inserted_id = create_document(_collection_name(Client), payload)
    # Fetch inserted to return enriched record
    from bson import ObjectId

    doc = db[_collection_name(Client)].find_one({"_id": ObjectId(inserted_id)})
    return _serialize_doc(doc) if doc else {"_id": inserted_id}


# ---- Invoice endpoints ----

@app.get("/invoices", tags=["invoices"]) 
def list_invoices(
    status: Optional[str] = Query(None, description="Filter by status"),
    client_id: Optional[str] = Query(None, description="Filter by client id"),
    limit: int = Query(50, ge=1, le=200),
):
    filt: Dict[str, Any] = {}
    if status:
        filt["status"] = status
    if client_id:
        filt["client_id"] = client_id
    docs = get_documents(_collection_name(Invoice), filt, limit)
    return [_serialize_doc(d) for d in docs]


@app.post("/invoices", tags=["invoices"], status_code=201) 
def create_invoice(payload: Invoice):
    # Optionally, validate referenced client exists
    if payload.client_id:
        client = db[_collection_name(Client)].find_one({"_id": __import__("bson").ObjectId(payload.client_id)}) if len(payload.client_id) == 24 else None
        if client is None:
            raise HTTPException(status_code=400, detail="Invalid client_id")

    inserted_id = create_document(_collection_name(Invoice), payload)

    from bson import ObjectId

    doc = db[_collection_name(Invoice)].find_one({"_id": ObjectId(inserted_id)})
    return _serialize_doc(doc) if doc else {"_id": inserted_id}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
