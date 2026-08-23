import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [figures, setFigures] = useState([])

  useEffect(() => {
    fetch('/api/figures')
      .then((response) => response.json())
      .then((data) => setFigures(data))
      .catch((error) => console.error('Error fetching figures:', error))
  }, [])

  return (
    <div>
      <h1>Fig Tracker</h1>

      {figures.map((figure) => (
        <div key={figure.id}>
          <h2>{figure.name}</h2>
          <p>{figure.scale}</p>
        </div>
      ))}
    </div>
  )
}
export default App
