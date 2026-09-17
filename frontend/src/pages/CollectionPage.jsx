import { useState, useEffect } from 'react'
import FigureCard from '../components/FigureCard.jsx'
import FigureCardSkeleton from '../components/FigureCardSkeleton.jsx'
import { Container, SimpleGrid, Group, Button, Text, Modal, Stack, Loader, Progress, Card, Badge, Pagination } from '@mantine/core'

// import FigureModal from '../components/FigureModal'
function CollectionPage() {
    const [collection, setCollection] = useState([])
    const [collectionTotal, setCollectionTotal] = useState(0)
    const [collectionPage, setCollectionPage] = useState(1)
    const [collectionLoading, setCollectionLoading] = useState(true)
    const [syncModalOpen, setSyncModalOpen] = useState(false)
    const [syncStatus, setSyncStatus] = useState(null)
    const [syncProcessed, setSyncProcessed] = useState(0)
    const [syncTotal, setSyncTotal] = useState(0)
    const [syncError, setSyncError] = useState(null)
    const [providerStatus, setProviderStatus] = useState([])
    const collectionPageSize = 24

    // const [selectedFigure, setSelectedFigure] = useState(null)

    useEffect(() => {
        const controller = new AbortController()
        const offset = (collectionPage - 1) * collectionPageSize
        fetch(`/api/collection?limit=${collectionPageSize}&offset=${offset}`, {
            signal: controller.signal,
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`)
                }
                return response.json()
            })
            .then((data) => {
                setCollection(data.items)
                setCollectionTotal(data.total)
                setCollectionLoading(false)
            })
            .catch((error) => {
                if (error.name !== 'AbortError') {
                    console.error('Error fetching collection:', error)
                    setCollectionLoading(false)
                }
            })
        return () => controller.abort()
    }, [collectionPage])

    useEffect(() => {
        let active = true
        let timeoutId
        const loadProviderStatus = () => {
            fetch('/api/prices/providers/status')
                .then((response) => {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`)
                    }
                    return response.json()
                })
                .then((data) => {
                    if (active) {
                        setProviderStatus(data)
                        if (data.some((provider) => provider.status === 'running')) {
                            timeoutId = setTimeout(loadProviderStatus, 5000)
                        }
                    }
                })
                .catch((error) => console.error('Error fetching provider status:', error))
        }

        loadProviderStatus()
        return () => {
            active = false
            clearTimeout(timeoutId)
        }
    }, [])

    const syncPercent =
        syncTotal > 0
            ? (syncProcessed / syncTotal) * 100
            : 0

    const handleCollectionPageChange = (page) => {
        setCollectionLoading(true)
        setCollectionPage(page)
    }

    const handleSync = async () => {
        setSyncModalOpen(true)
        setSyncStatus('starting')
        setSyncProcessed(0)
        setSyncTotal(0)
        setSyncError(null)
        try {
            const response = await fetch('/api/mfc/collection/sync', {
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

            const offset = (collectionPage - 1) * collectionPageSize
            const collectionResponse = await fetch(
                `/api/collection?limit=${collectionPageSize}&offset=${offset}`
            )

            if (!collectionResponse.ok) {
                throw new Error(`HTTP ${collectionResponse.status}`)
            }

            const collectionData = await collectionResponse.json()
            await new Promise(resolve => setTimeout(resolve, 1000)) // Wait for 1 second before closing the modal
            setCollection(collectionData.items)
            setCollectionTotal(collectionData.total)
            setCollectionLoading(false)
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
                    {collectionTotal} figures
                </Text>

                <Group>
                    <Button onClick={handleSync} loading={syncStatus === 'starting' || syncStatus === 'in_progress'}>
                        Sync MFC
                    </Button>
                </Group>
            </Group>
            {providerStatus.length > 0 && (
                <Card withBorder mb="md" padding="sm">
                    <Group gap="sm">
                        <Text fw={500}>Price sources</Text>
                        {providerStatus.map((provider) => (
                            <Badge
                                key={provider.provider}
                                color={provider.status === 'available'
                                    ? 'green'
                                    : provider.status === 'running'
                                        ? 'blue'
                                        : 'orange'}
                                variant="light"
                                title={provider.error || undefined}
                            >
                                {provider.provider}: {provider.status}
                            </Badge>
                        ))}
                    </Group>
                </Card>
            )}
            <SimpleGrid cols={{ base: 1, sm: 2, md: 3, lg: 4, xl: 8 }} spacing="lg">
                {collectionLoading
                    ? Array.from({ length: collectionPageSize }, (_, index) => (
                        <FigureCardSkeleton key={`skeleton-${index}`} />
                    ))
                    : collection.map((figure) => (
                        <FigureCard key={figure.mfc_id} figure={figure} />
                    ))}
            </SimpleGrid>
            {collectionTotal > collectionPageSize && (
                <Group justify="center" mt="xl">
                    <Pagination
                        value={collectionPage}
                        onChange={handleCollectionPageChange}
                        total={Math.ceil(collectionTotal / collectionPageSize)}
                    />
                </Group>
            )}
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
                overlayProps={{ backgroundOpacity: 0.75, blur: 3 }}
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