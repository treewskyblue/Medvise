import React from 'react';
import ReactMarkdown from 'react-markdown';
import './MessageBubble.css';

const MessageBubble = ({ message }) => {
    const isUser = message.type === 'user';

    // 결과 테이블 랜더링
    const renderPredictionTable = () => {
        if (!message.prediction) return null;

        return (
            <div className="prediction-table">
                <h4>Recommended TPN</h4>
                <table>
                    <thead>
                        <tr>
                            <th>영양소</th>
                            <th>공급량</th>
                        </tr>
                    </thead>
                    <tbody>
                        {Object.entries(message.prediction).map(([itemKey, value]) => {
                            const unit = itemKey.includes("Calorie") ? "kcal" : "g";
                            return (
                                <tr key={itemKey}>
                                    <td>{itemKey}</td>
                                    <td>{value} {unit}</td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        );
    };

    // 참고 문서 목록 랜더링
    const renderReferences = () => {
        if (!message.references || message.references.length === 0) return null;

        return (
            <div className="references-section">
                <h4>참고 진료 지침</h4>
                <ul className="references-list">
                    {message.references.map((ref, index) => (
                        <li key={index} className="reference-item">
                            <span className="reference-name">
                                {ref.filename || ref.source.split('/').pop()}
                            </span>
                            <div className="reference-excerpt">
                                {ref.content && ref.content.length > 150
                                    ? ref.content.substring(0, 150) + '...'
                                    : ref.content}
                            </div>
                        </li>
                    ))}
                </ul>
            </div>
        );
    };

    return (
        <div className={`message-bubble ${isUser ? 'user' : 'assistant'}`}>
            <div className="message-header">
                <div className="sender">
                    {isUser ? '사용자' : 'Response'}
                </div>
            </div>
            <div className="message-content">
                <ReactMarkdown>{message.content}</ReactMarkdown>
                {!isUser && message.prediction && renderPredictionTable()}
                {!isUser && message.references && renderReferences()}
            </div>
        </div>
    );
};

export default MessageBubble;