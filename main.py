import argparse
import asyncio
from utils import get_valid_date
from downloader import Downloader
from utils import get_filter
import os


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--date-from",
        type=get_valid_date,
        required=True,
        help="date from which download starts in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--date-to",
        type=get_valid_date,
        required=True,
        help="date until which download ends in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--filter", action="append", default=None, help="path to filter file(s)"
    )
    parser.add_argument(
        "--database", default="./download.sqlite", help="path to database file"
    )
    parser.add_argument("--server", type=int, required=True, help="server id")

    args = parser.parse_args()
    bot_token = os.environ["DISCORD_TOKEN"]

    if args.date_from >= args.date_to:
        parser.error("invalid date range: --date-from must be before --date-to")

    downloader = Downloader(bot_token, args.server, args.database)
    filters = get_filter(args.filter)
    asyncio.run(downloader.run(filters, args.date_from, args.date_to))

if __name__ == "__main__":
    main()
