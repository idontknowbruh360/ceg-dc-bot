import asyncio
import logging
import uvicorn
from config import settings
from database import init_db
from bot import bot_instance
from web import app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cegbot_main")

async def run_web():
    config = uvicorn.Config(
        app=app,
        host=settings.HOST,
        port=settings.PORT,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

async def run_bot():
    token = settings.DISCORD_TOKEN.strip() if settings.DISCORD_TOKEN else ""
    if not token or token == "your_discord_bot_token_here":
        logger.warning("DISCORD_TOKEN is missing or default placeholder. Web Admin Panel is accessible, but Discord Bot will stay offline until token is updated.")
        return
    
    try:
        await bot_instance.start(token)
    except Exception as e:
        logger.error(f"Failed to start Discord Bot: {e}")

async def main():
    await init_db()
    print("\n" + "=" * 60)
    print(f" 🚀 CEGBot Web Admin Panel live on: http://localhost:{settings.PORT}")
    print("=" * 60 + "\n")
    
    await asyncio.gather(
        run_web(),
        run_bot(),
        return_exceptions=True
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCEGBot shutdown complete.")
