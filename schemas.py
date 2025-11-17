"""
Database Schemas for TETO Coffee

Each Pydantic model corresponds to a MongoDB collection where the collection
name is the lowercase of the class name. Example: User -> "user".

These schemas are used for validation at the API boundary and for the
Flames database viewer.
"""

from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import Optional, List
from datetime import datetime


class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password_hash: Optional[str] = Field(None, description="Hashed password (server-side only)")
    avatar_url: Optional[HttpUrl] = Field(None, description="Avatar image")
    is_member: bool = Field(True, description="Membership flag")
    loyalty_points: int = Field(0, ge=0, description="Total loyalty points")


class MenuItem(BaseModel):
    title: str = Field(..., description="Item name")
    description: Optional[str] = Field(None, description="Item description")
    price: float = Field(..., ge=0, description="Price in local currency")
    category: str = Field(..., description="coffee | pastry | special | seasonal")
    image_url: Optional[HttpUrl] = Field(None, description="Image URL (placeholder or real)")
    is_active: bool = Field(True, description="Whether item is visible")


class Reservation(BaseModel):
    name: str = Field(..., description="Guest full name")
    email: EmailStr
    date: str = Field(..., description="YYYY-MM-DD")
    time: str = Field(..., description="HH:MM (24h)")
    guests: int = Field(..., ge=1, le=12)
    special_requests: Optional[str] = None
    member_email: Optional[EmailStr] = Field(None, description="If reserved by a logged-in member")
    status: str = Field("confirmed", description="confirmed | cancelled | completed")


class Event(BaseModel):
    title: str
    description: Optional[str] = None
    date: str = Field(..., description="YYYY-MM-DD")
    time: str = Field(..., description="HH:MM (24h)")
    image_url: Optional[HttpUrl] = None
    capacity: Optional[int] = Field(50, ge=1)
    price: float = Field(0, ge=0, description="0 for free; members may get discounts")


class EventRegistration(BaseModel):
    event_id: str
    name: str
    email: EmailStr
    member_email: Optional[EmailStr] = None
    tier: str = Field("guest", description="guest | member | vip")


class BlogPost(BaseModel):
    title: str
    content: str
    image_url: Optional[HttpUrl] = None
    author: Optional[str] = Field("TETO Team")
    tags: List[str] = Field(default_factory=list)
    published_at: Optional[datetime] = None


class GalleryImage(BaseModel):
    title: Optional[str] = None
    image_url: HttpUrl
    description: Optional[str] = None


class NewsletterSubscriber(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    source: Optional[str] = Field("website")


class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    message: str
    topic: Optional[str] = Field("general")

