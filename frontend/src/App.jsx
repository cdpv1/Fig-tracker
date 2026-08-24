import { useState, useEffect } from 'react'
import FigureCard from './components/FigureCard'
import './App.css'
import { Container, Grid, SimpleGrid, Title } from '@mantine/core'

function App() {
  const [collection, setCollection] = useState([])

  useEffect(() => {
    fetch('/api/collection')
      .then((response) => response.json())
      .then((data) => setCollection(data))
      .catch((error) => console.error('Error fetching collection:', error))
  }, [])

  return (
    <Container size="xl" py="xl">
      <Title order={1} mb="lg">Fig Tracker</Title>
      <SimpleGrid cols={{base:1, sm:2, md:3, lg:4}} spacing="lg">
        {collection.map((figure) => (
          <FigureCard key={figure.mfc_id} figure={figure} />
        ))}
      </SimpleGrid>
    </Container>
  )
}
export default App
