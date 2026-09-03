"""Rotas HTTP para disparar e consultar scans.

POST /api/scans        -> inicia um scan em background e devolve o id (status "running")
GET  /api/scans        -> lista os scans executados nesta sessão
GET  /api/scans/{id}   -> devolve o estado/relatório atual de um scan (para polling)
"""

import threading
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.scan_runner import executar_scan, _normalizar_url
from api.routes.config import _CONFIG

router = APIRouter(prefix="/api/scans", tags=["scans"])

# Armazenamento em memória (suficiente para a demo; troca por BD depois).
_SCANS: dict[str, dict] = {}
_LOCK = threading.Lock()


class ScanRequest(BaseModel):
    url: str
    linguagem: Optional[str] = None
    login: Optional[str] = None
    senha: Optional[str] = None
    motores: Optional[list[str]] = None


def _rodar_em_background(scan_id: str, url: str, motores: Optional[list[str]], limite_requisicoes: int):
    def _on_progress(snapshot: dict):
        with _LOCK:
            _SCANS[scan_id] = snapshot

    try:
        final = executar_scan(
            url=url, motores=motores, on_progress=_on_progress, scan_id=scan_id,
            limite_requisicoes=limite_requisicoes,
        )
        with _LOCK:
            _SCANS[scan_id] = final
    except Exception as e:  # noqa: BLE001 - queremos registrar qualquer falha no estado
        with _LOCK:
            atual = _SCANS.get(scan_id, {})
            atual["status"] = "error"
            atual["erro"] = str(e)
            _SCANS[scan_id] = atual


@router.post("")
def criar_scan(req: ScanRequest):
    if not req.url or not req.url.strip():
        raise HTTPException(status_code=400, detail="URL é obrigatória.")

    try:
        url = _normalizar_url(req.url.strip())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    scan_id = str(uuid.uuid4())
    # Estado inicial imediato, antes de qualquer etapa concluir.
    with _LOCK:
        _SCANS[scan_id] = {
            "id": scan_id,
            "url": url,
            "criadoEm": datetime.now().isoformat(timespec="seconds"),
            "status": "running",
            "etapas": [],
            "resumo": {"url": url, "total": 0, "nivel": "—",
                       "criticas": 0, "altas": 0, "medias": 0, "baixas": 0},
            "acuraciaBars": [],
            "vulnerabilidades": [],
        }

    # Item 2: usa o limite de requisições escolhido pelo usuário em
    # Configurações no momento da criação do teste (snapshot, não afetado
    # por uma mudança posterior na configuração global).
    limite_requisicoes = _CONFIG.get("limiteRequisicoes", 100)

    thread = threading.Thread(
        target=_rodar_em_background, args=(scan_id, url, req.motores, limite_requisicoes), daemon=True
    )
    thread.start()

    return _SCANS[scan_id]


def _risco_de(resumo: dict) -> str:
    if resumo.get("criticas"):
        return "Crítico"
    if resumo.get("altas"):
        return "Alto"
    if resumo.get("medias"):
        return "Médio"
    return "Baixo"


@router.get("")
def listar_scans():
    with _LOCK:
        itens = [
            {
                "id": s["id"],
                "url": s["url"],
                "criadoEm": s["criadoEm"],
                "status": s.get("status", "done"),
                "nivel": s["resumo"]["nivel"],
                "risco": _risco_de(s["resumo"]),
                "total": s["resumo"]["total"],
                "criticas": s["resumo"].get("criticas", 0),
                "altas": s["resumo"].get("altas", 0),
                "medias": s["resumo"].get("medias", 0),
                "baixas": s["resumo"].get("baixas", 0),
            }
            for s in _SCANS.values()
        ]
    # Mais recentes primeiro.
    itens.sort(key=lambda x: x["criadoEm"], reverse=True)
    return itens


@router.get("/{scan_id}")
def obter_scan(scan_id: str):
    with _LOCK:
        relatorio = _SCANS.get(scan_id)
    if not relatorio:
        raise HTTPException(status_code=404, detail="Scan não encontrado.")
    return relatorio
