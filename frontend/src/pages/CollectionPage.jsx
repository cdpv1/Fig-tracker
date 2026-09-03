import { useState, useEffect } from 'react'
import FigureCard from '../components/FigureCard.jsx'
import { Container, SimpleGrid, Group, Button, Text, Modal } from '@mantine/core'

// import FigureModal from '../components/FigureModal'
function CollectionPage() {
    const [collection, setCollection] = useState([])
    const [syncing, setSyncing] = useState(false)
    const [syncError, setSyncError] = useState(null)

    // const [selectedFigure, setSelectedFigure] = useState(null)

    useEffect(() => {
        fetch('/api/collection')
            .then((response) => response.json())
            .then((data) => setCollection(data))
            .catch((error) => console.error('Error fetching collection:', error))
    }, [])

    const handleSync = async () => {
        try {
            setSyncing(true)
            setSyncError(null)
            const response = await fetch('/api/mfc/cdpv3/collection/sync', {
                method: 'POST',
            })

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`)
            }

            const collectionResponse = await fetch('/api/collection')

            if (!collectionResponse.ok) {
                throw new Error(`HTTP ${collectionResponse.status}`)
            }

            const collectionData = await collectionResponse.json()

            setCollection(collectionData)
        } catch (error) {
            console.error('Error syncing collection:', error)
            setSyncError(error.message)
        } finally {
            setSyncing(false)
        }
    }

    return (
        <Container fluid>
            <Group justify="space-between" align="center" mb="md">
                <Text c="dimmed">
                    {collection.length} figures
                </Text>

                <Group>
                    <Button onClick={handleSync} loading={syncing}>
                        Sync MFC
                    </Button>
                </Group>
            </Group>
            <SimpleGrid cols={{ base: 1, sm: 2, md: 3, lg: 4, xl: 8 }} spacing="lg">
                {collection.map((figure) => (
                    <FigureCard key={figure.mfc_id} figure={figure} />
                ))}
            </SimpleGrid>
            {/* <FigureModal selectedFigure={selectedFigure} opened={selectedFigure !== null} onClose={() => setSelectedFigure(null)}></FigureModal> */}
            <Modal
                opened={syncing}
                onClose={() => { }}
                closeOnClickOutside={false}
                closeOnEscape={false}
                withCloseButton={false}
                title="Syncing MFC"
            ></Modal>
        </Container>
    )
}

export default CollectionPage