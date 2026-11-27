import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .storage import CODE_LEN, TTL, FileMeta, code_hash, generate_code, storage

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_SIZE = 100 * 1024 * 1024
CHUNK = 1024 * 1024

app = FastAPI(title="exchanger")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def _data_path(file_id: str) -> Path:
    return UPLOAD_DIR / file_id


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


templates.env.filters["human_size"] = _human_size


# ---------- страницы ----------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/s/{code}", response_class=HTMLResponse)
async def share_page(request: Request, code: str):
    meta = storage.get(code)
    if meta is None:
        return templates.TemplateResponse(
            "download.html",
            {"request": request, "meta": None, "code": code},
            status_code=404,
        )
    return templates.TemplateResponse(
        "download.html",
        {"request": request, "meta": meta, "code": code},
    )


# ---------- API ----------

@app.post("/upload")
async def upload_file(file: Annotated[UploadFile, File(...)]):
    if not file.filename:
        raise HTTPException(400, "no filename")

    file_id = uuid.uuid4().hex
    data_path = _data_path(file_id)
    tmp_path = data_path.with_suffix(".part")

    size = 0
    try:
        with tmp_path.open("wb") as buffer:
            while chunk := await file.read(CHUNK):
                size += len(chunk)
                if size > MAX_SIZE:
                    raise HTTPException(413, f"file too large (max {MAX_SIZE // (1024*1024)} MiB)")
                await run_in_threadpool(buffer.write, chunk)
        tmp_path.replace(data_path)
    except HTTPException:
        tmp_path.unlink(missing_ok=True)
        raise
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(500, "upload failed")

    code = generate_code()
    now = datetime.now(timezone.utc)
    meta = FileMeta(
        id=file_id,
        code_hash=code_hash(code),
        original_name=file.filename,
        size=size,
        content_type=file.content_type,
        created_at=now,
        expires_at=now + TTL,
    )
    storage.put(meta)

    return {
        "code": code,
        "url": f"/s/{code}",
        "expires_at": meta.expires_at.isoformat(),
        "original_name": meta.original_name,
        "size": size,
    }


@app.get("/s/{code}/info")
async def share_info(code: str):
    meta = storage.get(code)
    if meta is None:
        raise HTTPException(404, "not found")
    return {
        "original_name": meta.original_name,
        "size": meta.size,
        "size_human": _human_size(meta.size),
        "content_type": meta.content_type,
        "expires_at": meta.expires_at.isoformat(),
        "ttl_seconds": int((meta.expires_at - datetime.now(timezone.utc)).total_seconds()),
    }


@app.get("/s/{code}/download")
async def share_download(code: str):
    meta = storage.get(code)
    if meta is None:
        raise HTTPException(404, "not found")
    data_path = _data_path(meta.id)
    if not data_path.is_file():
        raise HTTPException(404, "not found")
    return FileResponse(
        path=data_path,
        filename=meta.original_name,
        media_type=meta.content_type or "application/octet-stream",
        content_disposition_type="attachment",
    )