import axios from 'axios';

// API 기본 경로 설정
const API_BASE_URL = '/api';

// 기본 axios 인스턴스 생성
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000, // 30초 타임아웃
});


/**
 * 사용자 메시지를 서버에 전송
 * @param {string} message - 사용자 메시지
 * @param {Array} history - 대화 이력
 * @returns {Promise} - 서버 응답
 */
export const sendMessage = async (message, history) => {
    try {
        const response = await apiClient.post('/chat', {
            message,
            history,
        });

        return response.data;
    } catch (error) {
        console.error('API 오류:', error);

        // 에러 처리
        if (error.response) {
            // 서버가 응답을 반환했지만, 오류 상태 코드가 있음
            console.error('응답 오류:', error.response.data);
            throw new Error(error.response.data.error || '서버 오류가 발생했습니다.');
        } else if (error.request) {
            // 요청이 전송되었지만 응답을 받지 못함
            console.error('응답 없음:', error.request);
            throw new Error('서버에서 응답이 없습니다. 네트워크 연결을 확인하세요.')
        } else {
            // 요청 설정 중 오류 발생
            console.error('요청 오류:', error.message);
            throw new Error('요청을 설정하는 중 오류가 발생했습니다.');
        }
    }
};

/**
 * 서버 상태 확인
 * @returns {Promise} - 서버 상태
 */
export const checkServerHealth = async () => {
    try {
        const response = await apiClient.get('/health');
        return response.data;
    } catch (error) {
        console.error('서버 상태 확인 오류:', error);
        throw new Error('서버 상태를 확인할 수 없습니다.');
    }
};

/**
 * 진료 지침 목록 조회
 * @returns {Promise} - 진료 지침 목록
 */
export const getGuidelines = async () => {
    try {
        const response = await apiClient.get('/guidelines');
        return response.data;
    } catch (error) {
        console.error('진료 지침 조회 오류:', error);
        throw new Error('진료 지침 목록을 불러올 수 없습니다.');
    }
};

/**
 * 새 진료 지침 업로드
 * @param {FormData} formData - 파일 포함 폼 데이터
 * @returns {Promise} - 업로드 결과
 */
export const uploadGuideline = async (formData) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/guidelines`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    } catch (error) {
        console.error('진료 지침 업로드 오류:', error);
        throw new Error('진료 지침을 업로드할 수 없습니다.');
    }
};

/**
 * 진료 지침 삭제
 * @param {string} filename - 삭제할 파일 이름
 * @returns {Promise} - 삭제 결과
 */
export const deleteGuideline = async (filename) => {
    try {
        const response = await apiClient.delete(`/guidelines/${filename}`);
        return response.data;
    } catch (error) {
        console.error('진료 지침 삭제 오류:', error);
        throw new Error('진료 지침을 삭제할 수 없습니다.');
    }
};

/**
 * 특정 진료 지침 조회
 * @param {string} filename - 조회할 파일 이름
 * @returns {Promise} - 파일 내용
 */
export const getGuidelineContent = async (filename) => {
    try{
        const response = await apiClient.get(`/guidelines/${filename}`);
        return response.data;
    } catch (error) {
        console.error('진료 지침 내용 조회 오류:', error);
        throw new Error('진료 지침 내용을 불러올 수 없습니다.');
    }
};