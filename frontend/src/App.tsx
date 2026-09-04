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
          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            <div className="xl:col-span-3 min-w-0">
              <Dashboard />
            </div>
            <div className="xl:col-span-1 min-w-0">
              <ArchitectureFlow />
            </div>
          </div>
        )}
        
        {activeTab === 'all-traces' && (
          <TracesList evaluatedOnly={false} />
        )}

        {activeTab === 'evaluated' && (
          <TracesList evaluatedOnly={true} />
        )}
        
        {activeTab === 'batch' && (
          <BatchEvaluation />
        )}
      </main>
    </div>
  )
}

export default App
