import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SMTData
import os

class SMTDataGenerator:
    def __init__(self):
        # 정상 동작 범위 (더 넓게)
        self.normal_ranges = {
            'temperature': (180, 225),  # 220 → 225로 확대
            'vibration': (0.1, 0.6),    # 0.5 → 0.6으로 확대
            'current': (15, 27),        # 25 → 27로 확대
            'production_count': (75, 120),  # 80 → 75로 확대
            'defect_count': (0, 4),     # 3 → 4로 확대
            'cycle_time': (2.7, 3.3),   # 2.8-3.2 → 2.7-3.3으로 확대
            'pressure': (0.43, 0.57),   # 0.45-0.55 → 0.43-0.57로 확대
            'humidity': (38, 62)        # 40-60 → 38-62로 확대
        }
        
        # 고장 전조 패턴 (정상 범위와 많이 겹치게)
        self.failure_patterns = {
            'temperature': (220, 270),   # 230 → 220로 낮춤 (정상과 겹침)
            'vibration': (0.55, 1.3),    # 0.8 → 0.55로 낮춤
            'current': (26, 35),         # 28 → 26으로 낮춤
            'production_count': (50, 80), # 40-70 → 50-80으로 조정
            'defect_count': (3, 12),     # 5 → 3으로 낮춤
            'cycle_time': (3.2, 4.3),    # 3.5 → 3.2로 낮춤
            'pressure': (0.38, 0.45),    # 0.35-0.42 → 0.38-0.45로 조정
            'humidity': (58, 78)         # 65 → 58로 낮춤
        }
    
    def generate_normal_data(self, line_id: str = "LINE_01") -> dict:
        """정상 상태 데이터 생성 (더 큰 노이즈)"""
        # 노이즈를 10%로 증가 (현실적인 변동성)
        noise_factor = np.random.uniform(0.90, 1.10)
        
        # 30% 확률로 경계선에 가까운 데이터 생성
        if np.random.random() < 0.30:
            return {
                'line_id': line_id,
                'temperature': np.random.uniform(210, 225) * noise_factor,
                'vibration': np.random.uniform(0.45, 0.6) * noise_factor,
                'current': np.random.uniform(23, 27) * noise_factor,
                'production_count': int(np.random.uniform(75, 90) * noise_factor),
                'defect_count': int(np.random.uniform(2, 4) * noise_factor),
                'cycle_time': np.random.uniform(3.0, 3.3) * noise_factor,
                'pressure': np.random.uniform(0.45, 0.50) * noise_factor,
                'humidity': np.random.uniform(55, 62) * noise_factor,
                'failure_occurred': False
            }
        
        return {
            'line_id': line_id,
            'temperature': np.random.uniform(*self.normal_ranges['temperature']) * noise_factor,
            'vibration': np.random.uniform(*self.normal_ranges['vibration']) * noise_factor,
            'current': np.random.uniform(*self.normal_ranges['current']) * noise_factor,
            'production_count': int(np.random.uniform(*self.normal_ranges['production_count']) * noise_factor),
            'defect_count': int(np.random.uniform(*self.normal_ranges['defect_count']) * noise_factor),
            'cycle_time': np.random.uniform(*self.normal_ranges['cycle_time']) * noise_factor,
            'pressure': np.random.uniform(*self.normal_ranges['pressure']) * noise_factor,
            'humidity': np.random.uniform(*self.normal_ranges['humidity']) * noise_factor,
            'failure_occurred': False
        }
    
    def generate_failure_data(self, line_id: str = "LINE_01") -> dict:
        """고장 전조 데이터 생성 (정상 범위와 많이 겹치게)"""
        # 노이즈 추가
        noise_factor = np.random.uniform(0.90, 1.10)
        
        # 40% 확률로 정상과 매우 유사한 고장 데이터 (판별 어려움)
        if np.random.random() < 0.40:
            return {
                'line_id': line_id,
                'temperature': np.random.uniform(218, 240) * noise_factor,
                'vibration': np.random.uniform(0.50, 0.75) * noise_factor,
                'current': np.random.uniform(24, 29) * noise_factor,
                'production_count': int(np.random.uniform(65, 85) * noise_factor),
                'defect_count': int(np.random.uniform(3, 7) * noise_factor),
                'cycle_time': np.random.uniform(3.1, 3.7) * noise_factor,
                'pressure': np.random.uniform(0.40, 0.48) * noise_factor,
                'humidity': np.random.uniform(56, 68) * noise_factor,
                'failure_occurred': True
            }
        
        # 20% 확률로 중간 수준의 고장 징후
        if np.random.random() < 0.25:  # 남은 60% 중 20%
            return {
                'line_id': line_id,
                'temperature': np.random.uniform(235, 255) * noise_factor,
                'vibration': np.random.uniform(0.70, 1.0) * noise_factor,
                'current': np.random.uniform(28, 32) * noise_factor,
                'production_count': int(np.random.uniform(55, 70) * noise_factor),
                'defect_count': int(np.random.uniform(6, 10) * noise_factor),
                'cycle_time': np.random.uniform(3.5, 4.0) * noise_factor,
                'pressure': np.random.uniform(0.38, 0.43) * noise_factor,
                'humidity': np.random.uniform(65, 73) * noise_factor,
                'failure_occurred': True
            }
        
        # 나머지 40% - 명확한 고장 패턴
        return {
            'line_id': line_id,
            'temperature': np.random.uniform(*self.failure_patterns['temperature']) * noise_factor,
            'vibration': np.random.uniform(*self.failure_patterns['vibration']) * noise_factor,
            'current': np.random.uniform(*self.failure_patterns['current']) * noise_factor,
            'production_count': int(np.random.uniform(*self.failure_patterns['production_count']) * noise_factor),
            'defect_count': int(np.random.uniform(*self.failure_patterns['defect_count']) * noise_factor),
            'cycle_time': np.random.uniform(*self.failure_patterns['cycle_time']) * noise_factor,
            'pressure': np.random.uniform(*self.failure_patterns['pressure']) * noise_factor,
            'humidity': np.random.uniform(*self.failure_patterns['humidity']) * noise_factor,
            'failure_occurred': True
        }
    
    def generate_dataset(self, 
                        total_samples: int = 5000, 
                        failure_ratio: float = 0.15,
                        lines: list = ["LINE_01", "LINE_02", "LINE_03"]) -> pd.DataFrame:
        """학습용 데이터셋 생성"""
        data_list = []
        failure_count = int(total_samples * failure_ratio)
        normal_count = total_samples - failure_count
        
        # 정상 데이터 생성
        for _ in range(normal_count):
            line_id = np.random.choice(lines)
            data_list.append(self.generate_normal_data(line_id))
        
        # 고장 데이터 생성
        for _ in range(failure_count):
            line_id = np.random.choice(lines)
            data_list.append(self.generate_failure_data(line_id))
        
        df = pd.DataFrame(data_list)
        df = df.sample(frac=1).reset_index(drop=True)  # 셔플
        
        return df
    
    def save_to_db(self, db: Session, samples: int = 5000):
        """DB에 샘플 데이터 저장 + CSV 자동 저장 (하루 전 데이터로 생성)"""
        df = self.generate_dataset(samples)
        
        # === 하루 전부터 시작하는 타임스탬프 생성 ===
        now = datetime.now()
        one_day_ago = now - timedelta(days=1)
        
        minutes_interval = 10
        total_minutes = samples * minutes_interval
        
        # 시작 시간: 하루 전 - (전체 샘플 * 간격)
        start_time = one_day_ago - timedelta(minutes=total_minutes)
        
        for idx, row in df.iterrows():
            # 과거부터 하루 전까지 순차적으로 시간 할당
            timestamp = start_time + timedelta(minutes=idx * minutes_interval)
            
            smt_data = SMTData(
                timestamp=timestamp,
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
        
        db.commit()
        
        # CSV 자동 저장
        csv_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            'data', 
            'exports'
        )
        os.makedirs(csv_dir, exist_ok=True)
        
        timestamp_str = now.strftime('%Y%m%d_%H%M%S')
        csv_filename = f'smt_data_{timestamp_str}.csv'
        csv_path = os.path.join(csv_dir, csv_filename)
        
        # 타임스탬프 추가하여 저장
        df_with_time = df.copy()
        df_with_time['timestamp'] = [start_time + timedelta(minutes=i*minutes_interval) for i in range(len(df))]
        df_with_time.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        end_time = start_time + timedelta(minutes=(len(df)-1)*minutes_interval)
        
        return {
            'count': len(df),
            'csv_path': csv_path,
            'csv_filename': csv_filename,
            'time_range': f'{start_time.strftime("%Y-%m-%d %H:%M")} ~ {end_time.strftime("%Y-%m-%d %H:%M")}'
        }
    
    def export_to_csv(self, filename: str = "training_data.csv", samples: int = 5000):
        """CSV로 내보내기"""
        df = self.generate_dataset(samples)
        
        # data/exports 폴더에 저장
        export_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            'data', 
            'exports'
        )
        os.makedirs(export_dir, exist_ok=True)
        
        filepath = os.path.join(export_dir, filename)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        return filepath