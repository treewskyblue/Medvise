import os
import logging
from typing import List, Dict, Any, Optional
from langchain.embeddings import HuggingFaceEmbeddings, OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingManager:
    """
    문서 임베딩 생성 및 벡터 데이터베이스 관리를 위한 클래스
    """

    def __init__(self, persist_directory: str = "./data/vector_db", embedding_model: str = "local", openai_api_key: Optional[str] = None):
        """
        EmbeddingManager 초기화
        
        Args:
            persist_directory: 벡터 데이터베이스 저장 디렉토리
            embedding_model: 사용할 임베딩 모델 ('local' 또는 'openai')
            openai_api_key: OpenAI 임베딩 사용할 경우 필요함
        """
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model

        # 임베딩 모델 초기화
        if embedding_model == "openai" and openai_api_key:
            logger.info("OpenAI 임베딩 모델 초기화 중...")
            self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        else:
            # 로컬 모델 사용 (sentence-transformers)
            logger.info("로컬 HuggingFace 임베딩 모델 초기화 중...")
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
        
        # 저장 디렉토리가 없으면 생성
        os.makedirs(persist_directory, exist_ok=True)

        # 벡터 저장소 초기화
        self._initialize_vector_store()

    def _initialize_vector_store(self):
        """
        Chroma 벡터 저장소 초기화 또는 로드
        """
        try:
            # 기존 벡터 저장소가 있으면 로드
            if os.path.exists(self.persist_directory):
                logger.info(f"기존 벡터 저장소 로드 중: {self.persist_directory}")
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
                # 기존 vector_store도 호환성을 위해 유지
                self.vector_store = self.vectorstore

                try:
                    doc_count = len(self.vectorstore.get()['ids'])
                    logger.info(f"벡터 저장소 로드 완료: {len(self.vector_store.get()['ids'])}개의 문서")
                except Exception as count_err:
                    logger.warning(f"문서 개수 확인 실패: {str(count_err)}")
            else:
                # 새로운 벡터 저장소 생성
                logger.info(f"새로운 벡터 저장소 생성 중: {self.persist_directory}")
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
                self.vector_store = self.vectorstore
                logger.info(f"새로운 벡터 저장소 생성 완료")
        except Exception as e:
            logger.error(f"벡터 저장소 초기화 중 오류 발생: {str(e)}")
            # 오류 발생 시 새 저장소 생성
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            self.vector_store = self.vectorstore
    
    def add_documents(self, documents: List[Document], collection_name: str = "medical_guidelines"):
        """
        문서를 벡터 저장소에 추가
        
        Args:
            documents: 추가할 문서 리스트
            collection_name: 저장할 컬렉션 이름
        
        Returns:
            성공 여부
        """
        try:
            logger.info(f"벡터 저장소에 {len(documents)}개의 문서 추가 중...")

            # 빈 문서 필터링
            valid_documents = [doc for doc in documents if doc.page_content and doc.page_content.strip()]

            if not valid_documents:
                logger.warning("추가할 유효한 문서가 없음")
                return False
            
            logger.info(f"유효한 문서 {len(valid_documents)}개 추가 중...")

            # 문서 추가
            self.vectorstore.add_documents(valid_documents)

            # 변경사항 저장
            self.vectorstore.persist()

            # 문서 개수 확인
            try:
                total_docs = len(self.vectorstore.get()['ids'])
                logger.info(f"문서 추가 완료: 총 {total_docs}개 문서 저장됨")
            except Exception as count_err:
                logger.warning(f"문서 개수 확인 실패: {str(count_err)}")
                logger.info("문서 추가 완료")

            return True

        except Exception as e:
            logger.error(f"문서 추가 중 오류 발생: {str(e)}")
            import traceback
            logger.error(traceback.foamat_exc())
            return False

    def search_documents(self, query: str, k: int = 5) -> List[Document]:
        """
        query와 관련된 문서 검색
        
        Args: 
            query: 검색 쿼리
            k: 반환할 문서 수
            
        Returns:
            검색된, 유사도가 높은 문서 리스트
        """
        try:
            logger.info(f"쿼리 실행 중: '{query}'")

            # 벡터 저장소에 문서가 있는지 확인
            try:
                all_docs = self.vectorstore.get()
                if not all_docs['ids']:
                    logger.warning("벡터 저장소에 문서가 없음")
                    return []
                logger.info(f"벡터 저장소에 총 {len(all_docs['ids'])}개 문서 존재")
            except Exception as check_err:
                logger.warning(f"문서 존재 확인 실패: {str(check_err)}")

            # 유사도 검색 실행
            docs = self.vector_store.similarity_search(query, k=k)
            logger.info(f"검색 완료: {len(docs)}개의 문서 검색됨")

            # 검색 결과 로깅 (디버깅용)
            for i, doc in enumerate(docs):
                logger.info(f"검색 결과 {i+1}: {doc.page_content[:100]}...")

            return docs
        except Exception as e:
            logger.error(f"문서 검색 중 오류 발생: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []
        
    def clear_collection(self):
        """
        벡터 저장소의 모든 문서 삭제
        """
        try:
            logger.info("벡터 저장소 내 모든 문서 삭제 중...")
            self.vectorstore.delete_collection()
            self._initialize_vector_store()
            logger.info("벡터 저장소 초기화 완료")
        except Exception as e:
            logger.error(f"벡터 저장소 삭제 중 오류 발생: {str(e)}")