import requests
import os
import logging
from datetime import datetime
import hashlib
import hmac

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pagamentos')

# Configurações
PUSHINPAY_TOKEN = os.getenv("PUSHINPAY_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")  # Para validação de webhooks

def gerar_link_pagamento(user_id: int, valor: float) -> str:
    """Gera um link de pagamento para o usuário com descrição atualizada"""
    if not PUSHINPAY_TOKEN:
        logger.error("Token do PushinPay não configurado!")
        return "https://pagamento.com/erro-configuracao"
    
    url = "https://api.pushinpay.com/v1/payments"
    headers = {"Authorization": f"Bearer {PUSHINPAY_TOKEN}"}
    
    # Descrição atualizada para 5 dias
    payload = {
        "amount": valor,
        "description": "Acesso 5 dias ao bot de consultas",
        "external_reference": f"user_{user_id}",
        "notification_url": "https://seubot.com/webhook/pagamento",
        "back_url": "https://t.me/seubot",
        "payment_methods": ["pix", "credit_card"],
        "metadata": {
            "user_id": user_id,
            "plano": "5_dias",
            "valor": valor,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()  # Lança exceção para códigos 4xx/5xx
        
        if response.status_code == 201:
            data = response.json()
            logger.info(f"Link de pagamento gerado para user_id {user_id}: {data['payment_link']}")
            return data["payment_link"]
        
        logger.error(f"Resposta inesperada do PushinPay: {response.status_code} - {response.text}")
        return "https://pushinpay.com/pagamento-fallback"
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na comunicação com PushinPay: {str(e)}")
        return "https://pushinpay.com/pagamento-fallback"
    except KeyError:
        logger.error("Resposta do PushinPay não contém 'payment_link'")
        return "https://pushinpay.com/pagamento-fallback"

def validar_webhook_pagamento(payload: dict, signature: str) -> bool:
    """Valida a assinatura de um webhook do PushinPay"""
    if not WEBHOOK_SECRET:
        logger.warning("WEBHOOK_SECRET não configurado - validação desativada")
        return True
    
    try:
        # Calcular HMAC SHA256
        computed_signature = hmac.new(
            WEBHOOK_SECRET.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Comparar assinaturas
        return hmac.compare_digest(computed_signature, signature)
    
    except Exception as e:
        logger.error(f"Erro na validação do webhook: {str(e)}")
        return False

def processar_webhook_pagamento(payload: dict) -> bool:
    """Processa um webhook de pagamento confirmado"""
    try:
        # Verificar se é um evento de pagamento aprovado
        if payload.get('event') != 'payment_approved':
            logger.info(f"Evento ignorado: {payload.get('event')}")
            return False
        
        payment = payload.get('data', {})
        status = payment.get('status')
        external_ref = payment.get('external_reference', '')
        
        # Verificar se o pagamento foi aprovado
        if status != 'approved':
            logger.info(f"Pagamento não aprovado: status={status}")
            return False
        
        # Extrair user_id da referência externa
        if not external_ref.startswith('user_'):
            logger.error(f"Formato de external_reference inválido: {external_ref}")
            return False
        
        try:
            user_id = int(external_ref.split('_')[1])
        except (IndexError, ValueError):
            logger.error(f"Falha ao extrair user_id de {external_ref}")
            return False
        
        # Registrar o acesso (você precisará importar do database)
        from .database import criar_acesso
        if criar_acesso(user_id):
            logger.info(f"Acesso concedido para user_id {user_id}")
            return True
        
        logger.error(f"Falha ao criar acesso para user_id {user_id}")
        return False
    
    except Exception as e:
        logger.error(f"Erro no processamento do webhook: {str(e)}")
        return False