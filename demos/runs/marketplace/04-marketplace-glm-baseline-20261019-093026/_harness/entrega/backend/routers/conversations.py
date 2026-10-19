from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from backend.deps import get_current_user, get_db
from backend.models import Conversation, Listing, Message, User
from backend.schemas import ConversationIn, MessageIn
from backend.serializers import conversation_public, message_public

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def get_conversation_or_403(conv_id: int, user: User, db: OrmSession) -> Conversation:
    conv = db.get(Conversation, conv_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    if user.id not in (conv.buyer_id, conv.seller_id):
        raise HTTPException(status_code=403, detail="Você não participa desta conversa")
    return conv


@router.post("", status_code=201)
def create_conversation(
    data: ConversationIn,
    user=Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    listing = db.get(Listing, data.listing_id)
    if listing is None or listing.status != "active":
        raise HTTPException(status_code=404, detail="Anúncio não encontrado")
    if listing.seller_id == user.id:
        raise HTTPException(status_code=400, detail="Não é possível conversar consigo mesmo")
    conv = db.execute(
        select(Conversation).where(
            Conversation.listing_id == listing.id, Conversation.buyer_id == user.id
        )
    ).scalar_one_or_none()
    if conv is None:
        conv = Conversation(
            listing_id=listing.id, buyer_id=user.id, seller_id=listing.seller_id
        )
        db.add(conv)
        db.commit()
    other = db.get(User, conv.seller_id if conv.buyer_id == user.id else conv.buyer_id)
    return conversation_public(conv, other)


@router.get("")
def list_conversations(user=Depends(get_current_user), db: OrmSession = Depends(get_db)):
    convs = (
        db.execute(
            select(Conversation)
            .where(
                (Conversation.buyer_id == user.id) | (Conversation.seller_id == user.id)
            )
            .order_by(Conversation.created_at.desc())
        )
        .scalars()
        .all()
    )
    result = []
    for conv in convs:
        other = db.get(
            User, conv.seller_id if conv.buyer_id == user.id else conv.buyer_id
        )
        result.append(conversation_public(conv, other))
    return result


@router.get("/{conv_id}/messages")
def list_messages(
    conv_id: int,
    user=Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    conv = get_conversation_or_403(conv_id, user, db)
    msgs = (
        db.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at.asc(), Message.id.asc())
        )
        .scalars()
        .all()
    )
    return [message_public(m) for m in msgs]


@router.post("/{conv_id}/messages", status_code=201)
def send_message(
    conv_id: int,
    data: MessageIn,
    user=Depends(get_current_user),
    db: OrmSession = Depends(get_db),
):
    conv = get_conversation_or_403(conv_id, user, db)
    msg = Message(conversation_id=conv.id, sender_id=user.id, content=data.content)
    db.add(msg)
    db.commit()
    return message_public(msg)
