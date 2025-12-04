from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
from datetime import datetime, timedelta
import io
import os

from database import get_db, SMTData, TrainingHistory
from schemas import (
    SMTDataCreate, SMTDataResponse, PredictionRequest, PredictionResponse,
    TrainingRequest, TrainingResponse, RAGQueryRequest, RAGQueryResponse,
    DocumentUploadResponse
)
from data_generator import SMTDataGenerator
from ml_model import FailurePredictionModel
from rag_engine import RAGEngine, create_initial_manual

app = FastAPI(title="NEXIO.HUB", version="2.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 객체
ml_model = FailurePredictionModel()
rag_engine = RAGEngine()
data_generator = SMTDataGenerator()

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    # 초기 매뉴얼 생성 및 RAG 등록
    manual_path = create_initial_manual()
    
    # 기존 문서 수 확인
    if rag_engine.get_document_count() == 0:
        with open(manual_path, 'r', encoding='utf-8') as f:
            content = f.read()
        await rag_engine.add_document(
            content, 
            {'filename': 'smt_manual.txt', 'type': 'manual'}
        )

# ========== 데이터 관리 ==========

@app.post("/api/data/upload-csv", tags=["Data"])
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """CSV 파일 업로드"""
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        required_columns = ['line_id', 'temperature', 'vibration', 'current', 
                          'production_count', 'defect_count', 'cycle_time', 
                          'pressure', 'humidity', 'failure_occurred']
        
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail="CSV 형식이 올바르지 않습니다.")
        
        count = 0
        for _, row in df.iterrows():
            smt_data = SMTData(
                line_id=row['line_id'],
                temperature=float(row['temperature']),
                vibration=float(row['vibration']),
                current=float(row['current']),
                production_count=int(row['production_count']),
                defect_count=int(row['defect_count']),
                cycle_time=float(row['cycle_time']),
                pressure=float(row['pressure']),
                humidity=float(row['humidity']),
                failure_occurred=bool(row['failure_occurred'])
            )
            db.add(smt_data)
            count += 1
        
        db.commit()
        return {"success": True, "count": count, "message": f"{count}개 데이터 업로드 완료"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/data/generate", tags=["Data"])
def generate_sample_data(samples: int = 1000, db: Session = Depends(get_db)):
    """샘플 데이터 생성"""
    try:
        result = data_generator.save_to_db(db, samples)
        return {
            "success": True, 
            "message": f"{result['count']}개 데이터 생성 완료",
            "csv_saved": True,
            "csv_path": result['csv_path'],
            "csv_filename": result['csv_filename']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/data/add", response_model=SMTDataResponse, tags=["Data"])
def add_smt_data(data: SMTDataCreate, db: Session = Depends(get_db)):
    """수동 데이터 추가"""
    try:
        # 예측 실행
        prediction = ml_model.predict(data.dict())
        
        # DB 저장
        smt_data = SMTData(
            **data.dict(),
            predicted_failure=prediction['predicted_failure'],
            failure_probability=prediction['failure_probability']
        )
        db.add(smt_data)
        db.commit()
        db.refresh(smt_data)
        
        return smt_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/list", response_model=List[SMTDataResponse], tags=["Data"])
def get_data_list(
    skip: int = 0, 
    limit: int = 100, 
    line_id: str = None,
    db: Session = Depends(get_db)
):
    """데이터 조회"""
    query = db.query(SMTData)
    
    if line_id:
        query = query.filter(SMTData.line_id == line_id)
    
    data = query.order_by(SMTData.timestamp.desc()).offset(skip).limit(limit).all()
    return data

@app.get("/api/data/stats", tags=["Data"])
def get_stats(db: Session = Depends(get_db)):
    """통계 정보"""
    total = db.query(SMTData).count()
    failures = db.query(SMTData).filter(SMTData.failure_occurred == True).count()
    
    # 최근 24시간 데이터
    recent_time = datetime.now() - timedelta(hours=24)
    recent = db.query(SMTData).filter(SMTData.timestamp >= recent_time).count()
    
    # 라인별 통계
    lines = db.query(SMTData.line_id).distinct().all()
    line_stats = {}
    
    for (line_id,) in lines:
        line_data = db.query(SMTData).filter(SMTData.line_id == line_id)
        line_stats[line_id] = {
            'total': line_data.count(),
            'failures': line_data.filter(SMTData.failure_occurred == True).count()
        }
    
    return {
        'total_records': total,
        'total_failures': failures,
        'failure_rate': round(failures / total * 100, 2) if total > 0 else 0,
        'recent_24h': recent,
        'lines': line_stats
    }

# ========== 실시간 모니터링 ==========

@app.get("/api/monitor/realtime", tags=["Monitor"])
def get_realtime_data(line_id: str = "LINE_01", db: Session = Depends(get_db)):
    """실시간 데이터 (최근 1개)"""
    data = db.query(SMTData)\
        .filter(SMTData.line_id == line_id)\
        .order_by(SMTData.timestamp.desc())\
        .first()
    
    if not data:
        # 데이터 없으면 샘플 생성
        sample = data_generator.generate_normal_data(line_id)
        return sample
    
    return {
        'timestamp': data.timestamp,
        'temperature': data.temperature,
        'vibration': data.vibration,
        'current': data.current,
        'production_count': data.production_count,
        'defect_count': data.defect_count,
        'cycle_time': data.cycle_time,
        'pressure': data.pressure,
        'humidity': data.humidity,
        'predicted_failure': data.predicted_failure,
        'failure_probability': data.failure_probability
    }

@app.get("/api/monitor/chart", tags=["Monitor"])
def get_chart_data(
    line_id: str = "LINE_01",
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """차트용 시계열 데이터"""
    start_time = datetime.now() - timedelta(hours=hours)
    
    data = db.query(SMTData)\
        .filter(SMTData.line_id == line_id)\
        .filter(SMTData.timestamp >= start_time)\
        .order_by(SMTData.timestamp)\
        .all()
    
    return {
        'timestamps': [d.timestamp.isoformat() for d in data],
        'temperature': [d.temperature for d in data],
        'vibration': [d.vibration for d in data],
        'current': [d.current for d in data],
        'failure_probability': [d.failure_probability for d in data]
    }

# ========== AI 예측 ==========

@app.post("/api/predict", response_model=PredictionResponse, tags=["AI"])
def predict_failure(request: PredictionRequest):
    """고장 예측"""
    try:
        result = ml_model.predict(request.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/model/train", response_model=TrainingResponse, tags=["AI"])
def train_model(request: TrainingRequest, db: Session = Depends(get_db)):
    """모델 학습"""
    try:
        result = ml_model.train(db, request.min_samples)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/model/info", tags=["AI"])
def get_model_info(db: Session = Depends(get_db)):
    """모델 정보"""
    # 최근 학습 이력
    history = db.query(TrainingHistory)\
        .order_by(TrainingHistory.timestamp.desc())\
        .first()
    
    if not history:
        return {
            'trained': False,
            'message': '학습된 모델이 없습니다.'
        }
    
    # 특성 중요도
    importance = ml_model.get_feature_importance()
    
    return {
        'trained': True,
        'last_training': history.timestamp.isoformat(),
        'accuracy': history.accuracy,
        'precision': history.precision,
        'recall': history.recall,
        'f1_score': history.f1_score,
        'training_samples': history.training_samples,
        'feature_importance': importance
    }

# ========== RAG ==========

@app.post("/api/rag/query", response_model=RAGQueryResponse, tags=["RAG"])
async def query_rag(request: RAGQueryRequest):
    """RAG 질의응답"""
    try:
        result = await rag_engine.query(request.query, request.top_k)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rag/upload", response_model=DocumentUploadResponse, tags=["RAG"])
async def upload_document(file: UploadFile = File(...)):
    """문서 업로드"""
    try:
        content = await file.read()
        text = content.decode('utf-8')
        
        await rag_engine.add_document(
            text,
            {'filename': file.filename, 'type': 'uploaded'}
        )
        
        return {
            'success': True,
            'message': '문서 업로드 완료',
            'filename': file.filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rag/stats", tags=["RAG"])
def get_rag_stats():
    """RAG 통계"""
    return {
        'document_count': rag_engine.get_document_count(),
        'embedding_model': rag_engine.embedding_model,
        'llm_model': rag_engine.llm_model
    }

@app.delete("/api/rag/clear", tags=["RAG"])
def clear_rag_documents():
    """RAG 문서 초기화"""
    try:
        rag_engine.clear_documents()
        return {'success': True, 'message': '문서 초기화 완료'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== 헬스체크 ==========

@app.get("/", tags=["System"])
def root():
    return {
        "service": "SMT AI Factory",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy"}