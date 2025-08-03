from fastapi import FastAPI, Request, HTTPException, Header
from bot.database import Database
from datetime import datetime, timedelta
import os
import logging
import hmac
import hashlib

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Inicializar banco de dados
db = Database()

# Configuração de segurança
PUSHINGPAY_SECRET = os.getenv("PUSHINGPAY_SECRET")

@app.post("/webhook/pagamento")
async def webhook_pagamento(
    request: Request,
    x_pushingpay_signature: str = Header(None)
):
    # Verificação de segurança
    if not PUSHINGPAY_SECRET:
        logger.error("PUSHINGPAY_SECRET não configurada!")
        raise HTTPException(status_code=500, detail="Configuração incompleta")
    
    # Obter payload
    payload_bytes = await request.body()
    payload = await request.json()
    
    # Validar assinatura
    signature = hmac.new(
        PUSHINGPAY_SECRET.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    if signature != x_pushingpay_signature:
        logger.warning(f"Assinatura inválida: {x_pushingpay_signature}")
        raise HTTPException(status_code=403, detail="Assinatura inválida")
    
    logger.info(f"Webhook recebido: {payload}")
    
    # Processar apenas pagamentos aprovados
    if payload.get("status") == "approved":
        try:
            # Extrair user_id da referência externa
            ref = payload["external_reference"]
            user_id = int(ref.split("_")[-1])
            
            # Liberar acesso por 5 dias
            expiry = datetime.now() + timedelta(days=5)
            db.grant_access(user_id, days=5)
            
            logger.info(f"Acesso liberado para user_id: {user_id}")
            return {
                "status": "success",
                "user_id": user_id,
                "expiry": expiry.isoformat()
            }
        
        except (KeyError, ValueError, IndexError) as e:
            logger.error(f"Erro ao processar payload: {e}")
            raise HTTPException(status_code=400, detail="Formato de payload inválido")
    
    return {"status": "ignored"}