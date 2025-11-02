import React, { useState, useEffect } from 'react';
import { serviceRequestAPI, notificationAPI } from '../services/api';

const StaffDashboard = () => {
  const [requests, setRequests] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
    
    // Poll for new requests every 10 seconds
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [requestsRes, notificationsRes, countRes] = await Promise.all([
        serviceRequestAPI.getPending(),
        notificationAPI.getAll(),
        notificationAPI.getUnreadCount(),
      ]);

      setRequests(requestsRes.data);
      setNotifications(notificationsRes.data.results || notificationsRes.data);
      setUnreadCount(countRes.data.unread_count);
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const handleStatusUpdate = async (requestId, newStatus) => {
    setLoading(true);
    try {
      await serviceRequestAPI.updateStatus(requestId, newStatus);
      await loadData();
    } catch (error) {
      console.error('Error updating status:', error);
      alert('Failed to update request status');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationAPI.markAllRead();
      await loadData();
    } catch (error) {
      console.error('Error marking notifications as read:', error);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      PENDING: '#ff9800',
      ACKNOWLEDGED: '#2196f3',
      IN_PROGRESS: '#9c27b0',
      COMPLETED: '#4caf50',
      CANCELLED: '#f44336',
    };
    return colors[status] || '#757575';
  };

  return (
    <div className="staff-dashboard">
      <header className="dashboard-header">
        <h1>Staff Dashboard</h1>
        <div className="notification-badge">
          <span className="badge">{unreadCount}</span>
          <button onClick={handleMarkAllRead}>Mark All Read</button>
        </div>
      </header>

      <div className="dashboard-content">
        <section className="pending-requests">
          <h2>Pending Service Requests</h2>
          {requests.length === 0 ? (
            <p>No pending requests</p>
          ) : (
            <div className="requests-grid">
              {requests.map((request) => (
                <div key={request.request_id} className="request-card">
                  <div className="request-header">
                    <h3>Table {request.table.table_number}</h3>
                    <span 
                      className="status-badge"
                      style={{ backgroundColor: getStatusColor(request.status) }}
                    >
                      {request.status}
                    </span>
                  </div>
                  
                  <div className="request-body">
                    <p><strong>Type:</strong> {request.request_type}</p>
                    <p><strong>Time:</strong> {new Date(request.created_at).toLocaleTimeString()}</p>
                    {request.notes && <p><strong>Notes:</strong> {request.notes}</p>}
                  </div>
                  
                  <div className="request-actions">
                    <button
                      onClick={() => handleStatusUpdate(request.request_id, 'ACKNOWLEDGED')}
                      disabled={loading || request.status !== 'PENDING'}
                      className="btn-acknowledge"
                    >
                      Acknowledge
                    </button>
                    <button
                      onClick={() => handleStatusUpdate(request.request_id, 'IN_PROGRESS')}
                      disabled={loading || request.status === 'PENDING'}
                      className="btn-progress"
                    >
                      In Progress
                    </button>
                    <button
                      onClick={() => handleStatusUpdate(request.request_id, 'COMPLETED')}
                      disabled={loading}
                      className="btn-complete"
                    >
                      Complete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="notifications-panel">
          <h2>Recent Notifications</h2>
          <div className="notifications-list">
            {notifications.slice(0, 5).map((notification) => (
              <div 
                key={notification.notification_id} 
                className={`notification-item ${notification.is_read ? 'read' : 'unread'}`}
              >
                <h4>{notification.title}</h4>
                <p>{notification.message}</p>
                <span className="notification-time">
                  {new Date(notification.created_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
};

export default StaffDashboard;
