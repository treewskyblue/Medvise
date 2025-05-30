# MEDVISE
Medvise는 의료인을 위한 RAG 기반의 챗봇입니다.  

_(2025 전북대학교 SW경진대회 출품작)_

## 구성원
- 박서현, 전북대학교 바이오메디컬공학부(헬스케어정보공학)
- 김희진, 전북대학교 바이오메디컬공학부(헬스케어기기공학)
- 홍승재, 전북대학교 바이오메디컬공학부(헬스케어정보공학)

## 시연영상

## 프로그램 실행 시 유의사항
- Docker 프로그램이 필요합니다.
- OpenAI API 키를 별도로 입력해야 합니다. `docker-compose.yml` 파일의 'chatbot-backend' section에서 "YOUR_API_KEY_HERE" 에다가 API 키를 입력한 후 실행하시기 바랍니다.

## 프로젝트 구조
```bash
Medvise
├─chatbot-backend
│  ├─utils
│  │   ├─document_loader.py
│  │   ├─embeddings.py
│  │   ├─llm_processor.py
│  │   └─rag_engine.py
│  ├─app.py
│  ├─Dockerfile
│  └─requirements.txt
├─frontend
│  ├─public
│  │   ├─index.html
│  │   └─manifest.json
│  ├─src
│  │   ├─components
│  │   │   ├─Chatinterface.css
│  │   │   ├─Chatinterface.js
│  │   │   ├─GuidelineUploader.css
│  │   │   ├─GuidelineUploader.js
│  │   │   ├─InputArea.css
│  │   │   ├─InputArea.js
│  │   │   ├─MessageBubble.css
│  │   │   └─MessageBubble.js
│  │   ├─services
│  │   │   └─api.js
│  │   ├─App.css
│  │   ├─App.js
│  │   ├─index.css
│  │   └─index.js
│  ├─Dockerfile
│  ├─nginx.conf
│  └─package.json
├─ml-backend
│  ├─create_model_in_container.py
│  ├─Dockerfile
│  ├─init.sh
│  ├─main.py
│  ├─model.pkl
│  ├─requirements.txt
│  ├─scaler.pkl
│  └─TPN_ML_OMITTED.xlsx
└─docker-compose.yml
```
