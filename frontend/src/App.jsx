import React, { useState, useEffect } from 'react';
import { Bell, Clock, CheckCircle, XCircle, Phone, MessageSquare, BookOpen, AlertCircle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const SupervisorDashboard = () => {
  const [activeTab, setActiveTab] = useState('pending');
  const [pendingRequests, setPendingRequests] = useState([]);
  const [resolvedRequests, setResolvedRequests] = useState([]);
  const [knowledgeBase, setKnowledgeBase] = useState([]);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [answerText, setAnswerText] = useState('');
  const [notification, setNotification] = useState(null);
  const [loading, setLoading] = useState(false);

  // Fetch data from backend
  const fetchData = async () => {
    try {
      // Fetch pending requests
      const pendingRes = await fetch(`${BACKEND_URL}/api/requests?status=pending`);
      const pendingData = await pendingRes.json();
      setPendingRequests(pendingData.requests || []);

      // Fetch resolved requests
      const resolvedRes = await fetch(`${BACKEND_URL}/api/requests?status=resolved`);
      const resolvedData = await resolvedRes.json();
      setResolvedRequests(resolvedData.requests || []);

      // Fetch knowledge base
      const kbRes = await fetch(`${BACKEND_URL}/api/knowledge`);
      const kbData = await kbRes.json();
      setKnowledgeBase(kbData.entries || []);
    } catch (error) {
      console.error('Error fetching data:', error);
      showNotification('Failed to fetch data from backend', 'error');
    }
  };

  useEffect(() => {
    fetchData();
    // Poll every 5 seconds for new requests
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const handleSubmitAnswer = async (requestId) => {
    if (!answerText.trim()) {
      showNotification('Please enter an answer', 'error');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/requests/${requestId}/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answer: answerText, supervisor_id: 'supervisor' })
      });

      if (response.ok) {
        showNotification('Answer sent and knowledge base updated!');
        setAnswerText('');
        setSelectedRequest(null);
        fetchData(); // Refresh data
      } else {
        showNotification('Failed to submit answer', 'error');
      }
    } catch (error) {
      showNotification('Error submitting answer', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkUnresolved = async (requestId) => {
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/requests/${requestId}/unresolved`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        showNotification('Request marked as unresolved', 'error');
        setSelectedRequest(null);
        fetchData();
      } else {
        showNotification('Failed to mark unresolved', 'error');
      }
    } catch (error) {
      showNotification('Error marking unresolved', 'error');
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    const diff = Date.now() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-4 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Phone className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Frontdesk AI Supervisor</h1>
                <p className="text-sm text-gray-500">Human-in-the-Loop Management System</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 bg-red-50 px-3 py-2 rounded-lg">
                <Bell className="w-5 h-5 text-red-600" />
                <span className="font-semibold text-red-600">{pendingRequests.length}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Notification Toast */}
      {notification && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg ${
          notification.type === 'success' ? 'bg-green-500' : 
          notification.type === 'error' ? 'bg-red-500' : 'bg-blue-500'
        } text-white`}>
          {notification.message}
        </div>
      )}

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        <div className="flex space-x-1 bg-white p-1 rounded-lg shadow-sm">
          <button
            onClick={() => setActiveTab('pending')}
            className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-md transition ${
              activeTab === 'pending' 
                ? 'bg-blue-600 text-white' 
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Clock className="w-4 h-4" />
            <span className="font-medium">Pending ({pendingRequests.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('resolved')}
            className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-md transition ${
              activeTab === 'resolved' 
                ? 'bg-blue-600 text-white' 
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <CheckCircle className="w-4 h-4" />
            <span className="font-medium">History ({resolvedRequests.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('knowledge')}
            className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-md transition ${
              activeTab === 'knowledge' 
                ? 'bg-blue-600 text-white' 
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <BookOpen className="w-4 h-4" />
            <span className="font-medium">Knowledge Base ({knowledgeBase.length})</span>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6 pb-12">
        {activeTab === 'pending' && (
          <div className="space-y-4">
            {pendingRequests.length === 0 ? (
              <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">All caught up!</h3>
                <p className="text-gray-500">No pending requests at the moment.</p>
              </div>
            ) : (
              pendingRequests.map(request => (
                <div key={request.id} className="bg-white rounded-lg shadow-sm p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <AlertCircle className="w-5 h-5 text-orange-500" />
                        <span className="text-xs font-medium text-orange-600 uppercase tracking-wide">
                          Needs Response
                        </span>
                        <span className="text-xs text-gray-400">•</span>
                        <span className="text-xs text-gray-500">{formatTime(request.created_at)}</span>
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        "{request.question}"
                      </h3>
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <div className="flex items-center space-x-1">
                          <Phone className="w-4 h-4" />
                          <span>{request.caller_name}</span>
                        </div>
                        <span>•</span>
                        <span>{request.caller_phone}</span>
                        <span>•</span>
                        <span className="text-xs text-gray-400">Call ID: {request.call_id}</span>
                      </div>
                    </div>
                  </div>

                  {selectedRequest === request.id ? (
                    <div className="mt-4 space-y-3">
                      <textarea
                        value={answerText}
                        onChange={(e) => setAnswerText(e.target.value)}
                        placeholder="Type your answer here..."
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        rows="4"
                      />
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleSubmitAnswer(request.id)}
                          disabled={loading}
                          className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition font-medium disabled:opacity-50"
                        >
                          {loading ? 'Submitting...' : 'Submit Answer & Notify Customer'}
                        </button>
                        <button
                          onClick={() => handleMarkUnresolved(request.id)}
                          disabled={loading}
                          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                        >
                          Mark Unresolved
                        </button>
                        <button
                          onClick={() => {
                            setSelectedRequest(null);
                            setAnswerText('');
                          }}
                          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => setSelectedRequest(request.id)}
                      className="mt-4 w-full bg-blue-50 text-blue-600 px-4 py-2 rounded-lg hover:bg-blue-100 transition font-medium"
                    >
                      Respond to Request
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'resolved' && (
          <div className="space-y-4">
            {resolvedRequests.map(request => (
              <div key={request.id} className="bg-white rounded-lg shadow-sm p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <CheckCircle className="w-5 h-5 text-green-500" />
                      <span className="text-xs font-medium uppercase tracking-wide text-green-600">
                        RESOLVED
                      </span>
                      <span className="text-xs text-gray-400">•</span>
                      <span className="text-xs text-gray-500">{formatTime(request.resolved_at)}</span>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      "{request.question}"
                    </h3>
                    <div className="flex items-center space-x-4 text-sm text-gray-600 mb-3">
                      <span>{request.caller_name}</span>
                      <span>•</span>
                      <span>{request.caller_phone}</span>
                    </div>
                    {request.answer && (
                      <div className="bg-gray-50 rounded-lg p-3 mt-3">
                        <p className="text-sm text-gray-700 font-medium">Answer provided:</p>
                        <p className="text-sm text-gray-600 mt-1">{request.answer}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'knowledge' && (
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="flex items-start space-x-3">
                <BookOpen className="w-5 h-5 text-blue-600 mt-0.5" />
                <div>
                  <h3 className="text-sm font-semibold text-blue-900 mb-1">Knowledge Base</h3>
                  <p className="text-sm text-blue-700">
                    These answers are automatically learned from supervisor responses and used by the AI for future calls.
                  </p>
                </div>
              </div>
            </div>
            {knowledgeBase.map(item => (
              <div key={item.id} className="bg-white rounded-lg shadow-sm p-6">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-lg font-semibold text-gray-900 flex-1">
                    "{item.question}"
                  </h3>
                  <div className="flex items-center space-x-2 text-sm text-gray-500">
                    <MessageSquare className="w-4 h-4" />
                    <span>{item.usage_count} uses</span>
                  </div>
                </div>
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <p className="text-sm text-gray-700">{item.answer}</p>
                </div>
                <div className="mt-3 text-xs text-gray-500">
                  Learned {formatTime(item.learned_at)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SupervisorDashboard;