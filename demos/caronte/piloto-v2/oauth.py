"""Provedor de contrato OAuth 1.0; identidades e credenciais apenas sintéticas."""
import secrets
import string
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Request, Response
from oauthlib.oauth1 import RequestValidator, SignatureOnlyEndpoint

app = FastAPI()
KEY = "piloto-v2-consumer-key"
SECRET = "piloto-v2-consumer-secret"
PERFIS = {
    "admin": ("900001", "Admin Piloto", "admin.piloto@example.com"),
    "docente": ("900002", "Docente Piloto", "docente.piloto@example.com"),
    "outro": ("900003", "Outra Docente", "outra.piloto@example.com"),
    "secretaria": ("900004", "Secretaria Piloto", "secretaria.piloto@example.com"),
    "coordenador": ("900005", "Coordenador Piloto", "coordenador.piloto@example.com"),
    "estudante": ("900006", "Estudante Piloto", "estudante.piloto@example.com"),
    "novo": ("900007", "Novo Docente", "novo.piloto@example.com"),
    "negado": ("999999", "Fora da Whitelist", "negado.piloto@example.com"),
}
tokens = {}
nonces = set()
eventos = []


class Validador(RequestValidator):
    enforce_ssl = False  # Somente a rede privada Docker; a sessão do cliente usa HTTPS.
    safe_characters = set(string.ascii_letters + string.digits + "-")
    client_key_length = request_token_length = access_token_length = (1, 128)
    verifier_length = nonce_length = (1, 128)
    dummy_client = "cliente-invalido"

    def validate_client_key(self, client_key, request):
        return client_key == KEY

    def get_client_secret(self, client_key, request):
        return SECRET

    def get_access_token_secret(self, client_key, token, request):
        return tokens.get(token, {}).get("secret", "token-invalido")

    def validate_timestamp_and_nonce(self, client_key, timestamp, nonce, request):
        chave = (client_key, timestamp, nonce)
        if chave in nonces:
            return False
        nonces.add(chave)
        return True


endpoint = SignatureOnlyEndpoint(Validador())


async def autenticar(request):
    valido, oauth = endpoint.validate_request(
        str(request.url), http_method=request.method,
        body=(await request.body()).decode() or None, headers=dict(request.headers),
    )
    eventos.append({"rota": request.url.path, "assinatura_valida": valido})
    if not valido:
        raise HTTPException(401, "Assinatura OAuth inválida")
    return oauth


@app.post("/wsusuario/oauth/request_token")
async def request_token(request: Request):
    oauth = await autenticar(request)
    if oauth.resource_owner_key:
        raise HTTPException(401, "Request token não deve conter outro token")
    token = secrets.token_hex(32)
    tokens[token] = {"secret": secrets.token_hex(32), "tipo": "request"}
    return Response(urlencode({
        "oauth_token": token, "oauth_token_secret": tokens[token]["secret"],
        "oauth_callback_confirmed": "true",
    }), media_type="application/x-www-form-urlencoded")


@app.get("/wsusuario/oauth/authorize")
def authorize(oauth_token: str, perfil: str = "docente"):
    registro = tokens.get(oauth_token)
    if not registro or registro["tipo"] != "request" or perfil not in PERFIS:
        raise HTTPException(400, "Token ou perfil inexistente")
    registro.update(perfil=perfil, verifier=secrets.token_hex(16))
    return {"oauth_token": oauth_token, "oauth_verifier": registro["verifier"]}


@app.post("/wsusuario/oauth/access_token")
async def access_token(request: Request):
    oauth = await autenticar(request)
    registro = tokens.get(oauth.resource_owner_key)
    if (not registro or registro["tipo"] != "request"
            or not registro.get("verifier") or oauth.verifier != registro["verifier"]):
        raise HTTPException(401, "Verifier inválido")
    token = secrets.token_hex(32)
    tokens[token] = {"secret": secrets.token_hex(32), "tipo": "access",
                     "perfil": registro["perfil"]}
    registro["tipo"] = "consumido"
    return Response(urlencode({
        "oauth_token": token, "oauth_token_secret": tokens[token]["secret"],
    }), media_type="application/x-www-form-urlencoded")


@app.post("/wsusuario/oauth/usuariousp")
async def usuario(request: Request):
    oauth = await autenticar(request)
    registro = tokens.get(oauth.resource_owner_key)
    if not registro or registro["tipo"] != "access":
        raise HTTPException(401, "Access token inválido")
    nusp, nome, email = PERFIS[registro["perfil"]]
    return {"loginUsuario": nusp, "nomeUsuario": nome,
            "emailPrincipalUsuario": email, "vinculo": []}


@app.get("/eventos")
def listar_eventos():
    return eventos
