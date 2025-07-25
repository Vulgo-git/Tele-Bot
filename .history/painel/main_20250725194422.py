from fastapi import FastAPI, Request
from bot.database import criar_acesso

app = FastAPI()

@app.post("/webhook/pagamento")
async def webhook_pagamento(request: Request):
    payload = await request.json()
    
    if payload["status"] == "approved":
        # Extrair user_id da referência externa
        ref = payload["external_reference"]
        user_id = int(ref.split("_")[1])
        
        # Liberar acesso por 24h
        criar_acesso(user_id)
    
    return {"status": "ok"}