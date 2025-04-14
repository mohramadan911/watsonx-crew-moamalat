import React, { useState } from 'react';
import Tabs from './components/Tabs';
import ChatUI from './components/ChatUI';
import ModelConfig from './components/ModelConfig';
import S3Config from './components/S3Config';
import EmailConfig from './components/EmailConfig';

const App = () => {
  const [activeTab, setActiveTab] = useState('chat');

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <Tabs activeTab={activeTab} setActiveTab={setActiveTab} />
      <div className="mt-4">
        {activeTab === 'chat' && <ChatUI />}
        {activeTab === 'model' && <ModelConfig />}
        {activeTab === 's3' && <S3Config />}
        {activeTab === 'email' && <EmailConfig />}
      </div>
    </div>
  );
};

export default App;
