from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from backend.deps import get_current_user, get_db
from backend.models import Favorite, Listing
from backend.routers.listings import paginate
from backend.serializers import listing_public

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.post("/{listing_id}", status_code=204)
def add_favorite(
    listing_id: int,
    user=Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    listing = db.get(Listing, listing_id)
    if listing is None or listing.status != "active":
        raise HTTPException(status_code=404, detail="Anúncio não encontrado")
    exists = db.execute(
        select(Favorite).where(
            Favorite.user_id == user.id, Favorite.listing_id == listing_id
        )
    ).scalar_one_or_none()
    if not exists:
        db.add(Favorite(user_id=user.id, listing_id=listing_id))
        db.commit()
    return Response(status_code=204)


@router.delete("/{listing_id}", status_code=204)
def remove_favorite(
    listing_id: int,
    user=Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    db.query(Favorite).filter(
        Favorite.user_id == user.id, Favorite.listing_id == listing_id
    ).delete()
    db.commit()
    return Response(status_code=204)


@router.get("")
def list_favorites(
    user=Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
    db: OrmSession = Depends(get_db),
):
    query = (
        select(Listing)
        .join(Favorite, Favorite.listing_id == Listing.id)
        .where(Favorite.user_id == user.id)
        .order_by(Favorite.created_at.desc())
    )
    items, total = paginate(db, query, page, limit)
    return {
        "items": [listing_public(i, True) for i in items],
        "total": total,
        "page": page,
        "limit": limit,
    }
