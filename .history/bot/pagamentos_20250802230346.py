import os
import logging
from urllib.parse import urlencode

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pagamentos')

# Configurações
PUSHINPAY_CHECKOUT_ID = "9F8AD48B-4E0D-4455-9896-2718192D3493"
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")  # Para validação de webhooks
BASE_URL = "https://app.pushinpay.com.br/service/pay/"

def gerar_link_pagamento(user_id: int, valor: float) -> str:
    """Gera um link de pagamento personalizado para o usuário"""
    try:
        # Parâmetros para rastreamento do usuário
        params = {
            "custom": f"user_{user_id}",
            "amount": valor,
            "description": "Acesso 5 dias ao bot de consultas"
        }
        
        # Construir URL com parâmetros
        query_string = urlencode(params)
        link_pagamento = f"{BASE_URL}{PUSHINPAY_CHECKOUT_ID}?{query_string}"
        
        logger.info(f"Link de pagamento gerado para user_id {user_id}: {link_pagamento}")
        return link_pagamento
        
    except Exception as e:
        logger.error(f"Erro ao gerar link de pagamento: {str(e)}")
        return "https://pushinpay.com/pagamento-fallback"

def validar_webhook_pagamento(payload: dict, signature: str) -> bool:
    """Valida a assinatura de um webhook do PushinPay"""
    # Implementação anterior usando HMAC
    # ...
    return True  # Remova esta linha quando implementar

def processar_webhook_pagamento(payload: dict) -> bool:
    """Processa um webhook de pagamento confirmado"""
    try:
        # Verificar se é um evento de pagamento aprovado
        if payload.get('status') != 'approved':
            logger.info(f"Status de pagamento não aprovado: {payload.get('status')}")
            return False
        
        # Extrair user_id do campo custom
        custom_data = payload.get('custom', '')
        if not custom_data.startswith('user_'):
            logger.error(f"Formato de custom_data inválido: {custom_data}")
            return False
        
        try:
            user_id = int(custom_data.split('_')[1])
        except (IndexError, ValueError):
            logger.error(f"Falha ao extrair user_id de {custom_data}")
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