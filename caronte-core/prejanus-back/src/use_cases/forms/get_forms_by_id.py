from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

async def get_forms_by_id(session_forms: AsyncSession, recommenders_form_id: str):
    query = text("""
        select * from get_all_submissions(
            cast(:p_form_id as int),
            cast(:p_order_by as int),
            cast(:p_order_type as int),
            cast(:p_search as text),
            cast(:p_lang as text)
        )
    """)
    params = {
        "p_form_id": int(recommenders_form_id),
        "p_order_by": 1,
        "p_order_type": 0,
        "p_search": "",
        "p_lang": "pt" 
    }
    result = await session_forms.execute(
        query,
        params
    )
    return [dict(row._mapping) for row in result.fetchall()]