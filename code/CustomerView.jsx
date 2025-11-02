import React, { useState, useEffect } from 'react';
import { serviceRequestAPI, tableAPI } from '../services/api';

const CustomerView = () => {
  const [tables, setTables] = useState([]);
  const [selectedTable, setSelectedTable] = useState('');
  const [requestType, setRequestType] = useState('WAITER');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadTables();
  }, []);

  const loadTables = async () => {
    try {
      const { data } = await tableAPI.getAll();
      setTables(data.results || data);
    } catch (error) {
      console.error('Error loading tables:', error);
    }
  };

  const handleSubmitRequest = async (e) => {
    e.preventDefault();
    
    if (!selectedTable) {
      setMessage('Please select a table');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      await serviceRequestAPI.create({
        table_id: selectedTable,
        request_type: requestType,
        notes: notes,
      });

      setMessage('Request submitted successfully! Staff will be notified.');
      setNotes('');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      setMessage('Error submitting request. Please try again.');
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="customer-view">
      <h2>Restaurant Service</h2>
      
      <form onSubmit={handleSubmitRequest} className="request-form">
        <div className="form-group">
          <label>Select Table:</label>
          <select 
            value={selectedTable} 
            onChange={(e) => setSelectedTable(e.target.value)}
            required
          >
            <option value="">-- Select Table --</option>
            {tables.map((table) => (
              <option key={table.id} value={table.id}>
                Table {table.table_number} (Capacity: {table.capacity})
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Request Type:</label>
          <select 
            value={requestType} 
            onChange={(e) => setRequestType(e.target.value)}
          >
            <option value="WAITER">Call Waiter</option>
            <option value="BILL">Request Bill</option>
            <option value="ORDER">Place Order</option>
            <option value="ASSISTANCE">Need Assistance</option>
          </select>
        </div>

        <div className="form-group">
          <label>Additional Notes:</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Any special requests or notes..."
            rows="4"
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Submitting...' : 'Submit Request'}
        </button>
      </form>

      {message && (
        <div className={`message ${message.includes('Error') ? 'error' : 'success'}`}>
          {message}
        </div>
      )}
    </div>
  );
};

export default CustomerView;
