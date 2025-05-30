import os
import json
import logging
import openai

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API 키 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI API 설정
openai.api_key = OPENAI_API_KEY

def process_with_openai(user_message, chat_history, blood_test_mapping, context=None):
    """
    OpenAI API를 사용하여 사용자 메시지에서 혈액검사 값을 추출하고 응답 생성
    
    Args:
        user_message (str): 사용자 메시지
        chat_history (list): 채팅 기록
        blood_test_mapping (dict): 혈액검사 필드 매핑
        context (str, optional): RAG 시스템에서 검색한 관련 컨텍스트
        
    Returns:
        tuple: (추출된 값 딕셔너리, LLM 응답 텍스트)
    """

    try:
        # 대화 이력 구성
        messages = []

        # 시스템 메시지 - RAG context 유무에 따라 다르게 구성
        if context and context.strip():
            system_message = """
            당신은 신생아중환자실(NICU)에서 근무하는 의료진과 동등한 수준의 전문 지식을 갖추고 있는 챗봇입니다.

            **중요한 지침:**
            1. 답변은 반드시 아래 제공된 의학 문서의 내용에만 기반해야 합니다.
            2. 제공된 문서에 없는 정보는 절대 추가하지 마세요.
            3. 문서에서 답을 찾을 수 없는 경우, "제공된 문서에서 관련 정보를 찾을 수 없습니다"라고 명시하세요.
            4. 필요한 혈액검사 값이 입력된 경우에만 function call을 사용하세요.
            5. 소아청소년과 이외 다른 진료과에서 다루는 내용이 포함된 경우, 답변 마지막에 "타 진료과와 관련된 내용이 포함되어 있습니다. 필요시 Consult answer를 받으시기 바랍니다." 문장을 추가하세요.

            필요한 혈액 검사 값:
            1. 혈당 (Glucose, mg/dL) - 정상 범위: 70-100 mg/dL
            2. 알부민 (Albumin, g/dL) - 정상 범위: 3.4-5.4 g/dL
            3. 혈중요소질소 (BUN, mg/dL) - 정상 범위: 7-20 mg/dL
            4. 인 (Phosphorus, mg/dL) - 정상 범위: 2.5-4.5 mg/dL
            5. 총 단백질 (Total Protein, g/dL) - 정상 범위: 6.0-8.3 g/dL

            **참고할 의학 문서:**
            {context}

            위 내용을 참고하여 사용자의 질문에 최대한 도움이 되는 답변을 제공하세요. 검색된 내용이 제한적인 경우에도 가능한 정보를 제공하고, 더 자세한 내용이 필요하다면 구체적인 질문을 요청하세요.
        """.format(context=context)
        else:
            system_message = """
            당신은 신생아중환자실(NICU)에서 근무하는 의료진과 동등한 수준의 전문 지식을 갖추고 있는 챗봇입니다.
            
            필요한 혈액 검사 값:
            1. 혈당 (Glucose, mg/dL) - 정상 범위: 70-100 mg/dL
            2. 알부민 (Albumin, g/dL) - 정상 범위: 3.4-5.4 g/dL
            3. 혈중요소질소 (BUN, mg/dL) - 정상 범위: 7-20 mg/dL
            4. 인 (Phosphorus, mg/dL) - 정상 범위: 2.5-4.5 mg/dL
            5. 총 단백질 (Total Protein, g/dL) - 정상 범위: 6.0-8.3 g/dL
            
            혈액검사 결과가 제공되면 function call을 사용하여 값을 추출하세요.
            일반적인 질문에는 현재 업로드된 문서가 없으므로 문서를 업로드 한 후 질문을 할 수 있게끔 안내하세요.
            """

        messages.append({"role": "system", "content": system_message})

        # 채팅 히스토리 보관
        for message in chat_history:
            messages.append({
                "role": "user" if message["type"] == "user" else "assistant",
                "content": message["content"]
            })

        # 현재 사용자 메시지 추가
        messages.append({"role": "user", "content": user_message})

        # function calling 정의
        functions =[
            {
                "type": "function",
                "function" : {
                    "name": "extract_blood_test_values",
                    "description": "환자의 혈액 검사 값을 추출합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "glucose": {
                                "type" : "number",
                                "description": "혈당 (Glucose) 수치 (mg/dL)"
                            },
                             "albumin": {
                                "type": "number",
                                "description": "알부민 (Albumin) 수치 (g/dL)"
                            },
                            "bun": {
                                "type": "number",
                                "description": "혈중요소질소 (BUN) 수치 (mg/dL)"
                            },
                            "phosphorus": {
                                "type": "number",
                                "description": "인 (Phosphorus) 수치 (mg/dL)"
                            },
                            "total_protein": {
                                "type": "number",
                                "description": "총 단백질 (Total Protein) 수치 (g/dL)"
                            }
                        },
                        "required": []
                    }
                }
            }
        ]

        # API 호출
        response = openai.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            tools=functions,
            tool_choice="auto"
        )

        assistant_message = response.choices[0].message

        # 추출된 값 확인
        extracted_values = {}
        llm_response_text = ""

        # tool calls 처리
        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                if tool_call.function.name == "extract_blood_test_values":
                    try:
                        function_args = json.loads(tool_call.function.arguments)

                        # 추출된 값 저장
                        for key, value in function_args.items():
                            if key in blood_test_mapping and value is not None:
                                extracted_values[key] = value
                    except json.JSONDecodeError:
                        logger.error("Function arguments JSON 파싱 오류")

        # LLM 응답 텍스트
        llm_response_text = assistant_message.content if assistant_message.content else "혈액 검사 결과를 분석 중입니다."

        return extracted_values, llm_response_text
    
    except Exception as e:
        logger.exception(f"OpenAI API 처리 중 오류: {str(e)}")
        return {}, "죄송합니다. 메시지 처리 중 오류가 발생했습니다."