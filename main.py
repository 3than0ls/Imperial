from dotenv import load_dotenv

from client import Client
from firecord import firecord


def main():
    load_dotenv()

    client = Client()
    firecord.initialize_bot(client)
    client.start_bot()


if __name__ == "__main__":
    main()
