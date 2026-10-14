from datetime import datetime

from app.entities.User import UserType
from app.common.Result import Result

def create_user(db, user: UserType):
    exist = exist_user(db, user)

    if exist.succeeded: 
        return Result(exist.data["id"])
    
    if "role" not in user:
        user["role"] = "common"

    sql_string = '''
        insert into users(email, role, created_at)
            values(%s,%s,%s) returning id;
    '''

    user_id = None
    with db.transaction() as f:
        user_id = f.sql(sql_string, (user["email"], user["role"], datetime.today(),), callback=lambda x : x.fetchone())[0]
        
    return Result(user_id)

def exist_user(db, user: UserType):
    return get_user_by_email(db, user["email"])

def get_user_by_email(db, email):
    sql_string = '''
        select * from users
            where email = %s;
    '''
    with db.transaction() as f:
        res = f.sql_dict(sql_string, (email,), callback=lambda x : x.fetchone())

    return Result(res)