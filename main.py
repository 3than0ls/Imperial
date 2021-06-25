from dotenv import load_dotenv

from client import Client
from firecord import firecord


def main():
    """now THIS is scripting :). god knows how many lines of codes and files and garbage, all leading up to this stupid 18 line file."""
    load_dotenv()

    client = Client()
    firecord.initialize_bot(client)
    client.start_bot()


if __name__ == "__main__":
    main()
