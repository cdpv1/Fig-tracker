import { useState, useEffect } from 'react'
import FigureCard from '../components/FigureCard.jsx'
import { Container, SimpleGrid, Title } from '@mantine/core'

// import FigureModal from '../components/FigureModal'
function CollectionPage() {
    const [collection, setCollection] = useState([])

    // const [selectedFigure, setSelectedFigure] = useState(null)

    useEffect(() => {
        fetch('/api/collection')
            .then((response) => response.json())
            .then((data) => setCollection(data))
            .catch((error) => console.error('Error fetching collection:', error))
    }, [])

    return (
        <Container fluid>
            <SimpleGrid cols={{ base: 1, sm: 2, md: 3, lg: 4, xl: 8 }} spacing="lg">
                {collection.map((figure) => (
                    <FigureCard key={figure.mfc_id} figure={figure} />
                ))}
            </SimpleGrid>
            {/* <FigureModal selectedFigure={selectedFigure} opened={selectedFigure !== null} onClose={() => setSelectedFigure(null)}></FigureModal> */}
        </Container>
    )
}

export default CollectionPage