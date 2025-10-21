import React from 'react';

const App = () => {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Translation Management System</h1>
      <p>Welcome to the TMS Dashboard!</p>
      <div style={{ marginTop: '20px' }}>
        <h2>Features:</h2>
        <ul>
          <li>Project Management</li>
          <li>Translation Studio</li>
          <li>Analytics Dashboard</li>
          <li>Real-time Collaboration</li>
        </ul>
      </div>
      <div style={{ marginTop: '20px' }}>
        <button 
          onClick={() => alert('Button clicked!')}
          style={{
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer'
          }}
        >
          Test Button
        </button>
      </div>
    </div>
  );
};

export default App;
