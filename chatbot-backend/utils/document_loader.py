import os
import logging
import re
from typing import List, Dict, Optional
from langchain_community.document_loaders import TextLoader, Docx2txtLoader, UnstructuredMarkdownLoader, UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
import pdfplumber
import traceback
from langchain.schema import Document
from PyPDF2 import PdfReader
import pytesseract
from pdf2image import convert_from_path

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentLoader:
    """
    다양한 형식의 문서를 로드하고 처리하는 클래스
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        DocumentLoader 초기화
        
        Args:
            chunk_size: 문서를 나눌 청크의 크기 (디폴트 1000)
            chunk_overlap: 청크 간 겹치는 부분의 크기 (기본값 200)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
    def load_document(self, file_path: str) -> Optional[List[Document]]:
        """
        파일 유형에 따라 적절한 로더를 사용하여 문서를 로드
        
        Args:
            file_path (str): 로드할 파일의 경로
            
        Returns:
            LangChain Document: 객체 리스트 또는 로딩에 실패한 경우 None
        """

        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            documents = []

            if file_extension == '.txt':
                loader = TextLoader(file_path, encoding='utf-8') # 문서 확장자가 .txt일 경우 `TextLoader()` 사용
                documents = loader.load()

            elif file_extension == '.pdf':
                try:
                    # pdfplumber를 사용한 PDF 처리 시도
                    with pdfplumber.open(file_path) as pdf:
                        logger.info(f"pdfplumber로 PDF 처리 시작: {file_path}")

                        for i, page in enumerate(pdf.pages):
                            text = page.extract_text()
                            documents.append(Document(
                                page_content=text.strip(),
                                metadata={"source": file_path, "page": i+1, "filename": os.path.basename(file_path)}
                            ))
                        logger.info(f"pdfplumber로 {len(documents)}개 페이지 추출 완료")

                except Exception as pdf_err:
                    # pdfplumber 실패하면 기존 로직 실행
                    logger.info(f"pdfplumber 실패, OCR 시도: {str(pdf_err)}")
                    try:
                        # OCR 시도 (이미지 기반 PDF)
                        images = convert_from_path(file_path)
                        for i, image in enumerate(images):
                            text = pytesseract.image_to_string(image, lang = "kor+eng")
                            if text.strip():
                                documents.append(Document(
                                    page_content = text,
                                    metadata = {"source": file_path, "page": i+1, "filename": os.path.basename(file_path)}
                                ))
                    except Exception as ocr_err:
                        logger.error(f"OCR 처리 실패: {str(ocr_err)}")
                except Exception as all_err:
                    logger.error(f"PDF 처리 실패: {str(all_err)}")
                    return None
                    
            elif file_extension in ['.doc', '.docx']:
                loader = Docx2txtLoader(file_path) # 문서 확장자가 .doc, .docx일 경우 `Docx2txtLoader()` 사용
                documents = loader.load()

            elif file_extension in ['.md', '.markdown']:
                loader = UnstructuredMarkdownLoader(file_path) # 문서 확장자가 .md, .markdown일 경우 `UnstructuredMarkdownLoader()` 사용
                documents = loader.load()

            else:
                logger.error(f"지원되지 않는 파일 유형: {file_extension}") # 어느 곳에도 해당하지 않을 경우 error 로깅
                return None
            
            logger.info(f"문서 로드 완료: {file_path}, 총 {len(documents)}개의 문서")
            return documents
        
        except Exception as e:
            logger.error(f"문서 로드 중 오류 발생: {str(e)}")
            logger.error(f"상세 오류: {traceback.format_exc()}")
            return None
        
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        문서를 더 작은 청크로 분할
        
        Args:
            documents: 분할할 문서 리스트
            
        Returns:
            분할된 문서 리스트
        """
        try:
            split_docs = self.text_splitter.split_documents(documents)
            logger.info(f"문서 분할 완료: 총 {len(split_docs)}개의 청크 생성")
            return split_docs
        except Exception as e:
            logger.error(f"문서 분할 중 오류 발생: {str(e)}")
            return documents
        
    def process_dictionary(self, directory_path: str) -> List[Document]:
        """
        디렉토리 내의 모든 지원되는 문서 파일을 로드하고 분할
        
        Args:
            directory_path: 처리할 디렉토리 경로
            
        Returns:
            모든 문서의 분할된 청크 리스트
        """
        all_documents = [] # 모든 문서를 리스트로 관리

        try:
            for root, _, files in os.walk(directory_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_extension = os.path.splitext(file)[1].lower()

                    # 지원되는 파일 형식인지 확인
                    if file_extension in ['.txt', '.pdf', '.doc', '.docx', '.md', '.markdown']:
                        documents = self.load_document(file_path)

                        if documents:
                            # 메타데이터에 파일 이름과 경로 추가
                            for doc in documents:
                                doc.metadata['source'] = file_path
                                doc.metadata['filename'] = file

                            all_documents.extend(documents)

            # 모든 문서를 분할
            if all_documents:
                split_documents = self.split_documents(all_documents)
                logger.info(f"디렉토리 처리 완료: {directory_path}, 총 {len(split_documents)}개의 청크 생성")
                return split_documents
            else:
                logger.warning(f"로드된 문서가 없음: {directory_path}")
                return []
        
        except Exception as e:
            logger.error(f"디렉토리 처리 중 오류 발생: {str(e)}")
            return all_documents
        
    def clean_text(self, text: str) -> str:
        """
        텍스트 정리: 여러 줄 바꿈 및 공백 정리
        
        Args:
            text: 정리할 텍스트
            
        Returns:
            정리된 텍스트
        """
        # 여러 줄 바꿈을 하나로 치환
        text = re.sub(r'\n{3,}', '\n\n', text)

        # 여러 공백을 하나로 치환
        text = re.sub(r'\s{2,}', ' ', text)

        return text.strip()
    
    def process_uploaded_file(self, file_path: str, file_content: str, file_type: str = 'text') -> List[Document]:
        """
        업로드된 파일을 처리하여 Document 객체로 변환
        
        Args:
            file_path: 파일 경로 또는 식별자
            file_content: 파일 내용
            file_type: 파일 유형 (디폴트 'text')
            
        Returns:
            변환된 Document 객체 리스트
        """
        # 텍스트 정리
        cleaned_content = self.clean_text(file_content)

        # Document 객체 생성
        doc = Document(
            page_content=cleaned_content,
            metadata={
                'source': file_path,
                'filename': os.path.basename(file_path),
                'file_type': file_type
            }
        )

        # 문서 분할
        split_docs = self.text_splitter.split_documents([doc])
        logger.info(f"업로드된 파일 처리 완료: {file_path}, 총 {len(split_docs)}개의 청크 생성")

        return split_docs

