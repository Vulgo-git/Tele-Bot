import requests
import os

PUSHINGPAY_API_KEY = os.getenv("PUSHINGPAY_API_KEY")

def gerar_link_pagamento(user_id: int, valor: float = 15.00) -> str:
    """Gera link de pagamento na PushingPay"""
    response = requests.post(
        "https://api.pushingpay.com/payment_links",
        headers={"Authorization": f"Bearer {PUSHINGPAY_API_KEY}"},
        json={
            "amount": valor,
            "reference": f"BOT_ACCESS_{user_id}",
            "customer_name": f"Cliente {user_id}",
            "notification_url": "https://seubot.com/webhook/pushingpay"
        }
    )
    if response.status_code != 200:
        raise Exception(f"Erro PushingPay: {response.text}")
    return response.json()["payment_url"]