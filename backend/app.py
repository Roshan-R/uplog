import uuid
import asyncio
from fastapi import FastAPI, Header
from fastapi.requests import Request
from base_models import LogEntryBaseModel
from models import Base, AnonymousUsers, Sessions
from settings import async_engine
from utils import get_hashed_client_ip
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from fastapi import Depends
from datetime import datetime, timedelta


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator:
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


AsyncSessionLocal = async_sessionmaker(
    async_engine,
    expire_on_commit=False,  # Prevents objects from expiring after commit, useful for returning them
    class_=AsyncSession,  # This is crucial for async sessions
)


# --- Database Dependency (Async) ---
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session."""
    async with AsyncSessionLocal() as session:
        yield session
        await session.close()  # Ensure session is closed


app = FastAPI(lifespan=lifespan)
app.state.lock = asyncio.Lock()
app.state.total = 0


@app.post("/user/create")
async def create_user(request: Request, db: AsyncSession = Depends(get_db_session)) -> dict:
    client_ip = get_hashed_client_ip(request)
    user_id = str(uuid.uuid4())
    user = AnonymousUsers(
        user_id=user_id, hashed_ip=client_ip, created_at=datetime.now(datetime.UTC)
    )
    db.add(user)
    await db.commit()
    return {"user_id": user_id}


@app.post("/session/create")
async def create_session(
    request: Request,
    user_id: str = Header(..., alias="User-Id"),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    print("Request with headers", request.headers)
    session_id = str(uuid.uuid4())
    stream_name = "stream-" + user_id
    subject_name = "subject-" + session_id
    session = Sessions(
        session_id=session_id,
        enable_sharing=False,
        user=user_id,
        subject_name=subject_name,
        stream_name=stream_name,
        expires_at=datetime.now(datetime.UTC) + timedelta(days=2),
        created_at=datetime.now(datetime.UTC),
    )
    db.add(session)
    await db.commit()
    return {"session_id": session_id}


@app.post("/session/upload")
async def upload_session(
    request: Request, session_id: str, tag: str, logs: list[LogEntryBaseModel]
):
    # print("Request with headers",request.headers)
    print("Current data", logs[0].message, "|", "Last data", logs[-1].message)
    async with app.state.lock:
        app.state.total += len(logs)
    # await asyncio.sleep(random.randint(2,10))
    print(app.state.total)
