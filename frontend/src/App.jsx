import { useState, useEffect } from 'react'
import FigureCard from './components/FigureCard'
import './App.css'
import { Container, Grid, Modal, SimpleGrid, Title } from '@mantine/core'

function App() {
  const [collection, setCollection] = useState([])
  const [selectedFigure, setSelectedFigure] = useState(null)
  const sizeDisplay = selectedFigure?.scale
  ? `${selectedFigure.scale} Scale`
  : selectedFigure?.height_mm
    ? `${selectedFigure.height_mm} mm`
    : 'Size unknown'

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
      <Modal opened={selectedFigure !== null} onClose={() => setSelectedFigure(null)}>
        {selectedFigure && (
          <div>
            <img src={selectedFigure.picture_url} alt={selectedFigure.name}/>
            <p>{selectedFigure.name}</p>
            <p>{selectedFigure.manufacturer}</p>
            <p>{selectedFigure.origin}</p>
            <p>{selectedFigure.category}</p>
            <p>{sizeDisplay}</p>
            <p>{selectedFigure.release_date}</p>
            <p>{selectedFigure.rating}</p>
            <p>{selectedFigure.barcode}</p>
          </div>
        )}

      </Modal>
    </Container>
  )
}
export default App
