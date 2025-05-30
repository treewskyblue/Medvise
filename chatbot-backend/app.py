import os
import json
import logging
import requests
import re
from pillow_heif import register_heif_opener
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from utils.llm_processor import process_with_openai
from utils.rag_engine import RAGEngine


# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 환경 변수 설정
ML_API_URL = os.getenv('ML_API_URL', 'http://ml-backend:8000')
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# 디렉토리 설정
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'medical_guidelines')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # 최대 50MB 업로드 제한

# RAG Engine initialize
rag_engine = RAGEngine(
    medical_guidelines_dir = UPLOAD_FOLDER,
    vector_db_dir = os.path.join(os.getcwd(), 'data/vector_db'),
    embedding_model = "local",
    openai_api_key = OPENAI_API_KEY
)

# 혈액검사 매핑 정보 - 모델이 필요로 하는 입력 필드
BLOOD_TEST_MAPPING = {
        "glucose": 0,
        "albumin": 1,
        "bun": 2,
        "phosphorus": 3,
        "total_protein": 4
}

# 결과 필드 이름 매핑
RESULT_MAPPING = {
    "TPNCALCULATEDGLUCOSE": "포도당 공급량",
    "TPNCALCULATEDPROTEIN": "단백질 공급량",
    "TPNCALCULATEDLIPID": "지질 공급량",
    "TPNCALCULATEDCALORI": "총 칼로리 공급량"
}

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        chat_history = data.get('history', [])

        logger.info(f"Received user message: {user_message}")

        # RAG에서 관련 컨텍스트 검색
        context_docs, combined_context = rag_engine.retrieve_relevant_context(user_message, k=7)

        # 관련 내용이 있으면 로그에 기록
        if context_docs:
            logger.info(f"Found {len(context_docs)} relevant documents")
            for i, doc in enumerate(context_docs):
                logger.info(f"Document {i+1}: {doc['filename']}")

        # LLM을 사용하여 혈액검사 값 추출
        extracted_values, llm_response = process_with_openai(
            user_message,
            chat_history,
            BLOOD_TEST_MAPPING,
            context=combined_context
        )

        # 추출된 값이 있으면 ML 예측 실행
        if extracted_values and all(key in extracted_values for key in BLOOD_TEST_MAPPING.keys()):
            # 모델에 필요한 형식으로 데이터 포맷 변환
            model_input = [[
                extracted_values["glucose"],
                extracted_values["albumin"],
                extracted_values["bun"],
                extracted_values["phosphorus"],
                extracted_values["total_protein"]
            ]]

            # ML API에 예측 요청
            try:
                ml_response = requests.post(
                    f"{ML_API_URL}/predict",
                    json={"data": model_input},
                    timeout=5
                )

                if ml_response.status_code == 200:
                    prediction_results = ml_response.json()
                    logger.info(f"ML prediction results: {prediction_results}")

                    # 결과를 사용자 친화적 형식으로 변환
                    formatted_results = {}
                    for result in prediction_results:
                        for key, value in result.items():
                            formatted_name = RESULT_MAPPING.get(key, key)
                            formatted_results[formatted_name] = round(value, 2)

                    # LLM 응답에 예측 결과 추가
                    final_response = f"{llm_response}\n\n**TPN 처방 계획**\n"
                    for name, value in formatted_results.items():
                        unit = "g" if "칼로리" not in name else "kcal"
                        final_response += f"- {name}: {value} {unit}\n"

                    # 참고 문서 정보 추가
                    if context_docs:
                        final_response += "\n\n**참고한 진료 지침**\n"
                        for i, doc in enumerate(context_docs[:3]): # 최대 3개만 표시
                            source_name = os.path.basename(doc['source'])
                            final_response += f"{i+1}. {source_name}\n"

                    return jsonify({
                        "response": final_response,
                        "prediction": formatted_results,
                        "references": context_docs[:3] if context_docs else [] # 최대 3개의 참고 문서 정보 전달
                    })
                else:
                    error_msg = f"ML API 오류: {ml_response.status_code} - {ml_response.text}"
                    logger.error(error_msg)
                    return jsonify({
                        "response": f"{llm_response}\n\n죄송합니다. 예측 과정에서 오류가 발생했습니다. 다시 시도해 주세요.",
                        "error": error_msg
                    })
            except requests.exceptions.RequestException as e:
                logger.error(f"ML API 연결 오류: {str(e)}")
                return jsonify({
                    "response": f"{llm_response}\n\n죄송합니다. 기계 학습 예측 서비스에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.",
                    "error": str(e)
                })
        else:
            # 필요한 모든 값이 추출되지 않았을 경우,
            # 그러나 RAG 문서가 있는 경우 참조 정보는 제공
            final_response = llm_response

            # 참고 문서 정보 추가
            if context_docs:
                final_response += "\n\n**참고한 진료 지침**\n"
                for i, doc in enumerate(context_docs[:3]): # 최대 3개만 표시
                    source_name = os.path.basename(doc['source'])
                    page_info = f" (페이지 {doc.get('page', '?')})" if doc.get('page') else ""
                    final_response += f"{i+1}. {source_name}{page_info}\n"

            return jsonify({
                "response": final_response,
                "references": context_docs[:3] if context_docs else [] # 최대 3개의 참고 문서 정보 전달
            })
        
    except Exception as e:
        logger.exception("처리 중 오류 발생")
        return jsonify({
            "response": "죄송합니다. 요청을 처리하는 동안 오류가 발생했습니다.",
            "error": str(e)
        }), 500
    
@app.route('/api/guidelines', methods=['GET'])
def get_guidelines():
    """
    현재 저장된 모든 진료 지침 목록 조회
    """
    try:
        guidelines = rag_engine.get_all_guidelines()
        return jsonify({"guidelines": guidelines})
    except Exception as e:
        logger.exception("진료 지침 목록 조회 중 오류 발생")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/api/guidelines', methods=['POST'])
def upload_guideline():
    """
    새로운 진료 지침 업로드
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                "error": "파일이 없습니다."
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                "error": "선택된 파일이 없습니다."
            }), 400
        
        if file:
            # 한글 파일명 처리를 위한 함수
            def secure_korean_filename(filename):
                # 오류 가능성 높은 특수문자만 제거하고 한글은 유지
                return re.sub(r'[^\w\s가-힣.-]', '', filename).strip()
            
            # secure_filename 대신 secure_korean_filename 사용
            filename = secure_korean_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # 파일 저장
            file.save(file_path)

            # 파일 유형 확인 및 처리
            file_extension = os.path.splitext(filename)[1].lower()

            if file_extension == '.pdf':
                # PDF 파일은 그 경로를 RAG 엔진으로 전달
                file_type = 'pdf'
                success = rag_engine.add_guideline(filename, "", file_type)
            else:
                # 텍스트 파일 내용 읽기
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # RAG 엔진에 추가
                file_type = 'markdown' if filename.endswith(('.md', '.markdown')) else 'text'
                success = rag_engine.add_guideline(filename, content, file_type)

            if success:
                return jsonify({
                    "message": "진료 지침이 성공적으로 업로드되었습니다.",
                    "filename": filename
                })
            else:
                return jsonify({
                    "error": "진료 지침 처리 중 오류가 발생했습니다."
                }), 500
            
    except Exception as e:
        logger.exception("진료 지침 업로드 중 오류 발생")
        return jsonify({
            "error": str(e)
        }), 500
    
@app.route('/api/guidelines/<filename>', methods=['DELETE'])
def delete_guideline(filename):
    """
    진료 지침 삭제
    """
    try:
        filename = secure_filename(filename)
        success = rag_engine.delete_guideline(filename)

        if success:
            return jsonify({
                "message": f"진료 지침 '{filename}'이 성공적으로 삭제되었습니다."
            })
        else:
            return jsonify({
                "error": "진료 지침 삭제 중 오류가 발생했습니다."
            }), 500
    
    except Exception as e:
        logger.exception("진료 지침 삭제 중 오류 발생")
        return jsonify({
            "error": str(e)
        }), 500
    
@app.route('/api/guidelines/<filename>', methods=['GET'])
def get_guideline(filename):
    """
    특정 진료 지침 내용 조회
    """
    try:
        filename = secure_filename(filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        if not os.path.exists(file_path):
            return jsonify({
                "error": "해당 진료 지침을 찾을 수 없습니다."
            }), 404
        
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    except Exception as e:
        logger.exception("진료 지침 조회 중 오류 발생")
        return jsonify({
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)