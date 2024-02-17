from __future__ import annotations

import json
import os
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING

from dulwich.errors import NotGitRepository
from dulwich.repo import Repo
from pydantic import BaseModel, parse_file_as
from pydantic.json import pydantic_encoder

if TYPE_CHECKING:
    from .config import Account

CACHE_DIR = "cache"


def load_transactions(account: Account):
    try:
        return parse_file_as(
            list[account.transaction_model], Path(CACHE_DIR, f"{account.name}.json")
        )
    except FileNotFoundError:
        return []


def with_cache_dir(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
        func(*args, **kwargs)

    return wrapper


@with_cache_dir
def store_transactions(account: Account, transactions: list[BaseModel]):
    for t in transactions:
        assert isinstance(
            t, account.transaction_model
        ), f"Tried to store invalid transaction type for {account.name}. {t.__class__} != {account.transaction_model}"

    with open(Path(CACHE_DIR, f"{account.name}.json"), "w") as f:
        f.write(json.dumps(transactions, indent=4, default=pydantic_encoder))


@with_cache_dir
def store_diff(diff):
    Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
    with open(Path(CACHE_DIR, "diff.json"), "w") as f:
        f.write(json.dumps(diff, indent=4, default=pydantic_encoder))


@contextmanager
def commit_cache_changes():
    try:
        r = Repo(CACHE_DIR)
    except NotGitRepository:
        r = Repo.init(CACHE_DIR)
    try:
        yield
    finally:
        files = [f for f in os.listdir(CACHE_DIR) if f.endswith(".json")]
        if len(files) > 0:
            r.stage(files)

            r.do_commit(
                message=b"Update",
                author=b"tg_bank_forwarder <>",
            )

            r.close()
