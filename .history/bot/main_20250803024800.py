import os
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    CallbackContext
)

# Configuração básica
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configurações
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PUSHINGPAY_LINK = os.getenv("PUSHINGPAY_LINK")

# Dicionário para armazenar acessos
USER_ACCESS = {}

# ===== FUNÇÕES PRINCIPAIS =====
def start(update: Update, context: CallbackContext) -> None:
    """Handler para o comando /start"""
    try:
        # Correção 1: Verificação segura do usuário
        user = update.effective_user
        if not user:
            logger.error("Usuário não encontrado na atualização")
            return
            
        logger.info(f"Usuário {user.id} iniciou o bot")
        
        keyboard = [
            [InlineKeyboardButton("🔍 Consultar CPF", callback_data='consult_cpf')],
            [InlineKeyboardButton("🚗 Consultar Placa", callback_data='consult_plate')],
            [InlineKeyboardButton("💰 Liberar Acesso (5 Dias)", callback_data='buy_access')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Correção 2: Verificação segura do first_name
        first_name = user.first_name or "usuário"
        update.message.reply_text(
            f"👋 Olá {first_name}! Bem-vindo ao Consultas Pro.\n\n"
            "🔓 Tenha acesso a consultas completas com apenas R$15 para 5 dias de uso ilimitado!\n\n"
            "Selecione uma opção abaixo:",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Erro no /start: {e}")

def button_handler(update: Update, context: CallbackContext) -> None:
    """Handler para botões inline"""
    try:
        query = update.callback_query
        if not query:
            return
            
        user = query.from_user
        if not user:
            return
            
        query.answer()
        
        # Compra de acesso
        if query.data == 'buy_access':
            payment_link = f"{PUSHINGPAY_LINK}?custom={user.id}"
            text = (
                "💰 *LIBERAR ACESSO POR 5 DIAS*\n\n"
                "Valor: R$15,00\n\n"
                "👉 [Clique aqui para pagar](" + payment_link + ")\n\n"
                "Após o pagamento, envie o comprovante neste chat."
            )
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text=text,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            return
        
        # Consultas (requerem acesso)
        if not has_access(user.id):
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text="⛔ *Acesso não liberado!* Clique em *💰 Liberar Acesso*.",
                parse_mode="Markdown"
            )
            return
        
        # Inicializar user_data se necessário
        if context.user_data is None:
            context.user_data = {}
        
        # Redirecionar para consultas
        if query.data == 'consult_cpf':
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text="🔢 Digite o CPF (11 dígitos, somente números):"
            )
            context.user_data['waiting_for'] = 'cpf'
    
    except Exception as e:
        logger.error(f"Erro no button_handler: {e}", exc_info=True)

def message_handler(update: Update, context: CallbackContext) -> None:
    """Lida com mensagens textuais"""
    try:
        user = update.message.from_user
        if not user or not update.message.text:
            return
            
        text = update.message.text
        
        # Processar comprovantes
        if "comprovante" in text.lower() or "pagamento" in text.lower():
            update.message.reply_text(
                "✅ Comprovante recebido! Estamos verificando...\n"
                "Seu acesso será ativado em até 10 minutos."
            )
            return
        
        # Inicializar user_data se necessário
        if context.user_data is None:
            context.user_data = {}
        
        # Verificar se está aguardando consulta
        if 'waiting_for' not in context.user_data:
            update.message.reply_text("❌ Comando não reconhecido. Use /start para ver as opções.")
            return
        
        # Processar consultas
        if context.user_data['waiting_for'] == 'cpf':
            if len(text) != 11 or not text.isdigit():
                update.message.reply_text("⚠️ CPF inválido! Digite 11 números.")
                return
            
            # Simulação de consulta
            result = (
                "🔍 *Resultado da Consulta CPF:*\n\n"
                f"CPF: `{text}`\n"
                "Nome: João Silva\n"
                "Nascimento: 15/07/1985\n"
                "Mãe: Maria Silva\n"
                "Situação: Regular\n\n"
                "📝 *Consulta realizada em*: " + datetime.now().strftime("%d/%m/%Y %H:%M")
            )
            update.message.reply_text(result, parse_mode="Markdown")
            del context.user_data['waiting_for']
    
    except Exception as e:
        logger.error(f"Erro no message_handler: {e}", exc_info=True)

def grant_access(user_id: int, days: int = 5) -> None:
    """Concede acesso ao usuário"""
    expiry = datetime.now() + timedelta(days=days)
    USER_ACCESS[user_id] = expiry
    logger.info(f"Acesso concedido para {user_id} até {expiry}")

def has_access(user_id: int) -> bool:
    """Verifica se o usuário tem acesso ativo"""
    if user_id not in USER_ACCESS:
        return False
    return USER_ACCESS[user_id] > datetime.now()

def activate_command(update: Update, context: CallbackContext) -> None:
    """Comando de admin para ativar acesso"""
    try:
        user = update.effective_user
        if not user or not update.message:
            return
            
        # Substitua 123456789 pelo seu user_id
        if user.id != 123456789:  # Seu user_id de admin
            update.message.reply_text("❌ Acesso negado!")
            return
        
        # Correção 3: Verificação segura de context.args
        if not context.args or len(context.args) < 1:
            update.message.reply_text("❌ Uso: /ativar <user_id>")
            return
            
        try:
            target_user_id = int(context.args[0])
            grant_access(target_user_id)
            update.message.reply_text(f"✅ Acesso ativado para {target_user_id}")
        except ValueError:
            update.message.reply_text("❌ O user_id deve ser um número inteiro.")
    except Exception as e:
        logger.error(f"Erro no activate_command: {e}", exc_info=True)

# ===== CONFIGURAÇÃO E INICIALIZAÇÃO =====
def main() -> None:
    """Inicia o bot"""
    if not TELEGRAM_TOKEN:
        logger.error("Variável TELEGRAM_TOKEN não configurada!")
        return
    if not PUSHINGPAY_LINK:
        logger.error("Variável PUSHINGPAY_LINK não configurada!")
        return
    
    try:
        # Criação segura do Updater
        updater = Updater(TELEGRAM_TOKEN)
        if updater is None:
            logger.error("Falha ao criar o Updater. Verifique o token.")
            return
            
        dispatcher = updater.dispatcher
        if dispatcher is None:
            logger.error("Falha ao obter o dispatcher.")
            return
        
        # Registro de handlers
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("ativar", activate_command))
        dispatcher.add_handler(CallbackQueryHandler(button_handler))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))

        # Iniciar o bot
        logger.info("Iniciando bot...")
        updater.start_polling()
        logger.info("🤖 Bot iniciado e aguardando comandos...")
        updater.idle()
        
    except Exception as e:
        logger.critical(f"ERRO FATAL: {e}", exc_info=True)

if __name__ == '__main__':
    main()