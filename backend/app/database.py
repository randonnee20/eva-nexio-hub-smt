from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
import os

# DB 경로 설정
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'smt_data.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 테이블 정의 (models 역할)
class SMTData(Base):
    __tablename__ = "smt_data"
    
    id = Column(Integer, primary_key=True, index=True)
    # 현재 시간을 자동으로 설정 (datetime.now 함수 참조)
    timestamp = Column(DateTime, default=datetime.now)
    line_id = Column(String, index=True)
    temperature = Column(Float)
    vibration = Column(Float)
    current = Column(Float)
    production_count = Column(Integer)
    defect_count = Column(Integer)
    cycle_time = Column(Float)
    pressure = Column(Float)
    humidity = Column(Float)
    failure_occurred = Column(Boolean, default=False)
    predicted_failure = Column(Boolean, default=False)
    failure_probability = Column(Float, default=0.0)

class TrainingHistory(Base):
    __tablename__ = "training_history"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    training_samples = Column(Integer)

class RAGDocument(Base):
    __tablename__ = "rag_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    content = Column(String)
    upload_date = Column(DateTime, default=datetime.now)
    document_type = Column(String)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 테이블 생성
Base.metadata.create_all(bind=engine)