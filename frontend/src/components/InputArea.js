import React from 'react';
import './InputArea.css';

const InputArea = ({ input, setInput, handleSendMessage, loading }) => {
    // 텍스트 영역 리사이징
    const handleTextareaChange = (e) => {
        setInput(e.target.value);

        // 자동 높이 조절
        e.target.style.height = 'auto';
        e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
    };

    // Enter 키로 전송, Shift+Enter 키로 줄 바꿈
    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage(e);
        }
    };

    return (
        <div className="input-area">
            <form onSubmit={handleSendMessage}>
                <div className="input-container">
                    <textarea
                        value={input}
                        onChange={handleTextareaChange}
                        onKeyDown={handleKeyDown}
                        placeholder="검색하고자 하는 내용을 입력해주세요."
                        disabled={loading}
                        rows={1}
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() || loading}
                        className={loading ? 'loading' : ''}
                    >
                        {loading ? '전송 중...' : '전송'}
                    </button>
                </div>
                <div className="help-text">
                    Shift+Enter로 줄 바꿈 | Enter로 전송
                </div>
            </form>
        </div>
    );
};

export default InputArea;