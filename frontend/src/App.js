import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const App = () => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [userId] = useState(() => 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9));
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [rateLimitWarning, setRateLimitWarning] = useState(false);
  const [lastMessageTime, setLastMessageTime] = useState(0);
  const messagesEndRef = useRef(null);

  // Production optimizations
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Network status monitoring
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  useEffect(() => {
    loadChatHistory();
    initializeUserProfile();
  }, []);

  const loadChatHistory = async () => {
    try {
      const response = await axios.get(`${API}/chat/${userId}`);
      const chatHistory = response.data.reverse();
      
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
    if (!isOnline) {
      alert('אין חיבור לאינטרנט. אנא בדוק את החיבור שלך.');
      return;
    }

    // Rate limiting check
    const now = Date.now();
    if (now - lastMessageTime < 2000) { // 2 seconds minimum between messages
      setRateLimitWarning(true);
      setTimeout(() => setRateLimitWarning(false), 3000);
      return;
    }

    // Message length validation
    if (newMessage.length > 2000) {
      alert('ההודעה ארוכה מדי. אנא שלח הודעה עד 2000 תווים.');
      return;
    }

    const userMessage = {
      id: Date.now() + '_user',
      text: newMessage,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setNewMessage('');
    setIsLoading(true);
    setLastMessageTime(now);

    try {
      const response = await axios.post(`${API}/chat`, {
        user_id: userId,
        message: newMessage
      }, {
        timeout: 30000, // 30 second timeout
        headers: {
          'Content-Type': 'application/json'
        }
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
      
      let errorMessage = 'מצטער, נכשלתי בשליחת ההודעה. נסה שוב.';
      
      if (error.response?.status === 429) {
        errorMessage = 'שלחת יותר מדי הודעות. אנא המתן רגע ונסה שוב.';
      } else if (error.response?.status >= 500) {
        errorMessage = 'בעיה זמנית בשרת. אנא נסה שוב בעוד רגע.';
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = 'הבקשה ארכה יותר מדי. נסה שוב.';
      } else if (!isOnline) {
        errorMessage = 'אין חיבור לאינטרנט. בדוק את החיבור שלך.';
      }

      const errorMsg = {
        id: Date.now() + '_error',
        text: errorMessage,
        sender: 'ai',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMsg]);
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

  const quickActions = [
    { text: 'שלום! אני רוצה להתחיל להתאמן', icon: '💪' },
    { text: 'איך אני יכול לשפר את התזונה שלי?', icon: '🥗' },
    { text: 'אני צריך מוטיבציה להמשיך', icon: '🔥' },
    { text: 'תן לי תוכנית אימון למתחילים', icon: '🏋️‍♂️' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100" dir="rtl">
      {/* Network Status Banner */}
      {!isOnline && (
        <div className="bg-red-500 text-white text-center py-2">
          אין חיבור לאינטרנט - חלק מהתכונות עלולות לא לעבוד
        </div>
      )}

      {/* Rate Limit Warning */}
      {rateLimitWarning && (
        <div className="bg-yellow-500 text-white text-center py-2">
          אנא המתן רגע בין הודעות
        </div>
      )}

      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3 space-x-reverse">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-lg">💪</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">המאמן הדיגיטלי</h1>
                <p className="text-sm text-gray-500">מאמן הכושר האישי שלך - גרסת פרודקשן</p>
              </div>
            </div>
            <div className="flex items-center">
              <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-xs text-gray-500 mr-2">
                {isOnline ? 'מחובר' : 'לא מחובר'}
              </span>
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
                <p className="text-gray-500 mb-6">מאמן כושר מקצועי מבוסס AI שיעזור לך להגיע ליעדיך</p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
                  {quickActions.map((action, index) => (
                    <button
                      key={index}
                      onClick={() => setNewMessage(action.text)}
                      className="flex items-center justify-center p-3 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg text-blue-700 hover:from-blue-100 hover:to-indigo-100 transition-all duration-200 hover:shadow-md"
                      disabled={isLoading}
                    >
                      <span className="text-xl ml-2">{action.icon}</span>
                      <span className="text-sm font-medium">{action.text}</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'} message-bubble`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
                      message.sender === 'user'
                        ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-br-md'
                        : 'bg-gray-50 text-gray-800 rounded-bl-md border border-gray-200'
                    } transition-all duration-200`}
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
                <div className="bg-gray-50 rounded-2xl rounded-bl-md px-4 py-3 max-w-xs border border-gray-200">
                  <div className="flex items-center space-x-1 space-x-reverse">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <span className="text-xs text-gray-500 mr-2">המאמן מכין תשובה...</span>
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
                  placeholder={isOnline ? "כתוב הודעה..." : "אין חיבור לאינטרנט"}
                  className="w-full px-4 py-3 border border-gray-300 rounded-full resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                  rows="1"
                  disabled={isLoading || !isOnline}
                  maxLength={2000}
                />
                <div className="text-xs text-gray-500 mt-1 px-4">
                  {newMessage.length}/2000 תווים
                </div>
              </div>
              <button
                onClick={sendMessage}
                disabled={!newMessage.trim() || isLoading || !isOnline}
                className="w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-full flex items-center justify-center hover:from-blue-600 hover:to-blue-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                {isLoading ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;