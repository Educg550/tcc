from argon2 import PasswordHasher
from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from backend.db import SessionLocal
from backend.models import Listing, User

DEMO_PASSWORD = "Marketplace123!"

SEED_LISTINGS = [
    # (title, description, price_cents, stock, category, condition, city)
    ("Bicicleta urbana", "Bicicleta urbana aro 26, quadro de alumínio, freios a vela revisados. Ideal para trajetos curtos na cidade.", 89000, 1, "outros", "usado", "São Paulo"),
    ("Notebook para estudos", "Notebook leve com SSD de 256 GB e 8 GB de RAM. Ótimo para aulas, textos e navegação.", 159900, 3, "eletronicos", "novo", "Campinas"),
    ("Estante de madeira", "Estante de madeira maciça com cinco prateleiras. Peça firme, desmontável para transporte.", 45000, 2, "casa", "usado", "São Paulo"),
    ("Fone de ouvido bluetooth", "Fone bluetooth com cancelamento de ruído e 20 horas de bateria. Acompanha estojo.", 24900, 5, "eletronicos", "novo", "Rio de Janeiro"),
    ("Cafeteira italiana", "Cafeteira italiana de alumínio para 6 xícaras. Pouco uso, sem amassados.", 7900, 4, "casa", "usado", "Belo Horizonte"),
    ("Box de livros de ficção", "Coleção com 8 romances de ficção científica em bom estado. Vendo o box completo.", 12000, 2, "livros", "usado", "Porto Alegre"),
    ("Jaqueta de couro", "Jaqueta de couro legítimo tamanho M. Cortesia de guarda-roupa renovado.", 39900, 1, "moda", "usado", "Curitiba"),
    ("Mesa de jantar", "Mesa de jantar para 6 pessoas em madeira demolição. Acabamento envernizado.", 120000, 1, "casa", "usado", "São Paulo"),
    ("Teclado mecânico", "Teclado mecânico compacto com switches vermelhos e cabo removível.", 34900, 6, "eletronicos", "novo", "Recife"),
    ("Tênis de corrida", "Tênis de corrida tamanho 41, amortecimento em bom estado. Cor azul.", 18900, 3, "moda", "usado", "Salvador"),
    ("Livro de receitas", "Livro de receitas regionais, capa dura, 300 páginas. Novo, sem anotações.", 8900, 10, "livros", "novo", "Fortaleza"),
    ("Ventilador de mesa", "Ventilador de mesa 40 cm, três velocidades, silencioso. Funciona perfeitamente.", 15900, 2, "outros", "usado", "Goiânia"),
    ("Monitor 24 polegadas", "Monitor Full HD de 24 polegadas, entrada HDMI. Sem riscos na tela.", 69900, 2, "eletronicos", "usado", "São Paulo"),
    ("Kit de panelas", "Kit com três panelas antiaderentes e frigideira. Uso moderado.", 27900, 3, "casa", "usado", "Campinas"),
]


def run() -> None:
    db: OrmSession = SessionLocal()
    try:
        count = db.execute(select(func.count()).select_from(User)).scalar_one()
        if count > 0:
            return
        hasher = PasswordHasher()
        password_hash = hasher.hash(DEMO_PASSWORD)
        ana = User(name="Ana", email="ana@example.test", password_hash=password_hash)
        bruno = User(name="Bruno", email="bruno@example.test", password_hash=password_hash)
        carla = User(name="Carla", email="carla@example.test", password_hash=password_hash)
        db.add_all([ana, bruno, carla])
        db.flush()
        for i, row in enumerate(SEED_LISTINGS):
            title, description, price, stock, category, condition, city = row
            db.add(
                Listing(
                    seller_id=ana.id if i % 2 == 0 else bruno.id,
                    title=title,
                    description=description,
                    price_cents=price,
                    stock=stock,
                    category=category,
                    condition=condition,
                    city=city,
                )
            )
        db.commit()
    finally:
        db.close()
