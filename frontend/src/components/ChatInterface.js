import React, { useState, useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import InputArea from './InputArea';
import { sendMessage } from '../services/api';
import './ChatInterface.css';

const ChatInterface = ({ messages, setMessages, loading, setLoading }) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  // 메시지 자동 스크롤
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 메시지 전송 처리
  const handleSendMessage = async (event) => {
    event.preventDefault();
    
    if (!input.trim() || loading) return;
    
    // 사용자 메시지 추가
    const userMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: input
    };
    
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setInput('');
    setLoading(true);
    
    try {
      // 백엔드 API에 메시지 전송
      const chatHistory = messages.map(msg => ({
        type: msg.type,
        content: msg.content
      }));
      
      const response = await sendMessage(input, chatHistory);
      
      // 응답 추가
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.response,
        prediction: response.prediction
      };
      
      setMessages(prevMessages => [...prevMessages, assistantMessage]);
    } catch (error) {
      console.error('에러 발생:', error);
      
      // 에러 메시지 추가
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: '죄송합니다. 요청을 처리하는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.'
      };
      
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-interface">
      <div className="messages-container">
        {messages.map(message => (
          <MessageBubble 
            key={message.id} 
            message={message} 
          />
        ))}
        {loading && (
          <div className="loading-indicator">
            <div className="loading-dot"></div>
            <div className="loading-dot"></div>
            <div className="loading-dot"></div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <InputArea 
        input={input} 
        setInput={setInput} 
        handleSendMessage={handleSendMessage} 
        loading={loading}
      />
    </div>
  );
};

export default ChatInterface;