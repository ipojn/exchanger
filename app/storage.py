import hashlib
import secrets
import string
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

ALPHABET = string.ascii_letters + string.digits
CODE_LEN = 6
TTL = timedelta(days=7)

def generation_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(CODE_LEN))

def code_hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()

@dataclass
class FileMeta:
    id: str
    code_hash: str
    original_name: str
    size: int
    content_type: str | None
    created_at: datetime
    expires_at: datetime

class InMemoryStorage:
    def __init__(self) -> None:
        self._by_hash: dict[str, FileMeta] = {}

    def put(self, meta: FileMeta) -> None:
        self._by_hash[meta.code_hash] = meta

    def get(self, code: str) -> FileMeta | None:
        meta = self._by_hash.get(code_hash(code))
        if meta is None:
            return None
        if meta.expires_at <= datetime.now(timezone.utc):
            self._by_hash.pop(meta.code_hash, None)
            return None
        return meta

    def delete(self, code: str) -> None:
        self._by_hash.pop(code_hash(code), None)

    def purge_expired(self) -> int:
        now = datetime.now(timezone.utc)
        expired = [h for h, m in self._by_hash.items() if m.expires_at <= now]

        for h in expired:
            self._by_hash.pop(h, None)
        return len(expired)


storage = InMemoryStorage()