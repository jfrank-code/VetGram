import { useState } from 'react'
import Landing from './components/Landing/Landing.jsx'
import ChatApp from './components/ChatApp/ChatApp.jsx'

export default function App() {
  const [view, setView] = useState('landing')

  if (view === 'landing') {
    return <Landing onLaunch={() => setView('app')} />
  }

  return <ChatApp onBack={() => setView('landing')} />
}
