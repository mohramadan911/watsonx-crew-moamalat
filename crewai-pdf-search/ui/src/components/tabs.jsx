import React from 'react';

const Tabs = ({ activeTab, setActiveTab }) => {
  const tabs = [
    { id: 'chat', label: 'Chat + Upload' },
    { id: 'model', label: 'Model Config' },
    { id: 's3', label: 'S3 Config' },
    { id: 'email', label: 'Email Config' },
  ];

  return (
    <div className="flex space-x-4 border-b">
      {tabs.map(tab => (
        <button
          key={tab.id}
          onClick={() => setActiveTab(tab.id)}
          className={`py-2 px-4 font-medium ${
            activeTab === tab.id ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
};

export default Tabs;
