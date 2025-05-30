import React, { useState , useEffect } from 'react';
import './App.css';
import ChatInterface from './components/ChatInterface';
import GuidelineUploader from './components/GuidelineUploader';

function App() {
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        // Welcome message 표시
        const initialMessage = {
            id: 'welcome',
            type: 'assistant',
            content: "검색을 원하는 문서를 먼저 업로드 해주신 후에 이용해 주시기 바랍니다."
        };
        setMessages([initialMessage]);
    }, []);

    return (
        <div className="App">
            <header className="App-header">
                <h1>Medvise</h1>
                <p>RAG based Chat-bot</p>
            </header>
            <main>
                <GuidelineUploader />
                <ChatInterface
                    messages={messages}
                    setMessages={setMessages}
                    loading={loading}
                    setLoading={setLoading}
                />
            </main>
            <footer>
                <p> Medvise는 언제나 실수를 할 수 있습니다.</p>
            </footer>
        </div>
    );
}

export default App;