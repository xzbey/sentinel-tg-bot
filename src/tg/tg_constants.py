from telegram.ext import ConversationHandler
import logging

# logging.basicConfig(level=logging.INFO)
# logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

RADIUS, DATE, COMPOSITE = range(3)
END = ConversationHandler.END