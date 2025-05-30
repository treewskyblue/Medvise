import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import json
from langchain.schema import Document
import traceback
from utils.document_loader import DocumentLoader
from utils.embeddings import EmbeddingManager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGEngine:
    """
    Retrieval-Augmented Generation (RAG) 기능을 구현한 엔진
    """

    def __init__(self, medical_guidelines_dir: str = "./medical_guidelines", vector_db_dir: str = "./data/vector_db", embedding_model: str = "local", openai_api_key: Optional[str] = None):
        """
        RAGEngine initialize
        
        Args:
            medical_guidelines_dir: 진료 지침 문서가 저장된 디렉토리
            vector_db_dir: 백터 데이터베이스 저장 디렉토리
            embedding_model: 사용할 임베딩 모델('local' 또는 'openai')
            openai_api_key: OpenAI API Key
        """

        # 진료 지침 디렉토리
        self.medical_guidelines_dir = medical_guidelines_dir

        # 필요한 디렉토리 생성
        os.makedirs(medical_guidelines_dir, exist_ok=True)
        os.makedirs(vector_db_dir, exist_ok=True)

        # 문서 로더 및 임베딩 관리자 초기화
        self.document_loader = DocumentLoader(chunk_size=1000, chunk_overlap=200)
        self.embedding_manager = EmbeddingManager(
            persist_directory=vector_db_dir,
            embedding_model=embedding_model,
            openai_api_key=openai_api_key
        )

        # 지침 문서 인덱싱
        self._index_guidelines()

    def _index_guidelines(self):
        """
        진료 지침 디렉토리에 있는 모든 문서를 인덱싱
        """
        try:
            # 디렉토리가 비어 있는지 확인
            files = os.listdir(self.medical_guidelines_dir)
            if not files:
                logger.info(f"진료 지침 디렉토리가 비어 있음: {self.medical_guidelines_dir}")
                return

            # 문서 로드 및 청크로 분할
            documents = self.document_loader.process_dictionary(self.medical_guidelines_dir)

            if documents:
                # 벡터 저장소에 문서 추가
                success = self.embedding_manager.add_documents(documents)
                if success:
                    logger.info(f"진료 지침 인덱싱 완료: 총 {len(documents)}개의 청크")
                else:
                    logger.error("벡터 저장소에 문서 추가 실패")
            else:
                logger.warning("인덱싱할 문서가 없음")

        except Exception as e:
            logger.error(f"진료 지침 인덱싱 중 오류 발생: {str(e)}")
            logger.error(traceback.format_exc())
    
    def add_guideline(self, file_path: str, content: str, file_type: str = "text") -> bool:
        """
        새로운 진료 지침 문서 추가
        
        Args:
            file_path: 저장할 파일 경로
            content: 파일 내용
            file_type: 파일 유형 (디폴트 text)
            
        Returns:
            성공 여부 (bool)
        """
        try:
            # 파일명 처리 개선: 한글 파일명 지원
            basename = os.path.basename(file_path)
            save_path = os.path.join(self.medical_guidelines_dir, basename)

            logger.info(f"진료 지침 추가 시작: {basename}, 파일 유형: {file_type}")

            # 파일이 이미 존재하는지 확인 (PDF는 app.py에서 이미 저장됨)
            if not os.path.exists(save_path) and content:
                # 파일 저장
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            # 문서 처리
            if file_type == 'pdf':
                # 로깅 추가
                logger.info(f"PDF 문서 처리 시작: {save_path}")

                # 상대 경로 대신 전체 경로 사용
                documents = self.document_loader.load_document(save_path)
                if documents:
                    # 청크로 분할
                    documents = self.document_loader.split_documents(documents)
                    logger.info(f"PDF 문서 분할 완료: {len(documents)}개 청크")
                else:
                    logger.warning(f"PDF 문서 로딩 실패: {file_path}")
                    return False
            else:
                # PDF 아닌 애들 처리

                if not content:
                    logger.error(f"텍스트 파일의 내용이 비어있음: {file_path}")
                    return False
                
                documents = self.document_loader.process_uploaded_file(
                    file_path=save_path,
                    file_content=content,
                    file_type=file_type
                )

            # 벡터 저장소에 추가
            if documents:
                logger.info(f"벡터 저장소에 문서 추가 시작: {len(documents)}개 청크")
                success = self.embedding_manager.add_documents(documents)
                if success:
                    logger.info(f"새 진료 지침 추가 완료: {file_path}")
                    return True
                else:
                    logger.error(f"벡터 저장소 추가 실패: {file_path}")
                    return False
            else:
                logger.warning(f"문서 처리 중 문제 발생: {file_path}, 청크가 생성되지 않음")
                return False
            
        except Exception as e:
            logger.error(f"진료 지침 추가 중 오류 발생: {str(e)}")
            logger.error(traceback.format_exc())
            return False
        
    def retrieve_relevant_context(self, query: str, k: int = 3) -> Tuple[List[Dict[str, Any]], str]:
        """
        쿼리와 관련된 진료 지침 검색
        
        Args:
            query: 사용자 쿼리
            k: 검색할 문서 수
            
        Returns:
            검색 결과 튜플 (관련 문서 리스트, 관련 문서를 결합한 문자열)
        """
        try:
            # 벡터 저장소에서 관련 문서 검색
            docs = self.embedding_manager.search_documents(query, k=k)

            # 검색 결과 가공
            context_docs = []
            combined_context = ""

            for i, doc in enumerate(docs):
                # 문서 메타데이터 및 내용 추출
                doc_info = {
                    "index": i+1,
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "Unknown"),
                    "filename": doc.metadata.get("filename", "Unknown"),
                    "page": doc.metadata.get("page", "Unknown")
                }
                context_docs.append(doc_info)

                # 결합된 컨텍스트 구성
                source_name = os.path.basename(doc.metadata.get("source", "Unknown"))
                page_info = f" (페이지 {doc.metadata.get('page', '?')})" if doc.metadata.get('page') else ""
                combined_context += f"\n\n[출처: {source_name}]\n{doc.page_content}"

                logger.info(f"검색된 컨텍스트 전체:\n{combined_context}")
                logger.info(f"컨텍스트 길이: {len(combined_context)} 문자")
            
            if not docs:
                logger.warning(f"쿼리에 대한 관련 문서를 찾을 수 없음: '{query}'")
                return [], ""
            
            logger.info(f"쿼리에 대해 {len(docs)}개의 관련 문서 검색됨: '{query}'")
            return context_docs, combined_context.strip()
        
        except Exception as e:
            logger.error(f"컨텍스트 검색 중 오류 발생: {str(e)}")
            logger.error(traceback.format_exc())
            return [], ""
        
    def get_all_guidelines(self) -> List[Dict[str, Any]]:
        """
        모든 저장된 진료 지침 목록 조회
        
        Returns:
            진료 지침 파일 리스트
        """
        guidelines = []

        try:
            # 디렉토리 내 모든 파일 확인
            for filename in os.listdir(self.medical_guidelines_dir):
                file_path = os.path.join(self.medical_guidelines_dir, filename)

                # 파일로 확인되는 경우에만 처리
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    file_extension = os.path.splitext(filename)[1].lower()

                    # 파일 정보 구성
                    guideline_info = {
                        "filename": filename,
                        "path": file_path,
                        "size": file_size,
                        "extension": file_extension
                    }
                    guidelines.append(guideline_info)
            logger.info(f"진료 지침 목록 조회 완료: 총 {len(guidelines)}개 파일")
            return guidelines
        
        except Exception as e:
            logger.error(f"진료 지침 목록 조회 중 오류 발생: {str(e)}")
            return []
        
    def delete_guideline(self, filename: str) -> bool:
        """
        진료 지침 파일 삭제
        
        Args:
            filename: 삭제할 파일 이름
            
        Returns:
            삭제 성공 여부 (bool)
        """
        try:
            file_path = os.path.join(self.medical_guidelines_dir, filename)

            # 파일 존재 여부 확인
            if not os.path.exists(file_path):
                logger.warning(f"삭제할 파일이 존재하지 않음: {filename}")
                return False
            
            # 파일 삭제
            os.remove(file_path)

            # 벡터 저장소 재구성 (삭제 후 모든 문서 다시 인덱싱)

            self.embedding_manager.clear_collection()
            self._index_guidelines()

            logger.info(f"진료 지침 삭제 완료: {filename}")
            return True

        except Exception as e:
            logger.error(f"진료 지침 삭제 중 오류 발생: {str(e)}")
            return False
    