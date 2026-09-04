import { useState } from 'react'
import { Sidebar } from './components/Sidebar'
import { Dashboard } from './pages/Dashboard'
import { TracesList } from './pages/TracesList'
import { BatchEvaluation } from './pages/BatchEvaluation'
import { ArchitectureFlow } from './components/ArchitectureFlow'

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')

  return (
    <div className="layout">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="main-content">
        {activeTab === 'dashboard' && (
          <div className="grid grid-cols-4 gap-6">
            <div className="col-span-3">
              <Dashboard />
            </div>
            <div className="col-span-1">
              <ArchitectureFlow />
            </div>
          </div>
        )}
        
        {activeTab === 'traces' && (
          <TracesList />
        )}
        
        {activeTab === 'batch' && (
          <BatchEvaluation />
        )}
      </main>
    </div>
  )
}

export default App
