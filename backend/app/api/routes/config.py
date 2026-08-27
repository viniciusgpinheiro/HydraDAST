"""Configurações da aplicação (em memória, por sessão).

GET /api/config   -> devolve as configurações atuais
PUT /api/config   -> atualiza as configurações
"""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/config", tags=["config"])

# Estado real (em memória). Substituir por persistência em BD numa etapa futura.
_CONFIG = {
    "chaveApi": "",
    "respostaLLM": "desativado",
    "limiteRequisicoes": 100,
}


class ConfigUpdate(BaseModel):
    chaveApi: Optional[str] = None
    respostaLLM: Optional[str] = None
    limiteRequisicoes: Optional[int] = None


@router.get("")
def obter_config():
    return _CONFIG


@router.put("")
def atualizar_config(update: ConfigUpdate):
    for campo, valor in update.model_dump(exclude_none=True).items():
        _CONFIG[campo] = valor
    return _CONFIG
