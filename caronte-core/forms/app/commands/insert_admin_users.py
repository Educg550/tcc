from app.common.Result import Result
from app.entities.User import User
from app.services.user_service import create_user

from app.logger import Logger

def run(db, file):
    emails = file.read().split(",")
    for email in emails:
        email = email.strip()
        if not email:
            continue
        
        result = create_user(db, User({
            "email": email,
            "role": "administrator"
        }))

        if not result.succeeded:
            Logger.print.warning(f"Erro para criar usuário administrador: {email}")
            break

        Logger.print.info(f"Usuário administrador criado com sucesso: {email}")

    return Result(True)