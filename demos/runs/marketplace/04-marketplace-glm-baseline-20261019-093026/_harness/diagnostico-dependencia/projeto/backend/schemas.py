from pydantic import BaseModel, EmailStr, Field

CATEGORIES = ["eletronicos", "casa", "livros", "moda", "outros"]
CONDITIONS = ["novo", "usado"]


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserPatch(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class ListingIn(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=10, max_length=5000)
    price_cents: int = Field(gt=0)
    stock: int = Field(ge=1, le=999)
    category: str
    condition: str
    city: str = Field(min_length=1, max_length=120)
    image_url: str | None = Field(default=None, max_length=500)


class ListingPatch(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, min_length=10, max_length=5000)
    price_cents: int | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=1, le=999)
    category: str | None = None
    condition: str | None = None
    city: str | None = Field(default=None, min_length=1, max_length=120)
    image_url: str | None = Field(default=None, max_length=500)
    status: str | None = None


class ConversationIn(BaseModel):
    listing_id: int


class MessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class OrderIn(BaseModel):
    listing_id: int
    quantity: int = Field(gt=0, le=999)
    address: str = Field(min_length=1, max_length=500)


class StatusIn(BaseModel):
    status: str


class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=1000)
