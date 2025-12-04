import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler
import joblib
import os
from sqlalchemy.orm import Session
from database import SMTData, TrainingHistory
from datetime import datetime

class FailurePredictionModel:
    def __init__(self, model_path: str = None):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = [
            'temperature', 'vibration', 'current', 
            'production_count', 'defect_count', 'cycle_time',
            'pressure', 'humidity'
        ]
        
        if model_path is None:
            self.model_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                'models', 
                'failure_prediction_model.pkl'
            )
            self.scaler_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                'models', 
                'scaler.pkl'
            )
        else:
            self.model_path = model_path
            self.scaler_path = model_path.replace('.pkl', '_scaler.pkl')
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        # 저장된 모델 로드
        self.load_model()
    
    def load_model(self):
        """저장된 모델 로드"""
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            return True
        return False
    
    def save_model(self):
        """모델 저장"""
        if self.model is not None:
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
    
    def prepare_data(self, df: pd.DataFrame):
        """데이터 전처리"""
        X = df[self.feature_columns].values
        y = df['failure_occurred'].values
        
        # 스케일링
        X_scaled = self.scaler.fit_transform(X)
        
        return X_scaled, y
    
    def train(self, db: Session, min_samples: int = 100):
        """모델 학습 - 현실적인 성능을 위한 제약"""
        # DB에서 데이터 로드
        data = db.query(SMTData).all()
        
        if len(data) < min_samples:
            return {
                'success': False,
                'message': f'학습 데이터 부족. 최소 {min_samples}개 필요, 현재 {len(data)}개',
                'accuracy': 0, 'precision': 0, 'recall': 0, 'f1_score': 0
            }
        
        # DataFrame 변환
        df = pd.DataFrame([{
            'temperature': d.temperature,
            'vibration': d.vibration,
            'current': d.current,
            'production_count': d.production_count,
            'defect_count': d.defect_count,
            'cycle_time': d.cycle_time,
            'pressure': d.pressure,
            'humidity': d.humidity,
            'failure_occurred': d.failure_occurred
        } for d in data])
        
        # 데이터 준비
        X, y = self.prepare_data(df)
        
        # 학습/테스트 분할 (테스트 30%로 증가)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )
        
        # ===== 핵심 변경: 모델 제약 =====
        # 과적합 방지를 위한 제한적 파라미터
        self.model = RandomForestClassifier(
            n_estimators=12,        # 100 → 20 (트리 수 대폭 감소)
            max_depth=3,            # 10 → 3 (깊이 제한 - 복잡한 패턴 학습 제한)
            min_samples_split=35,   # 새로 추가: 노드 분할 최소 샘플
            min_samples_leaf=18,    # 새로 추가: 리프 노드 최소 샘플
            max_features='sqrt',    # 새로 추가: 각 트리가 일부 특성만 사용
            random_state=42,
            n_jobs=-1
        )
        self.model.fit(X_train, y_train)
        
        # 예측 및 평가
        y_pred = self.model.predict(X_test)
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        # 모델 저장
        self.save_model()
        
        # 학습 이력 저장
        history = TrainingHistory(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            training_samples=len(data)
        )
        db.add(history)
        db.commit()
        
        return {
            'success': True,
            'message': '모델 학습 완료',
            'accuracy': round(accuracy, 4),
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1_score': round(f1, 4)
        }
    
    def predict(self, data: dict):
        """고장 예측"""
        if self.model is None:
            return {
                'predicted_failure': False,
                'failure_probability': 0.0,
                'risk_level': 'UNKNOWN',
                'recommendations': ['모델이 학습되지 않았습니다. 먼저 학습을 진행하세요.']
            }
        
        # 입력 데이터 준비
        X = np.array([[
            data['temperature'],
            data['vibration'],
            data['current'],
            data['production_count'],
            data['defect_count'],
            data['cycle_time'],
            data['pressure'],
            data['humidity']
        ]])
        
        # 스케일링
        X_scaled = self.scaler.transform(X)
        
        # 예측
        prediction = self.model.predict(X_scaled)[0]
        probability = self.model.predict_proba(X_scaled)[0][1]
        
        # 위험도 판단
        if probability < 0.3:
            risk_level = 'LOW'
            recommendations = ['정상 동작 중입니다.']
        elif probability < 0.6:
            risk_level = 'MEDIUM'
            recommendations = [
                '주의: 일부 센서 값이 정상 범위를 벗어났습니다.',
                '정기 점검을 권장합니다.'
            ]
        else:
            risk_level = 'HIGH'
            recommendations = [
                '경고: 고장 가능성이 높습니다.',
                '즉시 설비 점검이 필요합니다.',
                '예방 정비를 실시하세요.'
            ]
        
        # 이상 센서 식별
        if data['temperature'] > 230:
            recommendations.append('⚠ 온도 과열 감지')
        if data['vibration'] > 0.7:
            recommendations.append('⚠ 진동 이상 감지')
        if data['current'] > 27:
            recommendations.append('⚠ 전류 과부하 감지')
        if data['defect_count'] > 5:
            recommendations.append('⚠ 불량률 증가 감지')
        
        return {
            'predicted_failure': bool(prediction),
            'failure_probability': round(float(probability), 4),
            'risk_level': risk_level,
            'recommendations': recommendations
        }
    
    def get_feature_importance(self):
        """특성 중요도"""
        if self.model is None:
            return {}
        
        importance = self.model.feature_importances_
        return {
            feature: round(float(imp), 4) 
            for feature, imp in zip(self.feature_columns, importance)
        }