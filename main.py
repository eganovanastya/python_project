from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import random
import string
from fastapi.middleware.cors import CORSMiddleware


# --- 1. НАСТРОЙКА БАЗЫ ДАННЫХ (SQLite) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./quiz.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. МОДЕЛИ БАЗЫ ДАННЫХ ---
class RoomDB(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    status = Column(String, default="waiting")

Base.metadata.create_all(bind=engine)

# --- 3. СХЕМЫ ДЛЯ API ---
class RoomCreateResponse(BaseModel):
    room_code: str
    status: str

# --- 4. ПРИЛОЖЕНИЕ ---
app = FastAPI(title="Quiz App Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем всем (для разработки)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 5. МЕНЕДЖЕР ПОДКЛЮЧЕНИЙ (WebSocket) ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.room_players: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, room_code: str, username: str):
        await websocket.accept()
        if room_code not in self.active_connections:
            self.active_connections[room_code] = []
            self.room_players[room_code] = []
        self.active_connections[room_code].append(websocket)
        self.room_players[room_code].append(username)

    def disconnect(self, websocket: WebSocket, room_code: str, username: str):
        if room_code in self.active_connections:
            if websocket in self.active_connections[room_code]:
                self.active_connections[room_code].remove(websocket)
            if username in self.room_players[room_code]:
                self.room_players[room_code].remove(username)
            if len(self.active_connections[room_code]) == 0:
                del self.active_connections[room_code]
                del self.room_players[room_code]

    async def broadcast_players(self, room_code: str):
        if room_code in self.active_connections:
            players_list = self.room_players[room_code]
            for connection in self.active_connections[room_code]:
                await connection.send_json({"event": "UPDATE_PLAYERS", "players": players_list})

manager = ConnectionManager()

# --- 6. БАЗА ДАННЫХ (зависимость) ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 7. ГЕНЕРАЦИЯ КОДА ---
def generate_room_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# --- 8. ЭНДПОИНТЫ ---
@app.post("/api/rooms", response_model=RoomCreateResponse)
def create_room(db: Session = Depends(get_db)):
    while True:
        code = generate_room_code()
        existing_room = db.query(RoomDB).filter(RoomDB.code == code).first()
        if not existing_room:
            break
    new_room = RoomDB(code=code, status="waiting")
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    return {"room_code": new_room.code, "status": new_room.status}

@app.get("/")
def root():
    return {"message": "Сервер работает!"}

# --- 9. WEB SOCKET (Самое главное!) ---
@app.websocket("/ws/{room_code}/{username}")
async def websocket_endpoint(websocket: WebSocket, room_code: str, username: str, db: Session = Depends(get_db)):
    # 1. Проверяем, есть ли комната в БД
    room = db.query(RoomDB).filter(RoomDB.code == room_code.upper()).first()
    if not room:
        await websocket.close(code=4004)
        return

    # 2. Проверяем дубликат имени
    if room_code in manager.room_players and username in manager.room_players[room_code]:
        await websocket.close(code=4005)
        return

    # 3. Подключаем
    await manager.connect(websocket, room_code, username)
    await manager.broadcast_players(room_code)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_code, username)
        await manager.broadcast_players(room_code)