import os
import httpx
import chromadb
from chromadb.config import Settings
from typing import List

class RAGEngine:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api"
        self.embedding_model = "nomic-embed-text"
        self.llm_model = "bllossom"  # Bllossom/llama-3.2-Korean-Bllossom-3B
        
        # ChromaDB 초기화
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            'data', 
            'chromadb'
        )
        os.makedirs(db_path, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=db_path)
        
        # 컬렉션 생성/로드
        try:
            self.collection = self.client.get_collection("smt_manuals")
        except:
            self.collection = self.client.create_collection("smt_manuals")
    
    async def get_embedding(self, text: str) -> List[float]:
        """Ollama로 임베딩 생성"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.ollama_url}/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text
                }
            )
            return response.json()["embedding"]
    
    async def add_document(self, text: str, metadata: dict = None):
        """문서 추가"""
        # 텍스트를 청크로 분할 (500자 단위)
        chunks = [text[i:i+500] for i in range(0, len(text), 500)]
        
        for idx, chunk in enumerate(chunks):
            embedding = await self.get_embedding(chunk)
            
            doc_id = f"{metadata.get('filename', 'doc')}_{idx}" if metadata else f"doc_{idx}"
            
            self.collection.add(
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[metadata or {}],
                ids=[doc_id]
            )
    
    async def search(self, query: str, top_k: int = 3) -> List[dict]:
        """유사 문서 검색"""
        query_embedding = await self.get_embedding(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        documents = []
        if results['documents'] and len(results['documents']) > 0:
            for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                documents.append({
                    'content': doc,
                    'metadata': metadata
                })
        
        return documents
    
    async def generate_answer(self, query: str, context: str) -> str:
        """LLM으로 답변 생성"""
        prompt = f"""다음 매뉴얼 내용을 참고하여 질문에 답변하세요.

매뉴얼 내용:
{context}

질문: {query}

답변 (간결하고 명확하게):"""

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.ollama_url}/generate",
                json={
                    "model": self.llm_model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            return response.json()["response"]
    
    async def query(self, query: str, top_k: int = 3) -> dict:
        """RAG 쿼리"""
        # 관련 문서 검색
        documents = await self.search(query, top_k)
        
        if not documents:
            return {
                'answer': '관련 매뉴얼을 찾을 수 없습니다. 문서를 먼저 업로드해주세요.',
                'sources': []
            }
        
        # 컨텍스트 구성
        context = "\n\n".join([doc['content'] for doc in documents])
        
        # 답변 생성
        answer = await self.generate_answer(query, context)
        
        # 출처 정리
        sources = [doc['metadata'].get('filename', 'Unknown') for doc in documents]
        sources = list(set(sources))  # 중복 제거
        
        return {
            'answer': answer,
            'sources': sources
        }
    
    def get_document_count(self) -> int:
        """저장된 문서 수"""
        return self.collection.count()
    
    def clear_documents(self):
        """모든 문서 삭제"""
        self.client.delete_collection("smt_manuals")
        self.collection = self.client.create_collection("smt_manuals")


# 초기 매뉴얼 생성
def create_initial_manual():
    """SMT 장비 매뉴얼 생성"""
    manual_content = """
SMT(Surface Mount Technology) 장비 운영 매뉴얼

1. 장비 개요
- SMT 장비는 PCB에 전자 부품을 표면 실장하는 자동화 설비입니다.
- 주요 구성: 픽앤플레이스 헤드, 비전 시스템, 컨베이어, 리플로우 오븐

2. 정상 동작 범위
- 온도: 180-220°C (리플로우 존)
- 진동: 0.1-0.5mm/s (운영 중)
- 전류: 15-25A (정상 부하)
- 생산 속도: 80-120개/시간
- 불량률: 3% 이하
- 사이클 타임: 2.8-3.2초
- 공기압: 0.45-0.55 MPa
- 습도: 40-60% RH

3. 고장 전조 증상
- 온도 230°C 이상: 히터 고장 또는 냉각 시스템 이상
- 진동 0.7mm/s 이상: 모터 베어링 마모 또는 불균형
- 전류 27A 이상: 과부하 또는 전기 계통 이상
- 불량률 5% 이상: 노즐 마모, 비전 시스템 정렬 불량
- 사이클 타임 3.5초 이상: 구동부 마모, 소프트웨어 이상

4. 예방 정비 지침
일일 점검:
- 노즐 청소 및 확인
- 컨베이어 벨트 장력 확인
- 비전 카메라 렌즈 청소

주간 점검:
- 진공 압력 확인
- 필터 청소/교체
- 구동부 윤활

월간 점검:
- 모터 베어링 점검
- 전기 케이블 절연 확인
- 온도 센서 캘리브레이션
- 비전 시스템 정렬 확인

5. 긴급 조치 사항
온도 과열 시:
1. 즉시 장비 정지
2. 긴급 냉각 시스템 가동
3. 히터 퓨즈 확인
4. 서비스 엔지니어 호출

진동 이상 시:
1. 생산 속도 50%로 감속
2. 베어링 소음 청취
3. 진동 센서 재캘리브레이션
4. 필요시 베어링 교체

전류 과부하 시:
1. 부하 감소 (생산량 조정)
2. 전기 계통 점검
3. 전원 차단기 확인
4. 전기 기사 점검

불량률 증가 시:
1. 노즐 교체
2. 비전 시스템 재정렬
3. PCB 고정 상태 확인
4. 부품 공급 상태 확인

6. 소모품 교체 주기
- 노즐: 3개월 또는 100만 사이클
- 필터: 1개월
- 벨트: 6개월
- 베어링: 1년
- 진공 펌프 오일: 3개월

7. 안전 수칙
- 운전 중 안전문 개방 금지
- 고온 부위 접촉 주의
- 전원 차단 후 정비 작업
- 개인 보호구 착용 (안전화, 장갑)
- 비상정지 버튼 위치 숙지

8. 문의
- 기술지원: 1588-XXXX
- 긴급출동: 010-XXXX-XXXX
- 이메일: support@example.com
"""
    
    manual_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
        'rag_documents', 
        'smt_manual.txt'
    )
    os.makedirs(os.path.dirname(manual_path), exist_ok=True)
    
    with open(manual_path, 'w', encoding='utf-8') as f:
        f.write(manual_content)
    
    return manual_path