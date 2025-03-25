from dotenv import load_dotenv
from src.bot import create_bot_application

def main() -> None:
    """Load environment and start the bot."""

    load_dotenv()
    application = create_bot_application()
    application.run_polling()

if __name__ == '__main__':
    main()
