from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

Base = declarative_base()

class Chat(Base):
    __tablename__ = 'chats'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    chat_id = Column(String)
    notification = Column(Boolean, default=True)
    mute = Column(Boolean, default=False)
    subscribe = Column(Boolean, default=True)
    delete_message = Column(Boolean, default=False)
    ban = Column(Boolean, default=False)

def add_chat(chat_id, name, subscribe=False, mute=False, delete_message=True, ban=False, notification=True):
    session = Session()
    new_chat = Chat(chat_id=chat_id, name=name, subscribe=subscribe, mute=mute, delete_message=delete_message, ban=ban, notification=notification)
    session.add(new_chat)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
    finally:
        session.close()

async def get_chat_settings(chat_id: int):
    session = Session()
    try:
        query = select(Chat).filter_by(chat_id=str(chat_id))
        result = session.execute(query)
        chat = result.scalars().first()
        return chat
    except Exception as e:
        print(f"Ошибка получения настроек чата: {e}")
        return None
    finally:
        session.close()

# Database setup
DB_USER = 'default'
DB_PASSWORD = 'M9qpGDUuaPN2'
DB_NAME = 'verceldb'
DB_HOST = 'ep-yellow-art-a4ueqjif.us-east-1.aws.neon.tech'
DB_PORT = '5432'
DB_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require'
engine = create_engine(DB_URI)
Session = sessionmaker(bind=engine)
