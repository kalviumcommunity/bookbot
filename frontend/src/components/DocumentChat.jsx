import React, { useState, useRef, useEffect } from 'react';
import './DocumentChat.css';
import apiService from '../services/api';

const DocumentChat = ({ content, onBack }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  useEffect(() => {
    // Welcome message
    setMessages([{ 
      role: 'model', 
      text: 'Hi! I have read the document you uploaded. Feel free to ask me anything about it!' 
    }]);
  }, []);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput('');
    
    const newHistory = [...messages, { role: 'user', text: userMessage }];
    setMessages(newHistory);
    setIsTyping(true);

    try {
      // Gemini API strictly requires that the history starts with a user message.
      // We must filter out the initial welcome 'model' message from the history array.
      const apiHistory = messages.filter((msg, idx) => !(idx === 0 && msg.role === 'model'));
      
      const response = await apiService.sendChatMessage(content, userMessage, apiHistory);
      setMessages([...newHistory, { role: 'model', text: response.reply }]);
    } catch (error) {
      setMessages([...newHistory, { role: 'model', text: 'Sorry, there was an error processing your request. Please try again.' }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <button className="back-btn" onClick={onBack}>← Back to Summary</button>
        <h2>💬 Chat with Document</h2>
      </div>
      
      <div className="chat-messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message-wrapper ${msg.role}`}>
            <div className={`message bubble-${msg.role}`}>
              {msg.text}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="message-wrapper model">
            <div className="message bubble-model typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask a question about your notes..."
          disabled={isTyping}
        />
        <button 
          onClick={handleSend} 
          disabled={isTyping || !input.trim()}
          className="send-btn"
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default DocumentChat;
