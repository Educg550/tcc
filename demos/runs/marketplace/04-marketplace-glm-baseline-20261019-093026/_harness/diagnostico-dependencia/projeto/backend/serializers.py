from datetime import datetime, timezone

from backend.models import Conversation, Listing, Message, Order, Review, User


def user_public(user: User) -> dict:
    return {"id": user.id, "name": user.name, "email": user.email}


def user_brief(user: User) -> dict:
    return {"id": user.id, "name": user.name}


def iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def listing_public(listing: Listing, is_favorite: bool = False) -> dict:
    return {
        "is_favorite": is_favorite,
        "id": listing.id,
        "title": listing.title,
        "description": listing.description,
        "price_cents": listing.price_cents,
        "stock": listing.stock,
        "category": listing.category,
        "condition": listing.condition,
        "city": listing.city,
        "image_url": listing.image_url,
        "status": listing.status,
        "seller": user_brief(listing.seller),
        "created_at": iso(listing.created_at),
    }


def conversation_public(conv: Conversation, other: User) -> dict:
    return {
        "id": conv.id,
        "listing_id": conv.listing_id,
        "listing_title": conv.listing.title,
        "buyer_id": conv.buyer_id,
        "seller_id": conv.seller_id,
        "other_user": user_brief(other),
        "created_at": iso(conv.created_at),
    }


def message_public(msg: Message) -> dict:
    return {
        "id": msg.id,
        "conversation_id": msg.conversation_id,
        "sender_id": msg.sender_id,
        "content": msg.content,
        "created_at": iso(msg.created_at),
    }


def order_public(order: Order) -> dict:
    return {
        "id": order.id,
        "listing_id": order.listing_id,
        "listing_title": order.listing.title,
        "buyer_id": order.buyer_id,
        "seller_id": order.seller_id,
        "buyer_name": order.buyer.name,
        "seller_name": order.seller.name,
        "quantity": order.quantity,
        "unit_price_cents": order.unit_price_cents,
        "total_cents": order.total_cents,
        "address": order.address,
        "status": order.status,
        "created_at": iso(order.created_at),
        "updated_at": iso(order.updated_at),
    }


def review_public(review: Review, buyer_name: str) -> dict:
    return {
        "id": review.id,
        "order_id": review.order_id,
        "listing_id": review.listing_id,
        "buyer_id": review.buyer_id,
        "buyer_name": buyer_name,
        "rating": review.rating,
        "comment": review.comment,
        "created_at": iso(review.created_at),
    }
