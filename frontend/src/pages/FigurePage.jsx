import { Container, Divider, Grid, Group, Stack, Title, Text, Badge, Paper, Image, Button } from "@mantine/core"
import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"

function FigurePage() {
    const { mfc_id } = useParams()
    const [figure, setFigure] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(false)

    const sizeDisplay = figure?.scale
        ? `${figure.scale} Scale`
        : figure?.height_mm
            ? `${figure.height_mm} mm`
            : "—"

    useEffect(() => {
        fetch(`/api/collection/${mfc_id}`)
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`)
                }
                return response.json()
            })
            .then((data) => {
                setFigure(data)
            })
            .catch((error) => {
                console.error('Error fetching figure:', error)
                setError(error.message)
            })
            .finally(() => {
                setLoading(false)
            })
    }, [mfc_id])

    if (loading) {
        return <p>Loading figure...</p>
    }

    if (error) {
        return <p>Error loading figure: {error}</p>
    }

    if (!figure) {
        return <p>Figure not found.</p>
    }

    return (
        <Container size="xl">
            <Group>
                <Paper shadow="xs" radius="md" p="xl" w="100%">
                    <Grid>
                        <Grid.Col span={{ base: 12, md: 5 }}>
                            <Image src={figure.picture_url} alt={figure.name} h={350} fit="contain" radius="md" />
                        </Grid.Col>
                        <Grid.Col span={{ base: 12, md: 7 }}>
                            <Group>
                                <Stack>
                                    <Title>{figure.name}</Title>
                                    <Text c="dimmed">{figure.manufacturer}</Text>
                                    <Group>
                                        <Badge>{figure.category}</Badge>
                                        <Badge>{figure.status}</Badge>
                                    </Group>
                                    <Stack>
                                        <Group>
                                            <Text c="dimmed">Origin</Text>
                                            <Text>{figure.origin || "—"}</Text>
                                        </Group>

                                        <Group>
                                            <Text c="dimmed">Size</Text>
                                            <Text>{sizeDisplay || "—"}</Text>
                                        </Group>

                                        <Group>
                                            <Text c="dimmed">Release</Text>
                                            <Text>{figure.release_date || "—"}</Text>
                                        </Group>

                                        <Group>
                                            <Text c="dimmed">Rating</Text>
                                            <Text>{figure.rating ?? "—"}</Text>
                                        </Group>

                                        <Group>
                                            <Text c="dimmed">Barcode</Text>
                                            <Text>{figure.barcode || "—"}</Text>
                                        </Group>
                                    </Stack>
                                </Stack>
                                <Button component="a" href={figure.mfc_url} target="_blank" rel="noopener noreferrer" fullWidth>Link to MFC</Button>
                            </Group>

                        </Grid.Col>
                    </Grid>
                </Paper>
                <Divider my="md" />
                <Paper shadow="xs" radius="md" p="xl" w="100%">
                    <Group justify="space-between" align="center" mb="md">
                        <Group gap="sm" align="center">
                            <Title>My Collection</Title>
                            <Badge mt={8} color={figure.displayed === 1 ? "blue" : "red"}>{figure.displayed === 1 ? "Displayed" : "Not Displayed"}</Badge>
                        </Group>
                        <Button>Edit</Button>
                    </Group>
                    <Stack gap="md">
                        <Group>
                            <Text c="dimmed">Purchase Price</Text>
                            <Text>{figure.purchase_price ?? "—"}</Text>
                        </Group>

                        <Group>
                            <Text c="dimmed">Purchase Date</Text>
                            <Text>{figure.purchase_date || "—"}</Text>
                        </Group>

                        <Group>
                            <Text c="dimmed">Store</Text>
                            <Text>{figure.purchase_store || "—"}</Text>
                        </Group>

                        <Group>
                            <Text c="dimmed">Figure Condition</Text>
                            <Text>{figure.item_condition || "—"}</Text>
                        </Group>

                        <Group>
                            <Text c="dimmed">Box Condition</Text>
                            <Text>{figure.box_condition || "—"}</Text>
                        </Group>

                        <Group>
                            <Text c="dimmed">Notes</Text>
                            <Text>{figure.notes || "—"}</Text>
                        </Group>
                    </Stack>
                </Paper>
            </Group>
        </Container >
    )
}

export default FigurePage
