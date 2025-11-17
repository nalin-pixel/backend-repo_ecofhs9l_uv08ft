import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import EmailStr
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import (
    User,
    MenuItem,
    Reservation,
    Event,
    EventRegistration,
    BlogPost,
    GalleryImage,
    NewsletterSubscriber,
    ContactMessage,
)

app = FastAPI(title="TETO Coffee API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"service": "TETO Coffee Backend", "status": "ok"}


@app.get("/test")
def test_database():
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
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response


# --- Utility ---

def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")


# --- Menu Endpoints ---

@app.get("/api/menu", response_model=List[MenuItem])
def list_menu():
    items = get_documents("menuitem", {"is_active": True})
    # strip MongoDB-specific fields for response model compliance
    for i in items:
        i.pop("_id", None)
    return items


@app.post("/api/menu", status_code=201)
def create_menu_item(item: MenuItem):
    new_id = create_document("menuitem", item)
    return {"id": new_id}


# --- Reservations ---

@app.post("/api/reservations", status_code=201)
def create_reservation(res: Reservation):
    new_id = create_document("reservation", res)
    return {"id": new_id, "status": "confirmed"}


@app.get("/api/reservations")
def list_reservations(email: Optional[EmailStr] = None):
    filt = {"email": str(email)} if email else {}
    docs = get_documents("reservation", filt)
    for d in docs:
        d["id"] = str(d.pop("_id", ""))
    return docs


# --- Events ---

@app.get("/api/events")
def list_events():
    docs = get_documents("event", {})
    for d in docs:
        d["id"] = str(d.pop("_id", ""))
    return docs


@app.post("/api/events", status_code=201)
def create_event(event: Event):
    new_id = create_document("event", event)
    return {"id": new_id}


@app.post("/api/events/{event_id}/register", status_code=201)
def register_event(event_id: str, reg: EventRegistration):
    # ensure event exists
    ev = db["event"].find_one({"_id": to_object_id(event_id)})
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    payload = reg.model_dump()
    payload["event_id"] = event_id
    new_id = db["eventregistration"].insert_one(payload).inserted_id
    return {"id": str(new_id)}


# --- Blog ---

@app.get("/api/blog")
def list_posts():
    posts = get_documents("blogpost", {})
    for p in posts:
        p["id"] = str(p.pop("_id", ""))
    return posts


@app.post("/api/blog", status_code=201)
def create_post(post: BlogPost):
    if post.published_at is None:
        post.published_at = datetime.utcnow()
    new_id = create_document("blogpost", post)
    return {"id": new_id}


# --- Gallery ---

@app.get("/api/gallery")
def list_gallery():
    imgs = get_documents("galleryimage", {})
    for g in imgs:
        g["id"] = str(g.pop("_id", ""))
    return imgs


@app.post("/api/gallery", status_code=201)
def add_gallery_image(img: GalleryImage):
    new_id = create_document("galleryimage", img)
    return {"id": new_id}


# --- Newsletter ---

@app.post("/api/newsletter", status_code=201)
def subscribe(sub: NewsletterSubscriber):
    # upsert by email
    existing = db["newslettersubscriber"].find_one({"email": sub.email})
    if existing:
        db["newslettersubscriber"].update_one({"_id": existing["_id"]}, {"$set": sub.model_dump()})
        return {"id": str(existing["_id"]), "updated": True}
    new_id = create_document("newslettersubscriber", sub)
    return {"id": new_id, "updated": False}


# --- Contact / Feedback ---

@app.post("/api/contact", status_code=201)
def contact(msg: ContactMessage):
    new_id = create_document("contactmessage", msg)
    return {"id": new_id, "received": True}


# --- Simple Auth Scaffold (email/password)
# Note: For production, integrate a real auth provider. This is a minimal placeholder to match UI flows.

from hashlib import sha256


def hash_password(password: str) -> str:
    return sha256(password.encode()).hexdigest()


@app.post("/api/auth/register")
def register_user(name: str, email: EmailStr, password: str):
    if db["user"].find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(name=name, email=email, password_hash=hash_password(password))
    new_id = db["user"].insert_one(user.model_dump()).inserted_id
    return {"id": str(new_id)}


@app.post("/api/auth/login")
def login_user(email: EmailStr, password: str):
    u = db["user"].find_one({"email": email})
    if not u or u.get("password_hash") != hash_password(password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # minimal session token mock
    token = sha256(f"{email}:{u.get('_id')}".encode()).hexdigest()
    return {"token": token, "name": u.get("name"), "email": email, "loyalty_points": u.get("loyalty_points", 0)}


# --- Analytics placeholders ---

@app.post("/api/analytics/track")
def track(event_name: str, path: Optional[str] = None, metadata: Optional[str] = None):
    payload = {
        "event_name": event_name,
        "path": path,
        "metadata": metadata,
        "ts": datetime.utcnow(),
    }
    db["analytics_event"].insert_one(payload)
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
