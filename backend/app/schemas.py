from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class SMTDataCreate(BaseModel):
    line_id: str
    temperature: float
    vibration: float
    current: float
    production_count: int
    defect_count: int
    cycle_time: float
    pressure: float
    humidity: float
    failure_occurred: bool = False

class SMTDataResponse(BaseModel):
    id: int
    timestamp: datetime
    line_id: str
    temperature: float
    vibration: float
    current: float
    production_count: int
    defect_count: int
    cycle_time: float
    pressure: float
    humidity: float
    failure_occurred: bool
    predicted_failure: bool
    failure_probability: float

    class Config:
        from_attributes = True

class PredictionRequest(BaseModel):
    temperature: float
    vibration: float
    current: float
    production_count: int
    defect_count: int
    cycle_time: float
    pressure: float
    humidity: float

class PredictionResponse(BaseModel):
    predicted_failure: bool
    failure_probability: float
    risk_level: str
    recommendations: List[str]

class TrainingRequest(BaseModel):
    min_samples: int = 100

class TrainingResponse(BaseModel):
    success: bool
    message: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float

class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 3

class RAGQueryResponse(BaseModel):
    answer: str
    sources: List[str]

class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    filename: str