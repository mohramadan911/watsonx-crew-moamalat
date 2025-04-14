import React, { useState } from 'react';

const ChatUI = () => {
  const [message, setMessage] = useState('');
  const [file, setFile] = useState(null);

  const handleUpload = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = () => {
    console.log('Prompt:', message);
    console.log('File:', file);
    // TODO: trigger backend upload and processing
  };

  return (
    <div className="bg-white p-4 rounded-xl shadow">
      <h2 className="text-lg font-semibold mb-2">Upload PDF and Chat</h2>
      <input type="file" accept="application/pdf" onChange={handleUpload} className="mb-2" />
      <textarea
        className="w-full border rounded p-2 mb-2"
        rows={4}
        placeholder="Ask something about the document..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
      />
      <button
        onClick={handleSubmit}
        className="bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
      >
        Run Analysis
      </button>
    </div>
  );
};

export default ChatUI;
