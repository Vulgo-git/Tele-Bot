import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from .database import get_user_data

TOKEN = os.getenv("TELEGRAM_TOKEN")
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_html(
        f"👋 Olá {user.mention_html()}!\n"
        "Use /consulta <CPF> para buscar dados\n"
        "💳 Acesse nosso painel: https://seusite.com/assinatura"
    )

async def consulta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Verificação básica de pagamento (simplificado)
    if not user_paid(update.effective_user.id):  # Implementar lógica de pagamento
        await update.message.reply_text("❌ Acesso bloqueado. Faça o pagamento primeiro!")
        return
        
    cpf = context.args[0] if context.args else None
    if not cpf or len(cpf) != 11:
        await update.message.reply_text("❌ CPF inválido. Envie /consulta 12345678900")
        return
    
    try:
        dados = get_user_data(cpf)
        await update.message.reply_text(f"✅ Dados:\n{dados}") if dados else \
        await update.message.reply_text("❌ Nada encontrado")
    except Exception as e:
        logging.error(f"Erro: {e}")
        await update.message.reply_text("🔒 Erro temporário")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("consulta", consulta))
    app.run_polling()

if __name__ == "__main__":
    main()