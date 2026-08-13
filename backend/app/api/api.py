from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.scans import router as scans_router
from api.routes.config import router as config_router

app = FastAPI(title="HydraDAST API")
# Rodar a partir de backend/app:  python -m uvicorn api.api:app --reload

# Configuração do CORS
origins = [
    "http://localhost:5173",  # Vite (dev padrão)
    "http://localhost:3000",  # CRA / porta alternativa
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, etc)
    allow_headers=["*"],  # Permite todos os cabeçalhos
)

app.include_router(scans_router)
app.include_router(config_router)


@app.get("/")
async def root():
    return {"mensagem": "Hello world!"}


@app.get("/api/dados")
async def get_dados():
    return {"mensagem": "Conectado com sucesso ao FastAPI!"}
