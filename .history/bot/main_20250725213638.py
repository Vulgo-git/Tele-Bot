import os
import sys
import logging
import asyncio
import traceback
from typing import cast, Optional
from dotenv import load_dotenv

# Configuração inicial de logging - CRÍTICO PARA DIAGNÓSTICO
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout  # Garante logs no Railway/Docker
)
logger = logging.getLogger(__name__)

# ================== CARREGAMENTO DE VARIÁVEIS ==================
try:
    load_dotenv()  # Tenta carregar .env localmente
    logger.info("Variáveis de ambiente do .env carregadas")
except Exception as e:
    logger.warning(f"Não foi possível carregar .env: {e}")

# Obtenção robusta do token
TOKEN = os.getenv("TELEGRAM_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    logger.critical("ERRO FATAL: Token do Telegram não encontrado!")
    logger.critical("Verifique se a variável TELEGRAM_TOKEN está definida")
    logger.critical("No Railway: Settings → Variables → TELEGRAM_TOKEN")
    sys.exit(1)  # Encerra o programa imediatamente

logger.info(f"Token do Telegram carregado (inicia com: {TOKEN[:5]}...)")

# ================== IMPORTAÇÕES PRINCIPAIS ==================
try:
    from telegram import (
        Update,
        InlineKeyboardButton,
        InlineKeyboardMarkup,
        Message,
        CallbackQuery
    )
    from telegram.ext import (
        Application,
        CommandHandler,
        CallbackQueryHandler,
        ContextTypes,
        CallbackContext
    )
except ImportError as e:
    logger.critical(f"Falha ao importar bibliotecas: {e}")
    sys.exit(1)

# ================== IMPORTAÇÕES PERSONALIZADAS ==================
try:
    from bot.pagamentos import gerar_link_pagamento
    from bot.database import verificar_acesso
except ImportError as e:
    logger.error(f"Importação de módulos locais falhou: {e}")
    # Criar funções de fallback
    def gerar_link_pagamento(user_id: int, valor: float) -> str:
        logger.warning("Função gerar_link_pagamento não disponível - usando fallback")
        return "https://pagamento.com/erro"
    
    def verificar_acesso(user_id: int) -> bool:
        logger.warning("Função verificar_acesso não disponível - acesso bloqueado")
        return False

# ================== HANDLERS PRINCIPAIS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para o comando /start."""
    try:
        # Verificações de segurança
        if not update.message or not update.message.from_user:
            logger.warning("Update inválido recebido no /start")
            return
        
        user = update.message.from_user
        logger.info(f"Comando /start recebido de {user.id}")
        
        # Teclado de opções
        keyboard = [
            [InlineKeyboardButton("🔍 Consultar CPF", callback_data='cpf')],
            [InlineKeyboardButton("🏢 Consultar CNPJ", callback_data='cnpj')],
            [InlineKeyboardButton("🚗 Consultar Placa", callback_data='placa')],
            [InlineKeyboardButton("💰 Liberar Acesso 24h (R$13)", callback_data='pagamento')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Saudação personalizada
        nome = user.first_name or "usuário"
        response = (
            f"👋 Olá {nome}!\n\n"
            "🔓 Tenha acesso a consultas completas de:\n"
            "- CPF\n- Nome\n- Telefone\n- CNPJ\n- Placa de veículo\n\n"
            "💵 Apenas R$13 para 24h de acesso ilimitado!"
        )
        
        await update.message.reply_text(response, reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Erro no handler /start: {e}", exc_info=True)
        if update.message:
            await update.message.reply_text("⚠️ Ocorreu um erro ao processar seu comando.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para botões inline."""
    try:
        query = update.callback_query
        if not query or not query.data or not query.from_user:
            logger.warning("CallbackQuery inválido recebido")
            return
        
        safe_query = cast(CallbackQuery, query)
        user_id = safe_query.from_user.id
        logger.info(f"Callback recebido: {safe_query.data} de {user_id}")
        
        # Processar ação de pagamento
        if safe_query.data == 'pagamento':
            logger.info(f"Usuário {user_id} solicitou pagamento")
            link = gerar_link_pagamento(user_id, 13.00)
            
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
        
        # Verificar acesso antes de permitir consultas
        if not verificar_acesso(user_id):
            logger.info(f"Usuário {user_id} tentou acessar sem permissão")
            await safe_query.answer("⛔ Acesso bloqueado! Libere seu acesso por 24h.", show_alert=True)
            return
        
        # Redirecionar para consultas
        if safe_query.data == 'cpf':
            if safe_query.message:
                msg = cast(Message, safe_query.message)
                await msg.reply_text("Digite o CPF para consulta (somente números):")
                
                # Inicializar user_data se necessário
                if context.user_data is None:
                    context.user_data = {}
                context.user_data['consulta_tipo'] = 'cpf'
        
        # Adicione outros tipos de consulta aqui...
        
    except Exception as e:
        logger.error(f"Erro no button_handler: {e}", exc_info=True)
        if update.callback_query and update.callback_query.message:
            await update.callback_query.message.reply_text("⚠️ Ocorreu um erro ao processar sua solicitação.")

# ================== TRATAMENTO DE ERROS ==================
async def error_handler(update: object, context: CallbackContext) -> None:
    """Captura todos os erros não tratados."""
    try:
        logger.error("Exceção não tratada:", exc_info=context.error)
        
        # Tenta enviar uma mensagem de erro ao usuário
        if update and isinstance(update, Update):
            if update.effective_message:
                await update.effective_message.reply_text(
                    "⚠️ Ocorreu um erro inesperado. Tente novamente mais tarde."
                )
    except Exception as e:
        logger.critical(f"Falha no tratamento de erros: {e}")

# ================== INICIALIZAÇÃO ==================
async def post_init(application: Application) -> None:
    """Executa após a inicialização do bot."""
    try:
        # Resetar webhook para evitar conflitos
        await application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook resetado com sucesso")
        
        # Informações do bot
        me = await application.bot.get_me()
        logger.info(f"Bot iniciado: @{me.username} (ID: {me.id})")
    except Exception as e:
        logger.error(f"Erro no post_init: {e}", exc_info=True)

async def main() -> None:
    """Ponto de entrada principal com tratamento de erros robusto."""
    try:
        logger.info("Iniciando aplicação Telegram...")
        
        # Construir aplicação
        app = Application.builder() \
            .token(TOKEN) \
            .post_init(post_init) \
            .build()
        
        # Registrar handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_error_handler(error_handler)
        
        logger.info("Handlers registrados. Iniciando polling...")
        
        # Iniciar em modo polling
        await app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES)
        
        
    except Exception as e:
        logger.critical(f"FALHA CRÍTICA: {e}", exc_info=True)
        logger.info("Reiniciando em 10 segundos...")
        await asyncio.sleep(10)
        await main()  # Tentar reiniciar

if __name__ == "__main__":
    try:
        # Executar com reinício automático em caso de falha
        while True:
            try:
                asyncio.run(main())
            except KeyboardInterrupt:
                logger.info("Bot encerrado pelo usuário")
                break
            except Exception as e:
                logger.critical(f"Falha no loop principal: {e}")
                logger.info("Reiniciando em 5 segundos...")
                asyncio.run(asyncio.sleep(5))
    except Exception as e:
        logger.critical(f"FALHA IRRECUPERÁVEL: {e}")
        sys.exit(1)