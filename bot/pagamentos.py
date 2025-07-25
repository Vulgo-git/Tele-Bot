import requests
import os

PUSHINPAY_TOKEN = os.getenv("PUSHINPAY_TOKEN")

def gerar_link_pagamento(user_id, valor):
    url = "https://api.pushinpay.com/v1/payments"
    headers = {"Authorization": f"Bearer {PUSHINPAY_TOKEN}"}
    payload = {
        "amount": valor,
        "description": "Acesso 24h ao bot de consultas",
        "external_reference": f"user_{user_id}",
        "notification_url": "https://seubot.com/webhook/pagamento",
        "back_url": "https://t.me/seubot",
        "payment_methods": ["pix", "credit_card"]
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        return response.json()["payment_link"]
    return "https://pushinpay.com/pagamento-fallback"