from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from backend.deps import get_current_user, get_db
from backend.models import Listing, Order, Review, User
from backend.routers.listings import paginate
from backend.schemas import OrderIn, ReviewIn, StatusIn
from backend.serializers import order_public, review_public

router = APIRouter(prefix="/api", tags=["orders"])

# (de, para) -> quem pode executar: "seller" ou "buyer"
TRANSITIONS = {
    ("pending", "confirmed"): "seller",
    ("confirmed", "shipped"): "seller",
    ("shipped", "delivered"): "buyer",
    ("pending", "cancelled"): "buyer",
    ("confirmed", "cancelled"): "buyer",
}


@router.post("/orders", status_code=201)
def create_order(
    data: OrderIn,
    user=Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    listing = db.execute(
        select(Listing).where(Listing.id == data.listing_id).with_for_update()
    ).scalar_one_or_none()
    if listing is None or listing.status != "active":
        raise HTTPException(status_code=409, detail="Anúncio indisponível")
    if listing.seller_id == user.id:
        raise HTTPException(status_code=400, detail="Não é possível comprar o próprio anúncio")
    if listing.stock < data.quantity:
        raise HTTPException(status_code=409, detail="Estoque insuficiente")
    listing.stock -= data.quantity
    order = Order(
        listing_id=listing.id,
        buyer_id=user.id,
        seller_id=listing.seller_id,
        quantity=data.quantity,
        unit_price_cents=listing.price_cents,
        total_cents=listing.price_cents * data.quantity,
        address=data.address.strip(),
    )
    db.add(order)
    db.commit()
    return order_public(order)


@router.get("/me/orders")
def my_orders(
    role: str = "buyer",
    user=Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
    db: OrmSession = Depends(get_db),
):
    if role not in ("buyer", "seller"):
        raise HTTPException(status_code=422, detail="role inválido")
    column = Order.buyer_id if role == "buyer" else Order.seller_id
    query = (
        select(Order)
        .where(column == user.id)
        .order_by(Order.created_at.desc(), Order.id.desc())
    )
    items, total = paginate(db, query, page, limit)
    return {
        "items": [order_public(i) for i in items],
        "total": total,
        "page": page,
        "limit": limit,
    }


def get_order_or_403(order_id: int, user: User, db: OrmSession) -> Order:
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if user.id not in (order.buyer_id, order.seller_id):
        raise HTTPException(status_code=403, detail="Você não participa deste pedido")
    return order


@router.get("/orders/{order_id}")
def get_order(
    order_id: int,
    user=Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    return order_public(get_order_or_403(order_id, user, db))


@router.patch("/orders/{order_id}/status")
def update_status(
    order_id: int,
    data: StatusIn,
    user=Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    order = db.execute(
        select(Order).where(Order.id == order_id).with_for_update()
    ).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    if user.id not in (order.buyer_id, order.seller_id):
        raise HTTPException(status_code=403, detail="Você não participa deste pedido")
    allowed_role = TRANSITIONS.get((order.status, data.status))
    if allowed_role is None:
        raise HTTPException(status_code=409, detail="Transição de status inválida")
    actual_role = "seller" if user.id == order.seller_id else "buyer"
    if actual_role != allowed_role:
        raise HTTPException(status_code=403, detail="Você não pode fazer esta transição")
    if data.status == "cancelled":
        listing = db.execute(
            select(Listing).where(Listing.id == order.listing_id).with_for_update()
        ).scalar_one()
        listing.stock += order.quantity
    order.status = data.status
    db.commit()
    return order_public(order)


@router.post("/orders/{order_id}/review", status_code=201)
def create_review(
    order_id: int,
    data: ReviewIn,
    user=Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    order = get_order_or_403(order_id, user, db)
    if order.buyer_id != user.id:
        raise HTTPException(status_code=403, detail="Somente o comprador pode avaliar")
    if order.status != "delivered":
        raise HTTPException(status_code=409, detail="Somente pedidos entregues podem ser avaliados")
    exists = db.execute(
        select(Review).where(Review.order_id == order.id)
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="Pedido já avaliado")
    review = Review(
        order_id=order.id,
        listing_id=order.listing_id,
        buyer_id=user.id,
        rating=data.rating,
        comment=data.comment.strip(),
    )
    db.add(review)
    db.commit()
    return review_public(review, user.name)
