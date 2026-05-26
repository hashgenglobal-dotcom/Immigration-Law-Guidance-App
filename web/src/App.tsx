import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import ChatPage from './pages/ChatPage'
<<<<<<< HEAD
=======
import ScenariosPage from './pages/ScenariosPage'
>>>>>>> features/more-guide
import OfficialUpdatesPage from './pages/OfficialUpdatesPage'
import SourcesPage from './pages/SourcesPage'
import AboutPage from './pages/AboutPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/chat" element={<ChatPage />} />
<<<<<<< HEAD
=======
        <Route path="/scenarios" element={<ScenariosPage />} />
>>>>>>> features/more-guide
        <Route path="/updates" element={<OfficialUpdatesPage />} />
        <Route path="/sources" element={<SourcesPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
