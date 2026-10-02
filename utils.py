import argparse
import json
import sqlite3
import re
from datetime import datetime, timezone


def get_valid_date(date: str) -> datetime:
    """check if the date is valid"""
    try:
        return datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date: {date}. Date in YYYY-MM-DD format required."
        )


def get_filter(filter_files: list[str]) -> set[str] | None:
    """load filter words from files"""
    if filter_files is None:
        return None

    filters: set[str] = set()
    for filter_file in filter_files:
        with open(filter_file, "r", encoding="utf-8") as f:
            filters.update(value.casefold() for value in json.load(f))
    return filters


def get_db(database_file: str = "database.sqlite") -> sqlite3.Connection:
    """connect to the database and create tables if they don't exist"""
    # connect to putput database
    db = sqlite3.connect(database_file)
    cur = db.cursor()
    # make sure a table is created
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT not null,
            date datetime not null,
            text TEXT
        );
            
        CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_unique ON messages (channel, date, text);
            
        CREATE TABLE IF NOT EXISTS reactions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            reaction TEXT NOT NULL,
            count INTEGER NOT NULL
        );
    """)
    db.commit()
    return db


def prep_emoji(emoji: str) -> str:
    """keep only custom emoji name"""
    return re.sub(r"<a?:(\w+):\d+>", r"\1", emoji)


def prep_msg(msg: str) -> str:
    """replace discord mentions and other patterns with placeholders"""
    msg = re.sub(r"<?(?:https?://|www\.)[^\s<>()\[\]]+>?", "<URL>", msg, flags=re.I)
    msg = re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", "<EMAIL>", msg)
    msg = re.sub(
        r"(?<!\d)(?:\+?420[ -]?)?\d{3}[ -]?\d{3}[ -]?\d{3}(?!\d)", "<PHONE>", msg
    )
    msg = re.sub(r"<@!?\d+>", "<USER>", msg)
    msg = re.sub(r"<#\d+>", "<CHANNEL>", msg)
    msg = re.sub(r"<@&\d+>", "<ROLE>", msg)
    msg = re.sub(r"<a?:(\w+):\d+>", r"<emoji>\1</emoji>", msg)
    msg = re.sub(r"\b[0-9]{6}\b", "000000", msg)
    msg = re.sub(r"\bx[a-z]{5,6}[0-9]{2}\b", "xlogin00", msg, flags=re.I)

    return msg
