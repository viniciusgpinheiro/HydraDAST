from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
#python -m uvicorn api:app --reload

# Configuração do CORS
origins = [
    "http://localhost:3000", # Porta padrão do React
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permite todos os métodos (GET, POST, etc)
    allow_headers=["*"], # Permite todos os cabeçalhos
)

@app.get("/")
async def root():
    return {"mensagem": "Hello world!"}

@app.get("/api/dados")
async def get_dados():
    return {"mensagem": "Conectado com sucesso ao FastAPI!"}

    