import { Route, Routes } from 'react-router-dom'
import './App.css'
import CollectionPage from './pages/CollectionPage'
import FigurePage from './pages/FigurePage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<CollectionPage />}></Route>
      <Route path="/figures/:mfc_id" element={<FigurePage />} />
    </Routes>
  )
}
export default App
