import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const App = () => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [userId] = useState(() => 'user_' + Date.now()); // Simple user ID generation
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Load chat history on component mount
    loadChatHistory();
    // Initialize user profile
    initializeUserProfile();
  }, []);

  const loadChatHistory = async () => {
    try {
      const response = await axios.get(`${API}/chat/${userId}`);
      const chatHistory = response.data.reverse(); // Reverse to show oldest first
      
      // Convert to message format
      const formattedMessages = [];
      chatHistory.forEach(chat => {
        formattedMessages.push({
          id: chat.id + '_user',
          text: chat.message,
          sender: 'user',
          timestamp: new Date(chat.timestamp)
        });
        formattedMessages.push({
          id: chat.id + '_ai',
          text: chat.response,
          sender: 'ai',
          timestamp: new Date(chat.timestamp)
        });
      });
      
      setMessages(formattedMessages);
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  const initializeUserProfile = async () => {
    try {
      await axios.post(`${API}/profile`, {
        user_id: userId,
        name: 'משתמש',
        fitness_level: 'beginner',
        goals: []
      });
    } catch (error) {
      console.error('Error initializing profile:', error);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim()) return;

    const userMessage = {
      id: Date.now() + '_user',
      text: newMessage,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setNewMessage('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API}/chat`, {
        user_id: userId,
        message: newMessage
      });

      const aiMessage = {
        id: Date.now() + '_ai',
        text: response.data.response,
        sender: 'ai',
        timestamp: new Date(response.data.timestamp)
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now() + '_error',
        text: 'מצטער, נכשלתי בשליחת ההודעה. נסה שוב.',
        sender: 'ai',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('he-IL', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100" dir="rtl">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center space-x-3 space-x-reverse">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-lg">💪</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">המאמן הדיגיטלי</h1>
              <p className="text-sm text-gray-500">מאמن הכושר האישי שלך</p>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Container */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="bg-white rounded-lg shadow-lg overflow-hidden h-[calc(100vh-200px)] flex flex-col">
          
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🤖</div>
                <h3 className="text-xl font-semibold text-gray-700 mb-2">ברוך הבא למאמן הדיגיטלי!</h3>
                <p className="text-gray-500">שלח הודעה כדי להתחיל את המסע שלך לכושר</p>
                <div className="mt-6 flex flex-wrap gap-2 justify-center">
                  <button
                    onClick={() => setNewMessage('שלום! אני רוצה להתחיל להתאמן')}
                    className="px-4 py-2 bg-blue-100 text-blue-700 rounded-full text-sm hover:bg-blue-200 transition-colors"
                  >
                    💪 רוצה להתחיל להתאמן
                  </button>
                  <button
                    onClick={() => setNewMessage('איך אני יכול לשפר את התזונה שלי?')}
                    className="px-4 py-2 bg-green-100 text-green-700 rounded-full text-sm hover:bg-green-200 transition-colors"
                  >
                    🥗 עצות תזונה
                  </button>
                  <button
                    onClick={() => setNewMessage('אני צריך מוטיבציה')}
                    className="px-4 py-2 bg-purple-100 text-purple-700 rounded-full text-sm hover:bg-purple-200 transition-colors"
                  >
                    🔥 מוטיבציה
                  </button>
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
                      message.sender === 'user'
                        ? 'bg-blue-500 text-white rounded-br-md'
                        : 'bg-gray-100 text-gray-800 rounded-bl-md'
                    }`}
                  >
                    <div className="whitespace-pre-wrap text-sm leading-relaxed">
                      {message.text}
                    </div>
                    <div
                      className={`text-xs mt-2 ${
                        message.sender === 'user' ? 'text-blue-100' : 'text-gray-500'
                      }`}
                    >
                      {formatTimestamp(message.timestamp)}
                    </div>
                  </div>
                </div>
              ))
            )}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-3 max-w-xs">
                  <div className="flex items-center space-x-1 space-x-reverse">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex items-end space-x-2 space-x-reverse">
              <div className="flex-1">
                <textarea
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="כתוב הודעה..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-full resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows="1"
                  disabled={isLoading}
                />
              </div>
              <button
                onClick={sendMessage}
                disabled={!newMessage.trim() || isLoading}
                className="w-12 h-12 bg-blue-500 text-white rounded-full flex items-center justify-center hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;