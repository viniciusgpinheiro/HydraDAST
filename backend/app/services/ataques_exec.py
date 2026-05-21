import os
import random
from typing import Iterable, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests

BASE_DIR = os.path.dirname(__file__)
ARSENAL_DIR = os.path.abspath(os.path.join(BASE_DIR, "../data/arsenal_final"))

# Mapeamento de categorias para arquivos do arsenal_final
ATTACK_CATEGORY_FILES: Dict[str, List[str]] = {
    "sql_injection": ["SQL_Injection_Master.txt"],
    "xss": ["XSS_Master.txt"],
    "template_injection": ["Template_Injection_Master.txt"],
    "command_injection": ["Command_Injection_Master.txt"],
    "lfi_path_traversal": ["LFI_PathTraversal_Master.txt"],
    "nosql_injection": ["NoSQL_Master.txt"],
    "xxe": ["XXE-Fuzzing.txt", "XML-FUZZ.txt"],
    "ssi": ["SSI-Injection-Jhaddix.txt"],
    "login_bypass": ["login_bypass.txt"],
    "polyglot": ["Polyglots.txt"],
    "generic_fuzz": ["big-list-of-naughty-strings.txt"],
}

# Mapeamento do tipo de campo (classificação do NLP) para categorias de ataque
CLASSIFICATION_TO_CATEGORIES: Dict[str, List[str]] = {
    "credencial_senha": ["login_bypass", "sql_injection"],
    "credencial_identificador": ["login_bypass", "sql_injection"],
    "busca_pesquisa": ["sql_injection", "xss"],
    "contato_mensagem": ["xss", "template_injection"],
    "segredo_api": ["nosql_injection", "sql_injection"],
    "identificador_oculto": ["sql_injection", "generic_fuzz"],
    "campo_generico": ["generic_fuzz", "xss"],
}

_payload_cache: Dict[str, List[str]] = {}


def _read_payloads_from_file(file_name: str) -> List[str]:
    if file_name in _payload_cache:
        return _payload_cache[file_name]

    file_path = os.path.join(ARSENAL_DIR, file_name)
    if not os.path.exists(file_path):
        _payload_cache[file_name] = []
        return []

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        payloads = [line.strip() for line in f.readlines() if line.strip()]

    _payload_cache[file_name] = payloads
    return payloads


def load_payloads_by_category(category: str) -> List[str]:
    files = ATTACK_CATEGORY_FILES.get(category, [])
    payloads: List[str] = []
    for file_name in files:
        payloads.extend(_read_payloads_from_file(file_name))
    return payloads


def pick_payloads_for_classification(
    classification: str,
    max_payloads: int = 30,
    seed: Optional[int] = None,
) -> Dict[str, List[str]]:
    categories = CLASSIFICATION_TO_CATEGORIES.get(classification, ["generic_fuzz"])
    rng = random.Random(seed)
    selection: Dict[str, List[str]] = {}

    for category in categories:
        payloads = load_payloads_by_category(category)
        if not payloads:
            selection[category] = []
            continue
        if len(payloads) <= max_payloads:
            selection[category] = payloads
        else:
            selection[category] = rng.sample(payloads, max_payloads)

    return selection


def build_attack_plan(
    target_url: str,
    form_action: str,
    form_method: str,
    parameter: str,
    classification: str,
    max_payloads: int = 30,
    seed: Optional[int] = None,
) -> Dict[str, Iterable[str]]:
    endpoint = urljoin(target_url, form_action or target_url)
    payloads_by_category = pick_payloads_for_classification(
        classification=classification,
        max_payloads=max_payloads,
        seed=seed,
    )
    return {
        "endpoint": endpoint,
        "method": (form_method or "GET").upper(),
        "parameter": parameter,
        "payloads_by_category": payloads_by_category,
    }


def _is_target_allowed(target_url: str, allowlist: Iterable[str]) -> bool:
    parsed = urlparse(target_url)
    hostname = parsed.hostname or ""
    return hostname in set(allowlist)


def execute_plan(
    plan: Dict[str, Iterable[str]],
    allowlist_domains: Iterable[str],
    timeout: int = 8,
    dry_run: bool = True,
    headers: Optional[Dict[str, str]] = None,
) -> List[Dict[str, str]]:
    if not _is_target_allowed(plan["endpoint"], allowlist_domains):
        raise RuntimeError("Alvo não está na allowlist. Abortando execução.")

    results = []
    request_headers = {"User-Agent": "HydraDAST-Project-Agent"}
    if headers:
        request_headers.update(headers)

    method = plan["method"]
    parameter = plan["parameter"]

    def _build_request_payload(category: str, payload: str) -> Dict[str, Dict[str, str]]:
        if category == "xss":
            # Para XSS refletido em headers, injeta no header (ex: User-Agent)
            injected_headers = dict(request_headers)
            injected_headers["X-HydraDAST-XSS"] = payload
            return {"headers": injected_headers, "params": {}, "data": {}}

        # Padrão: payload vai no parâmetro do input (query/body)
        return {"headers": request_headers, "params": {parameter: payload}, "data": {parameter: payload}}

    for category, payloads in plan["payloads_by_category"].items():
        for payload in payloads:
            if dry_run:
                results.append({
                    "category": category,
                    "payload": payload,
                    "status": "DRY_RUN",
                })
                continue

            try:
                req = _build_request_payload(category, payload)
                if method == "GET":
                    response = requests.get(
                        plan["endpoint"],
                        params=req["params"],
                        headers=req["headers"],
                        timeout=timeout,
                    )
                else:
                    response = requests.post(
                        plan["endpoint"],
                        data=req["data"],
                        headers=req["headers"],
                        timeout=timeout,
                    )

                results.append({
                    "category": category,
                    "payload": payload,
                    "status": str(response.status_code),
                })
            except Exception as exc:
                results.append({
                    "category": category,
                    "payload": payload,
                    "status": f"ERROR: {exc}",
                })

    return results


__all__ = [
    "load_payloads_by_category",
    "pick_payloads_for_classification",
    "build_attack_plan",
    "execute_plan",
]
