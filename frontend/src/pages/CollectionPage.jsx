import { useState, useEffect } from 'react'
import FigureCard from '../components/FigureCard.jsx'
import { Container, SimpleGrid, Group, Button, Text, Modal, Stack, Loader, Progress } from '@mantine/core'

// import FigureModal from '../components/FigureModal'
function CollectionPage() {
    const [collection, setCollection] = useState([])
    const [syncModalOpen, setSyncModalOpen] = useState(false)
    const [syncStatus, setSyncStatus] = useState(null)
    const [syncProcessed, setSyncProcessed] = useState(0)
    const [syncTotal, setSyncTotal] = useState(0)
    const [syncError, setSyncError] = useState(null)

    // const [selectedFigure, setSelectedFigure] = useState(null)

    useEffect(() => {
        fetch('/api/collection')
            .then((response) => response.json())
            .then((data) => setCollection(data))
            .catch((error) => console.error('Error fetching collection:', error))
    }, [])

    const syncPercent =
        syncTotal > 0
            ? (syncProcessed / syncTotal) * 100
            : 0

    const handleSync = async () => {
        setSyncModalOpen(true)
        setSyncStatus('starting')
        setSyncProcessed(0)
        setSyncTotal(0)
        setSyncError(null)
        try {
            const response = await fetch('/api/mfc/cdpv3/collection/sync', {
                method: 'POST',
            })

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`)
            }

            const { job_id } = await response.json()

            while (true) {
                const statusResponse = await fetch(`/api/sync/${job_id}`)

                if (!statusResponse.ok) {
                    throw new Error(`HTTP ${statusResponse.status}`)
                }

                const job = await statusResponse.json()

                setSyncStatus(job.status)
                setSyncProcessed(job.processed)
                setSyncTotal(job.total)

                if (job.status === 'completed') {
                    break
                }

                if (job.status === 'failed') {
                    throw new Error(job.error || 'Sync failed')
                }

                await new Promise(resolve => setTimeout(resolve, 500))
            }

            const collectionResponse = await fetch('/api/collection')

            if (!collectionResponse.ok) {
                throw new Error(`HTTP ${collectionResponse.status}`)
            }

            const collectionData = await collectionResponse.json()
            await new Promise(resolve => setTimeout(resolve, 1000)) // Wait for 1 second before closing the modal
            setCollection(collectionData)
            setSyncStatus('completed')
        } catch (error) {
            console.error('Error syncing collection:', error)
            setSyncStatus('failed')
            setSyncError(error.message)
        } finally {
            setSyncModalOpen(false)
        }
    }

    return (
        <Container fluid>
            <Group justify="space-between" align="center" mb="md">
                <Text c="dimmed">
                    {collection.length} figures
                </Text>

                <Group>
                    <Button onClick={handleSync} loading={setSyncStatus === 'starting' || setSyncStatus === 'in_progress'}>
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
                opened={syncModalOpen}
                onClose={() => {
                    if (syncStatus === 'completed' || syncStatus === 'failed') {
                        setSyncModalOpen(false)
                    }
                }}
                closeOnClickOutside={false}
                closeOnEscape={false}
                title="Sync MFC Collection"
                centered
            >
                <Stack align="center" gap="md">
                    {syncStatus !== 'completed' && syncStatus !== 'failed' && (
                        <Loader />
                    )}

                    {syncTotal > 0 && (
                        <>
                            <Text>
                                {syncProcessed} / {syncTotal} figures
                            </Text>

                            <Progress
                                value={syncPercent}
                                w="100%"
                            />
                        </>
                    )}

                    {syncStatus === 'starting' && (
                        <Text c="dimmed">
                            Getting collection from MFC...
                        </Text>
                    )}

                    {syncStatus === 'completed' && (
                        <>
                            <Text>Sync complete!</Text>
                        </>
                    )}

                    {syncStatus === 'failed' && (
                        <>
                            <Text c="red">
                                {syncError}
                            </Text>

                            <Button onClick={() => setSyncModalOpen(false)}>
                                Close
                            </Button>
                        </>
                    )}
                </Stack>
            </Modal>
        </Container>
    )
}

export default CollectionPage