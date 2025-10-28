"""
Database Schemas

Define MongoDB collection schemas using Pydantic models.
Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- Client -> "client"
- Invoice -> "invoice"
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, EmailStr


class Client(BaseModel):
    """Clients collection schema"""
    name: str = Field(..., description="Client full name or company name", min_length=2, max_length=120)
    email: Optional[EmailStr] = Field(None, description="Primary contact email")
    phone: Optional[str] = Field(None, description="Contact phone number")
    company: Optional[str] = Field(None, description="Company name if individual contact")
    address: Optional[str] = Field(None, description="Mailing address")
    notes: Optional[str] = Field(None, description="Internal notes about the client")
    status: Literal["active", "inactive", "prospect"] = Field("active", description="Lifecycle status")


class InvoiceItem(BaseModel):
    description: str = Field(..., min_length=1, max_length=200)
    quantity: float = Field(1, ge=0)
    unit_price: float = Field(..., ge=0)


class Invoice(BaseModel):
    """Invoices collection schema"""
    invoice_number: Optional[str] = Field(None, description="Human-friendly invoice number, e.g., INV-0001")
    client_id: Optional[str] = Field(None, description="ID of the client this invoice belongs to")
    issue_date: Optional[str] = Field(None, description="ISO date string when invoice was issued")
    due_date: Optional[str] = Field(None, description="ISO date string when invoice is due")
    items: list[InvoiceItem] = Field(default_factory=list)
    currency: Literal["USD", "EUR", "GBP", "INR", "JPY", "AUD", "CAD"] = Field("USD")
    status: Literal["draft", "sent", "paid", "overdue", "cancelled"] = Field("draft")
    notes: Optional[str] = Field(None, description="Public notes shown on invoice")
    terms: Optional[str] = Field(None, description="Payment terms")


# Example additional schemas kept minimal for reference (not used by routes)
class User(BaseModel):
    name: str
    email: EmailStr
    is_active: bool = True


class Product(BaseModel):
    title: str
    price: float
    in_stock: bool = True
