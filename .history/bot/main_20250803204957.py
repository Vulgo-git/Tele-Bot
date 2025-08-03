import os
import logging
import atexit
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    CallbackContext
)
from bot.database import Database
from bot.pagamentos import gerar_link_pagamento

# Configuração básica
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configurações
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PUSHINGPAY_API_KEY = os.getenv("PUSHINGPAY_API_KEY")

# Inicializar banco de dados
db = Database()

# Função para fechar conexões ao sair
def close_db():
    try:
        db.close_connection()
        logger.info("Conexões do banco de dados fechadas com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao fechar conexões do banco: {e}")

# Registrar função de fechamento para execução ao sair
atexit.register(close_db)

# ===== FUNÇÕES PRINCIPAIS =====
def start(update: Update, context: CallbackContext) -> None:
    try:
        user = update.effective_user
        if not user:
            logger.warning("Usuário não encontrado na atualização")
            return
            
        logger.info(f"Usuário {user.id} iniciou o bot")
        
        keyboard = [
            [InlineKeyboardButton("🔍 Consultar CPF", callback_data='consult_cpf')],
            [InlineKeyboardButton("🚗 Consultar Placa", callback_data='consult_plate')],
            [InlineKeyboardButton("💰 Liberar Acesso (5 Dias)", callback_data='buy_access')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        first_name = user.first_name or "usuário"
        update.message.reply_text(
            f"👋 Olá {first_name}! Bem-vindo ao Consultas Pro.\n\n"
            "🔓 Tenha acesso a consultas completas com apenas R$15 para 5 dias de uso ilimitado!\n\n"
            "Selecione uma opção abaixo:",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Erro no /start: {e}", exc_info=True)

def button_handler(update: Update, context: CallbackContext) -> None:
    try:
        query = update.callback_query
        if not query:
            logger.warning("CallbackQuery não encontrado")
            return
            
        user = query.from_user
        if not user:
            logger.warning("Usuário não encontrado no CallbackQuery")
            return
            
        query.answer()
        
        if query.data == 'buy_access':
            try:
                # Gerar link de pagamento usando o módulo de pagamentos
                link = gerar_link_pagamento(user.id)
                text = (
                    "💰 *LIBERAR ACESSO POR 5 DIAS*\n\n"
                    "Valor: R$15,00\n\n"
                    f"👉 [Clique aqui para pagar]({link})\n\n"
                    "Após o pagamento, envie o comprovante neste chat."
                )
                context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=text,
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
            except Exception as e:
                logger.error(f"Erro ao gerar link de pagamento: {e}", exc_info=True)
                context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="⚠️ Erro ao gerar link de pagamento. Tente novamente mais tarde."
                )
            return
        
        # Verificar acesso no banco de dados
        if not db.has_access(user.id):
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
        
        elif query.data == 'consult_plate':
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text="🚗 Digite a placa do veículo (formato ABC1234 ou ABC1D23):"
            )
            context.user_data['waiting_for'] = 'plate'
    
    except Exception as e:
        logger.error(f"Erro no button_handler: {e}", exc_info=True)

def message_handler(update: Update, context: CallbackContext) -> None:
    try:
        user = update.message.from_user
        if not user:
            logger.warning("Usuário não encontrado na mensagem")
            return
            
        text = update.message.text
        if not text:
            return
        
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
        
        elif context.user_data['waiting_for'] == 'plate':
            if len(text) < 6 or len(text) > 7:
                update.message.reply_text("⚠️ Placa inválida! Formato: ABC1234 ou ABC1D23")
                return
            
            # Simulação de consulta
            result = (
                "🚗 *Resultado da Consulta de Placa:*\n\n"
                f"Placa: `{text}`\n"
                "Marca: Ford\n"
                "Modelo: Fiesta\n"
                "Ano: 2018\n"
                "Cor: Prata\n\n"
                "📝 *Consulta realizada em*: " + datetime.now().strftime("%d/%m/%Y %H:%M")
            )
            update.message.reply_text(result, parse_mode="Markdown")
            del context.user_data['waiting_for']
    
    except Exception as e:
        logger.error(f"Erro no message_handler: {e}", exc_info=True)

def activate_command(update: Update, context: CallbackContext) -> None:
    """Comando de admin para ativar acesso"""
    try:
        user = update.effective_user
        if not user or not update.message:
            logger.warning("Atualização inválida no activate_command")
            return
            
        # Substitua 123456789 pelo seu user_id de admin
        ADMIN_ID = 123456789
        if user.id != ADMIN_ID:
            update.message.reply_text("❌ Acesso negado!")
            return
        
        # Verificar argumentos
        if not context.args or len(context.args) < 1:
            update.message.reply_text("❌ Uso: /ativar <user_id>")
            return
            
        try:
            target_user_id = int(context.args[0])
            expiry = db.grant_access(target_user_id)
            update.message.reply_text(
                f"✅ Acesso ativado para {target_user_id}\n"
                f"Validade: {expiry.strftime('%d/%m/%Y %H:%M')}"
            )
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
    if not PUSHINGPAY_API_KEY:
        logger.error("Variável PUSHINGPAY_API_KEY não configurada!")
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
    finally:
        # Fechar conexões do banco de dados ao finalizar
        try:
            close_db()
        except Exception as e:
            logger.error(f"Erro ao fechar banco de dados: {e}")

if __name__ == '__main__':
    main()