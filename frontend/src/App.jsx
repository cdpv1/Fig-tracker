import { useState, useEffect } from 'react'
import FigureCard from './components/FigureCard'
import './App.css'
import { Container, Grid, Modal, SimpleGrid, Title } from '@mantine/core'
import FigureModal from './components/FigureModal'

function App() {
  const [collection, setCollection] = useState([])
  const [selectedFigure, setSelectedFigure] = useState(null)

  useEffect(() => {
    fetch('/api/collection')
      .then((response) => response.json())
      .then((data) => setCollection(data))
      .catch((error) => console.error('Error fetching collection:', error))
  }, [])

  return (
    <Container size="xl" py="xl">
      <Title order={1} mb="lg">Fig Tracker</Title>
      <SimpleGrid cols={{ base: 1, sm: 2, md: 3, lg: 4 }} spacing="lg">
        {collection.map((figure) => (
            <FigureCard key={figure.mfc_id} figure={figure} onClick={() => setSelectedFigure(figure)} />
        ))}
      </SimpleGrid>
      <FigureModal selectedFigure={selectedFigure} opened={selectedFigure !== null} onClose={() => setSelectedFigure(null)}></FigureModal>
    </Container>
  )
}
export default App
