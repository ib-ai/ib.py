from dotenv import load_dotenv

# Load environment variables before anything else.
load_dotenv()

from .bot import main

if __name__ == "__main__":
    main()
