from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from backend.deps import get_current_user, get_db, get_optional_user
from backend.models import Favorite, Listing, Review, User
from backend.schemas import (
    CATEGORIES,
    CONDITIONS,
    ListingIn,
    ListingPatch,
)
from backend.serializers import listing_public, review_public, user_brief

router = APIRouter(prefix="/api", tags=["listings"])


def apply_filters(query, q, category, condition, city, min_price, max_price):
    if q:
        like = f"%{q.lower()}%"
        query = query.where(
            func.lower(Listing.title).like(like)
            | func.lower(Listing.description).like(like)
        )
    if category:
        query = query.where(Listing.category == category)
    if condition:
        query = query.where(Listing.condition == condition)
    if city:
        query = query.where(func.lower(Listing.city) == city.lower())
    if min_price is not None:
        query = query.where(Listing.price_cents >= min_price)
    if max_price is not None:
        query = query.where(Listing.price_cents <= max_price)
    return query


SORTS = {
    "recent": Listing.created_at.desc(),
    "price_asc": Listing.price_cents.asc(),
    "price_desc": Listing.price_cents.desc(),
}


def paginate(db: OrmSession, query, page: int, limit: int):
    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    items = db.execute(query.offset((page - 1) * limit).limit(limit)).scalars().all()
    return items, total


def favorite_ids(db: OrmSession, user: User | None, listings: list[Listing]) -> set[int]:
    if user is None or not listings:
        return set()
    ids = [listing.id for listing in listings]
    rows = db.execute(
        select(Favorite.listing_id).where(
            Favorite.user_id == user.id, Favorite.listing_id.in_(ids)
        )
    ).scalars().all()
    return set(rows)


@router.get("/listings")
def list_listings(
    q: str | None = None,
    category: str | None = None,
    condition: str | None = None,
    city: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    sort: str = "recent",
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
    user: User | None = Depends(get_optional_user),
    db: OrmSession = Depends(get_db),
):
    query = select(Listing).where(Listing.status == "active", Listing.stock > 0)
    query = apply_filters(query, q, category, condition, city, min_price, max_price)
    query = query.order_by(SORTS.get(sort, SORTS["recent"]), Listing.id.desc())
    items, total = paginate(db, query, page, limit)
    favs = favorite_ids(db, user, items)
    return {
        "items": [listing_public(i, i.id in favs) for i in items],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/listings/{listing_id}")
def get_listing(
    listing_id: int,
    user: User | None = Depends(get_optional_user),
    db: OrmSession = Depends(get_db),
):
    listing = db.get(Listing, listing_id)
    if listing is None or listing.status != "active":
        raise HTTPException(status_code=404, detail="Anúncio não encontrado")
    other = (
        db.execute(
            select(Listing)
            .where(
                Listing.seller_id == listing.seller_id,
                Listing.id != listing.id,
                Listing.status == "active",
                Listing.stock > 0,
            )
            .order_by(Listing.created_at.desc())
            .limit(4)
        )
        .scalars()
        .all()
    )
    favs = favorite_ids(db, user, [listing, *other])
    return {
        **listing_public(listing, listing.id in favs),
        "seller_listings": [listing_public(i, i.id in favs) for i in other],
    }


@router.get("/listings/{listing_id}/reviews")
def listing_reviews(listing_id: int, db: OrmSession = Depends(get_db)):
    listing = db.get(Listing, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Anúncio não encontrado")
    rows = db.execute(
        select(Review, User.name)
        .join(User, User.id == Review.buyer_id)
        .where(Review.listing_id == listing_id)
        .order_by(Review.created_at.desc())
    ).all()
    return [review_public(r, name) for r, name in rows]


@router.post("/listings", status_code=201)
def create_listing(
    data: ListingIn,
    user=Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    if data.category not in CATEGORIES:
        raise HTTPException(status_code=422, detail="Categoria inválida")
    if data.condition not in CONDITIONS:
        raise HTTPException(status_code=422, detail="Condição inválida")
    listing = Listing(
        seller_id=user.id,
        title=data.title.strip(),
        description=data.description.strip(),
        price_cents=data.price_cents,
        stock=data.stock,
        category=data.category,
        condition=data.condition,
        city=data.city.strip(),
        image_url=data.image_url or None,
    )
    db.add(listing)
    db.commit()
    return listing_public(listing)


@router.patch("/listings/{listing_id}")
def patch_listing(
    listing_id: int,
    data: ListingPatch,
    user=Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    listing = db.get(Listing, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Anúncio não encontrado")
    if listing.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Você não é o dono deste anúncio")
    updates = data.model_dump(exclude_unset=True)
    if "category" in updates and updates["category"] not in CATEGORIES:
        raise HTTPException(status_code=422, detail="Categoria inválida")
    if "condition" in updates and updates["condition"] not in CONDITIONS:
        raise HTTPException(status_code=422, detail="Condição inválida")
    if "status" in updates and updates["status"] not in ("active", "inactive"):
        raise HTTPException(status_code=422, detail="Status inválido")
    for field, value in updates.items():
        if field in ("title", "description", "city") and value is not None:
            value = value.strip()
        setattr(listing, field, value)
    db.commit()
    return listing_public(listing)


@router.get("/me/listings")
def my_listings(
    user=Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
    db: OrmSession = Depends(get_db),
):
    query = (
        select(Listing)
        .where(Listing.seller_id == user.id)
        .order_by(Listing.created_at.desc(), Listing.id.desc())
    )
    items, total = paginate(db, query, page, limit)
    favs = favorite_ids(db, user, items)
    return {
        "items": [listing_public(i, i.id in favs) for i in items],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/sellers/{seller_id}")
def seller_profile(seller_id: int, db: OrmSession = Depends(get_db)):
    seller = db.get(User, seller_id)
    if seller is None:
        raise HTTPException(status_code=404, detail="Vendedor não encontrado")
    stats = db.execute(
        select(func.avg(Review.rating), func.count(Review.id))
        .join(Listing, Listing.id == Review.listing_id)
        .where(Listing.seller_id == seller_id)
    ).one()
    return {
        **user_brief(seller),
        "average_rating": round(float(stats[0]), 2) if stats[0] is not None else None,
        "reviews_count": stats[1],
    }


@router.get("/sellers/{seller_id}/listings")
def seller_listings(
    seller_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
    user: User | None = Depends(get_optional_user),
    db: OrmSession = Depends(get_db),
):
    seller = db.get(User, seller_id)
    if seller is None:
        raise HTTPException(status_code=404, detail="Vendedor não encontrado")
    query = (
        select(Listing)
        .where(
            Listing.seller_id == seller_id,
            Listing.status == "active",
            Listing.stock > 0,
        )
        .order_by(Listing.created_at.desc(), Listing.id.desc())
    )
    items, total = paginate(db, query, page, limit)
    favs = favorite_ids(db, user, items)
    return {
        "items": [listing_public(i, i.id in favs) for i in items],
        "total": total,
        "page": page,
        "limit": limit,
    }
