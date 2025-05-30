import React, { useState, useEffect } from 'react';
import './GuidelineUploader.css';
import { uploadGuideline, getGuidelines, deleteGuideline } from '../services/api';

const GuidelineUploader = () => {
  const [file, setFile] = useState(null);
  const [guidelines, setGuidelines] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  // 지침 목록 로드
  useEffect(() => {
    fetchGuidelines();
  }, []);

  const fetchGuidelines = async () => {
    try {
      const response = await getGuidelines();
      setGuidelines(response.guidelines || []);
    } catch (error) {
      console.error('진료 지침 로드 오류:', error);
      setError('진료 지침을 불러올 수 없습니다.');
    }
  };

  // 파일 선택 처리
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setError('');
  };

  // 파일 업로드 처리
  const handleUpload = async () => {
    if (!file) {
      setError('파일을 선택해 주세요.');
      return;
    }

    // 허용된 파일 유형 검사
    const allowedTypes = ['.txt', '.md', '.markdown', '.pdf'];
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
      setError('지원되는 파일 형식: .txt, .md, .markdown, .pdf');
      return;
    }

    setUploading(true);
    setError('');
    setSuccessMessage('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      await uploadGuideline(formData);
      
      setSuccessMessage('진료 지침이 성공적으로 업로드되었습니다.');
      setFile(null);
      // 파일 입력 초기화
      document.getElementById('guideline-file').value = '';
      // 지침 목록 갱신
      fetchGuidelines();
    } catch (error) {
      console.error('업로드 오류:', error);
      setError('파일 업로드 중 오류가 발생했습니다.');
    } finally {
      setUploading(false);
    }
  };

  // 지침 삭제 처리
  const handleDelete = async (filename) => {
    if (!window.confirm(`"${filename}" 지침을 삭제하시겠습니까?`)) {
      return;
    }

    try {
      await deleteGuideline(filename);
      setSuccessMessage(`"${filename}" 지침이 삭제되었습니다.`);
      // 지침 목록 갱신
      fetchGuidelines();
    } catch (error) {
      console.error('삭제 오류:', error);
      setError('지침 삭제 중 오류가 발생했습니다.');
    }
  };

  // 바이트 단위를 읽기 쉬운 형식으로 변환
  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    else return (bytes / 1048576).toFixed(1) + ' MB';
  };

  const togglePanel = () => {
    setIsOpen(!isOpen);
  };

  return (
    <div className="guideline-uploader">
      <div className="uploader-header" onClick={togglePanel}>
        <h3>진료 지침 관리</h3>
        <span className={`toggle-icon ${isOpen ? 'open' : ''}`}>▼</span>
      </div>
      
      {isOpen && (
        <div className="uploader-content">
          <div className="upload-section">
            <input
              type="file"
              id="guideline-file"
              accept=".txt,.md,.markdown,.pdf"
              onChange={handleFileChange}
              disabled={uploading}
            />
            <button 
              onClick={handleUpload} 
              disabled={!file || uploading}
              className={uploading ? 'loading' : ''}
            >
              {uploading ? '업로드 중...' : '업로드'}
            </button>
          </div>
          
          {error && <p className="error-message">{error}</p>}
          {successMessage && <p className="success-message">{successMessage}</p>}
          
          <div className="guidelines-list">
            <h4>업로드된 진료 지침 ({guidelines.length})</h4>
            {guidelines.length === 0 ? (
              <p className="no-guidelines">업로드된 진료 지침이 없습니다.</p>
            ) : (
              <ul>
                {guidelines.map((guideline, index) => (
                  <li key={index} className="guideline-item">
                    <div className="guideline-info">
                      <span className="guideline-name">{guideline.filename}</span>
                      <span className="guideline-size">{formatFileSize(guideline.size)}</span>
                    </div>
                    <button 
                      className="delete-btn" 
                      onClick={() => handleDelete(guideline.filename)}
                      title="삭제"
                    >
                      ×
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          
          <div className="guidelines-help">
            <p>
              <strong>지원 형식:</strong> .txt, .md, .markdown, .pdf
            </p>
            <p>
              <strong>사용 방법:</strong> 업로드된 진료 지침은 챗봇이 자동으로 참고하여 영양소 계산 시 활용합니다.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default GuidelineUploader;