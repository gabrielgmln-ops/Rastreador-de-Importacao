# rastreador-importacao/backend/app/auth.py
# Login simples (fora do escopo: autenticação robusta).
# Um único usuário vindo do ambiente; token assinado com HMAC-SHA256 e prazo de validade.
import base64
import hashlib
import hmac
import time

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

_bearer = HTTPBearer(auto_error=False)


def _b64(dados: bytes) -> str:
    return base64.urlsafe_b64encode(dados).decode().rstrip("=")


def _assinar(carga: str) -> str:
    chave = get_settings().secret_key.encode()
    return _b64(hmac.new(chave, carga.encode(), hashlib.sha256).digest())


def credenciais_validas(usuario: str, senha: str) -> bool:
    s = get_settings()
    # compare_digest em ambos: tempo constante, não vaza qual campo errou
    ok_usuario = hmac.compare_digest(usuario.encode(), s.admin_user.encode())
    ok_senha = hmac.compare_digest(senha.encode(), s.admin_password.encode())
    return ok_usuario and ok_senha


def emitir_token(usuario: str, agora: float | None = None) -> str:
    expira = int((agora or time.time()) + get_settings().token_ttl_min * 60)
    carga = _b64(f"{usuario}:{expira}".encode())
    return f"{carga}.{_assinar(carga)}"


def validar_token(token: str, agora: float | None = None) -> str | None:
    """Devolve o usuário se o token é íntegro e não expirou; senão None."""
    try:
        carga, assinatura = token.split(".")
        if not hmac.compare_digest(assinatura, _assinar(carga)):
            return None
        bruto = base64.urlsafe_b64decode(carga + "=" * (-len(carga) % 4)).decode()
        usuario, expira = bruto.rsplit(":", 1)
        if int(expira) < (agora or time.time()):
            return None
        return usuario
    except (ValueError, UnicodeDecodeError):
        return None


def exige_usuario(cred: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> str:
    """Dependência: protege as rotas que exigem login."""
    usuario = validar_token(cred.credentials) if cred else None
    if not usuario:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "não autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario
