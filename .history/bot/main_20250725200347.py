import os
from typing import cast
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv
from bot.pagamentos import gerar_link_pagamento
from bot.database import verificar_acesso

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Verificação segura para evitar None
    if not update.message or not update.message.from_user:
        return
    
    user = update.message.from_user
    keyboard = [
        [InlineKeyboardButton("🔍 Consultar CPF", callback_data='cpf')],
        [InlineKeyboardButton("🏢 Consultar CNPJ", callback_data='cnpj')],
        [InlineKeyboardButton("🚗 Consultar Placa", callback_data='placa')],
        [InlineKeyboardButton("💰 Liberar Acesso 24h (R$13)", callback_data='pagamento')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Garantia de que first_name existe
    nome = user.first_name or "usuário"
    
    await update.message.reply_text(
        f"👋 Olá {nome}!\n\n"
        "🔓 Tenha acesso a consultas completas de:\n"
        "- CPF\n- Nome\n- Telefone\n- CNPJ\n- Placa de veículo\n\n"
        "💵 Apenas R$13 para 24h de acesso ilimitado!",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Verificação segura para CallbackQuery
    query = update.callback_query
    if not query or not query.data or not query.from_user:
        return
    
    # Cast para tipo conhecido
    safe_query = cast(CallbackQuery, query)
    user_id = safe_query.from_user.id
    
    if safe_query.data == 'pagamento':
        link = gerar_link_pagamento(user_id, 13.00)
        
        # Verificação segura para message
        if safe_query.message:
            msg = cast(Message, safe_query.message)
            await msg.reply_text(
                "💰 *LIBERAR ACESSO 24H*\n\n"
                "Valor: R$13,00\n"
                "Clique no link abaixo para pagar:\n"
                f"{link}\n\n"
                "Após o pagamento, seu acesso será liberado automaticamente!",
                parse_mode="Markdown"
            )
        return
    
    # Verificar acesso pago
    if not verificar_acesso(user_id):
        await safe_query.answer("⛔ Acesso bloqueado! Libere seu acesso por 24h.", show_alert=True)
        return
    
    # Redirecionar para consultas
    if safe_query.data == 'cpf':
        if safe_query.message:
            msg = cast(Message, safe_query.message)
            await msg.reply_text("Digite o CPF para consulta (somente números):")
            context.user_data['consulta_tipo'] = 'cpf'
    # ... outros tipos de consulta

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()