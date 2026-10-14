import json
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class FormSchema(BaseModel):
    id: int
    title: str
    created_at: str
    created_by: str
    tags: dict
    phase: str

async def get_forms_by_tag(session_forms: AsyncSession, tag_filter) -> list[FormSchema]:
    query = text("""
        select * from get_all_user_forms(
            cast(:p_user_id as int),
            cast(:p_order_by as int),
            cast(:p_order_type as int),
            cast(:p_tag_filter as jsonb),
            cast(:p_search as text),
            cast(:p_lang as text),
            cast(:is_admin as boolean)
        )
    """)
    
    params = {
        "p_user_id": None,
        "p_order_by": 1,
        "p_order_type": 0,
        "p_tag_filter": json.dumps(tag_filter or {}),
        "p_search": "",
        "p_lang": "pt",
        "is_admin": True
    }

    result = await session_forms.execute(
        query,
        params
    )

    forms = [dict(row._mapping) for row in result.fetchall()]
    return forms
