import { ActionIcon, Container, Divider, Grid, Group, Stack, Title, Text, Badge, Paper, Image, Button, Checkbox, TextInput, Textarea, NumberInput, Alert, Table, Box, Modal, SimpleGrid, Skeleton } from "@mantine/core"
import { useForm } from '@mantine/form';
import { DateInput } from '@mantine/dates';
import { useEffect, useRef, useState } from "react"
import { useParams } from "react-router-dom"
import {CaretLeftIcon, CaretRightIcon} from '@phosphor-icons/react';

function FigurePageSkeleton() {
    return (
        <Container size="xl">
            <Paper shadow="xs" radius="md" p="xl" w="100%">
                <Grid>
                    <Grid.Col span={{ base: 12, md: 5 }}>
                        <Skeleton height={350} radius="md" />
                        <Group gap="xs" mt="md">
                            <Skeleton height={64} width={64} radius="sm" />
                            <Skeleton height={64} width={64} radius="sm" />
                            <Skeleton height={64} width={64} radius="sm" />
                        </Group>
                    </Grid.Col>
                    <Grid.Col span={{ base: 12, md: 7 }}>
                        <Stack gap="md">
                            <Skeleton height={32} width="80%" radius="sm" />
                            <Skeleton height={18} width="45%" radius="sm" />
                            <Group gap="xs">
                                <Skeleton height={24} width={84} radius="sm" />
                                <Skeleton height={24} width={96} radius="sm" />
                                <Skeleton height={24} width={72} radius="sm" />
                            </Group>
                            <Divider />
                            <Skeleton height={18} width="35%" radius="sm" />
                            <Skeleton height={42} radius="sm" />
                            <Skeleton height={42} radius="sm" />
                            <Skeleton height={100} radius="sm" />
                        </Stack>
                    </Grid.Col>
                </Grid>
                <Divider my="xl" />
                <Stack gap="md">
                    <Skeleton height={24} width="30%" radius="sm" />
                    <Skeleton height={120} radius="sm" />
                </Stack>
            </Paper>
        </Container>
    )
}

function FigurePage() {
    const { mfc_id } = useParams()
    const [figure, setFigure] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(false)
    const [editing, setEditing] = useState(false)
    const [saving, setSaving] = useState(false)
    const [saveError, setSaveError] = useState(null)
    const [priceHistory, setPriceHistory] = useState([])
    const [priceSummary, setPriceSummary] = useState(null)
    const [galleryImages, setGalleryImages] = useState([])
    const [selectedImageIndex, setSelectedImageIndex] = useState(0)
    const [imageModalOpened, setImageModalOpened] = useState(false)
    const thumbnailRefs = useRef([])
    const form = useForm({
        initialValues: {
            purchase_price: '',
            purchase_date: null,
            purchase_store: '',
            item_condition: '',
            box_condition: '',
            displayed: false,
            notes: '',
        },
    })

    const handleCancel = () => {
        form.setValues({
            purchase_price: figure.purchase_price ?? '',
            purchase_date: figure.purchase_date ?? null,
            purchase_store: figure.purchase_store ?? '',
            item_condition: figure.item_condition ?? '',
            box_condition: figure.box_condition ?? '',
            displayed: Boolean(figure.displayed),
            notes: figure.notes ?? '',
        })

        setEditing(false)
    }

    const handleSave = async () => {
        setSaving(true)
        try {
            const values = {
                ...form.values,
                purchase_price:
                    form.values.purchase_price === ''
                        ? null
                        : Number(form.values.purchase_price),
                purchase_date:
                    form.values.purchase_date || null,
                purchase_store:
                    form.values.purchase_store || null,
                item_condition:
                    form.values.item_condition || null,
                box_condition:
                    form.values.box_condition || null,
                notes:
                    form.values.notes || null,
            }

            const payload = {}

            for (const [key, value] of Object.entries(values)) {
                const currentValue =
                    key === 'displayed'
                        ? Boolean(figure[key])
                        : figure[key]

                if (value !== currentValue) {
                    payload[key] = value
                }
            }

            if (Object.keys(payload).length === 0) {
                setEditing(false)
                return
            }

            const response = await fetch(`/api/collection/${mfc_id}`, {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload)
            })

            if (!response.ok) {
                setSaveError(response.statusText)
                throw new Error(`HTTP ${response.status}`)
            }

            const updated = await response.json()
            console.log('Updated response:', updated)
            console.log('Form values:', payload)
            setFigure((current) => ({
                ...current,
                ...updated,
            }))

            setEditing(false)
            setSaveError(null)
        } catch (error) {
            console.log("Error Saving Edits:", error)
            setSaveError(error.message)

        } finally {
            setSaving(false)
        }
    }

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
                try {
                    setGalleryImages(JSON.parse(data.gallery_urls || '[]'))
                } catch (galleryError) {
                    console.error('Error parsing gallery images:', galleryError)
                    setGalleryImages([])
                }
                form.setValues({
                    purchase_price: data.purchase_price ?? '',
                    purchase_date: data.purchase_date ?? '',
                    purchase_store: data.purchase_store ?? '',
                    item_condition: data.item_condition ?? '',
                    box_condition: data.box_condition ?? '',
                    displayed: Boolean(data.displayed),
                    notes: data.notes ?? '',
                })
            })
            .catch((error) => {
                console.error('Error fetching figure:', error)
                setError(error.message)
            })
            .finally(() => {
                setLoading(false)
            })

        fetch(`/api/prices/${mfc_id}`)
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`)
                }
                return response.json()
            })
            .then((data) => {
                setPriceHistory(data)
            })
            .catch((error) => {
                console.error('Error fetching price history:', error)
            })

        fetch(`/api/prices/${mfc_id}/summary`)
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`)
                }
                return response.json()
            })
            .then((data) => setPriceSummary(data))
            .catch((error) => {
                console.error('Error fetching price summary:', error)
            })
    }, [mfc_id])

    useEffect(() => {
        thumbnailRefs.current[selectedImageIndex]?.scrollIntoView({
            behavior: 'smooth',
            block: 'nearest',
            inline: 'nearest',
        })
    }, [selectedImageIndex])

    if (loading) {
        return <FigurePageSkeleton />
    }

    if (error) {
        return <p>Error loading figure: {error}</p>
    }

    if (!figure) {
        return <p>Figure not found.</p>
    }

    const imageCount = galleryImages.length + 1
    const getGalleryImageUrl = (index) => {
        const galleryUrl = galleryImages[index]
        try {
            return new URL(galleryUrl).hostname === 'myfigurecollection.net'
                ? `/api/mfc/gallery-image/${figure.mfc_id}/${index}`
                : galleryUrl
        } catch {
            return galleryUrl
        }
    }
    const selectedImageUrl = selectedImageIndex === 0
        ? `/api/mfc/image/${figure.mfc_id}?source=mfc-primary-v2`
        : getGalleryImageUrl(selectedImageIndex - 1)
    const showPreviousImage = () => {
        setSelectedImageIndex((current) => (current - 1 + imageCount) % imageCount)
    }
    const showNextImage = () => {
        setSelectedImageIndex((current) => (current + 1) % imageCount)
    }
    const hasPurchaseValue = (value) => (
        value !== null
        && value !== undefined
        && (typeof value !== 'string' || value.trim() !== '')
    )
    const hasPurchaseDetails = [
        figure.purchase_price,
        figure.purchase_date,
        figure.purchase_store,
        figure.item_condition,
        figure.box_condition,
        figure.notes,
    ].some(hasPurchaseValue)

    return (
        <Container size="xl">
            <Group>
                <Paper shadow="xs" radius="md" p="xl" w="100%">
                    <Grid>
                        <Grid.Col span={{ base: 12, md: 5 }}>
                            <Box pos="relative">
                                <Image
                                    src={selectedImageUrl}
                                    alt={figure.name}
                                    h={350}
                                    fit="contain"
                                    radius="md"
                                    onClick={() => setImageModalOpened(true)}
                                    style={{ cursor: 'zoom-in' }}
                                />
                                {imageCount > 1 && (
                                    <Box
                                        pos="absolute"
                                        top={0}
                                        right={0}
                                        bottom={0}
                                        left={0}
                                        px="sm"
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'space-between',
                                            pointerEvents: 'none',
                                        }}
                                    >
                                        <ActionIcon
                                            onClick={showPreviousImage}
                                            aria-label="Show previous image"
                                            variant="light"
                                            radius="m"
                                            size="lg"
                                            opacity={0.7}
                                            style={{ pointerEvents: 'auto' }}
                                        >
                                            <CaretLeftIcon size={32} />
                                        </ActionIcon>
                                        <ActionIcon
                                            onClick={showNextImage}
                                            aria-label="Show next image"
                                            variant="light"
                                            radius="m"
                                            size="lg"
                                            opacity={0.7}
                                            style={{ pointerEvents: 'auto' }}
                                        >
                                            <CaretRightIcon size={32} />
                                        </ActionIcon>
                                    </Box>
                                )}
                            </Box>
                            {galleryImages.length > 0 && (
                                <div
                                    style={{
                                        display: 'flex',
                                        gap: 'var(--mantine-spacing-xs)',
                                        marginTop: 'var(--mantine-spacing-md)',
                                        maxWidth: '100%',
                                        overflowX: 'auto',
                                        overflowY: 'hidden',
                                        paddingBottom: 'var(--mantine-spacing-xs)',
                                    }}
                                >
                                    {[null, ...galleryImages].map((imageUrl, index) => (
                                        <Button
                                            key={imageUrl || 'primary'}
                                            ref={(element) => {
                                                thumbnailRefs.current[index] = element
                                            }}
                                            variant="subtle"
                                            p={0}
                                            style={{
                                                flex: '0 0 64px',
                                                boxSizing: 'border-box',
                                                border: selectedImageIndex === index
                                                    ? '2px solid var(--mantine-color-blue-6)'
                                                    : '2px solid transparent',
                                            }}
                                            w={64}
                                            h={64}
                                            onClick={() => setSelectedImageIndex(index)}
                                            aria-label={`Show ${figure.name} image ${index + 1}`}
                                        >
                                            <Image
                                                src={index === 0
                                                    ? `/api/mfc/image/${figure.mfc_id}?source=mfc-primary-thumbnail`
                                                    : getGalleryImageUrl(index - 1)}
                                                alt=""
                                                w={60}
                                                h={60}
                                                fit="cover"
                                            />
                                        </Button>
                                    ))}
                                </div>
                            )}
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
                    <Title order={2} mb="md">
                        Market Prices
                    </Title>
                    {!priceSummary?.markets?.length ? (
                        <Text c="dimmed">No market summary yet.</Text>
                    ) : (
                        <Stack gap="lg">
                            {priceSummary.markets.map((market) => (
                                <Stack key={market.currency} gap="sm">
                                    <Title order={3}>{market.currency}</Title>
                                    <SimpleGrid cols={{ base: 2, sm: 4 }}>
                                        <MarketStat label="Average" value={formatPrice(market.average, market.currency)} />
                                        <MarketStat label="Lowest" value={formatPrice(market.minimum, market.currency)} />
                                        <MarketStat label="Highest" value={formatPrice(market.maximum, market.currency)} />
                                        <MarketStat label="In stock" value={`${market.in_stock_count} shops`} />
                                    </SimpleGrid>
                                    <Text size="sm" c="dimmed">
                                        {market.shops?.length
                                            ? `Available from ${market.shops.join(', ')}`
                                            : 'No in-stock shops in the latest observations'}
                                    </Text>
                                </Stack>
                            ))}
                        </Stack>
                    )}
                </Paper>
                <Divider my="md" />
                <Paper shadow="xs" radius="md" p="xl" w="100%">
                    <Group justify="space-between" align="center" mb="md">
                        <Group gap="sm" align="center">
                            <Title>My Collection</Title>
                            <Badge mt={8} color={figure.displayed === 1 ? "blue" : "grey"}>{figure.displayed === 1 ? "Displayed" : "Not Displayed"}</Badge>
                        </Group>
                        {editing ? (
                            <Button onClick={handleCancel} color="red">Cancel</Button>
                        ) : hasPurchaseDetails ? (
                            <Button onClick={() => setEditing(true)}>Edit</Button>
                        ) : null}

                    </Group>
                    {editing ? (
                        <Stack gap="md">
                            {saveError && (
                                <Alert color="red" mb="md">
                                    {saveError}
                                </Alert>
                            )}
                            <Group>
                                <Text c="dimmed">Purchase Price</Text>
                                <NumberInput decimalScale={2} {...form.getInputProps('purchase_price')} />
                            </Group>

                            <Group>
                                <Text c="dimmed">Purchase Date</Text>
                                <DateInput valueFormat="YYYY-MM-DD" {...form.getInputProps('purchase_date')} />
                            </Group>

                            <Group>
                                <Text c="dimmed">Store</Text>
                                <TextInput {...form.getInputProps('purchase_store')} />
                            </Group>

                            <Group>
                                <Text c="dimmed">Figure Condition</Text>
                                <TextInput {...form.getInputProps('item_condition')} />
                            </Group>

                            <Group>
                                <Text c="dimmed">Box Condition</Text>
                                <TextInput {...form.getInputProps('box_condition')} />
                            </Group>

                            <Group>
                                <Text c="dimmed">Displayed?</Text>
                                <Checkbox {...form.getInputProps('displayed', { type: 'checkbox' })}
                                />
                            </Group>

                            <Group>
                                <Text c="dimmed">Notes</Text>
                                <Textarea {...form.getInputProps('notes')} />
                            </Group>
                            <Button fullWidth onClick={handleSave} loading={saving}>Save</Button>
                        </Stack>
                    ) : !hasPurchaseDetails ? (
                        <Group justify="space-between" align="center">
                            <Text c="dimmed">No purchase details recorded.</Text>
                            <Button variant="light" onClick={() => setEditing(true)}>Add details</Button>
                        </Group>
                    ) : (
                        <Stack gap="md">
                            {hasPurchaseValue(figure.purchase_price) && (
                                <Group>
                                    <Text c="dimmed">Purchase Price</Text>
                                    <Text>{figure.purchase_price}</Text>
                                </Group>
                            )}
                            {hasPurchaseValue(figure.purchase_date) && (
                                <Group>
                                    <Text c="dimmed">Purchase Date</Text>
                                    <Text>{figure.purchase_date}</Text>
                                </Group>
                            )}
                            {hasPurchaseValue(figure.purchase_store) && (
                                <Group>
                                    <Text c="dimmed">Store</Text>
                                    <Text>{figure.purchase_store}</Text>
                                </Group>
                            )}
                            {hasPurchaseValue(figure.item_condition) && (
                                <Group>
                                    <Text c="dimmed">Figure Condition</Text>
                                    <Text>{figure.item_condition}</Text>
                                </Group>
                            )}
                            {hasPurchaseValue(figure.box_condition) && (
                                <Group>
                                    <Text c="dimmed">Box Condition</Text>
                                    <Text>{figure.box_condition}</Text>
                                </Group>
                            )}
                            {hasPurchaseValue(figure.notes) && (
                                <Group>
                                    <Text c="dimmed">Notes</Text>
                                    <Text>{figure.notes}</Text>
                                </Group>
                            )}
                        </Stack>
                    )}
                </Paper>
                <Divider my="md" />
                <Paper shadow="xs" radius="md" p="xl" w="100%">
                    <Title order={2} mb="md">
                        Price History
                    </Title>

                    {priceHistory.length === 0 ? (
                        <Text c="dimmed">No price history yet.</Text>
                    ) : (
                        <Table>
                            <Table.Thead>
                                <Table.Tr>
                                    <Table.Th>Source</Table.Th>
                                    <Table.Th>Shop</Table.Th>
                                    <Table.Th>Price</Table.Th>
                                    <Table.Th>Condition</Table.Th>
                                    <Table.Th>Availability</Table.Th>
                                    <Table.Th>Recorded</Table.Th>
                                </Table.Tr>
                            </Table.Thead>

                            <Table.Tbody>
                                {priceHistory.map((record) => (
                                    <Table.Tr key={record.id}>
                                        <Table.Td>{record.source}</Table.Td>
                                        <Table.Td>{record.shop || '—'}</Table.Td>
                                        <Table.Td>
                                            {formatPrice(record.price, record.currency)}
                                        </Table.Td>
                                        <Table.Td>{record.item_condition || '—'}</Table.Td>
                                        <Table.Td>{record.availability || '—'}</Table.Td>
                                        <Table.Td>{record.recorded_at}</Table.Td>
                                    </Table.Tr>
                                ))}
                            </Table.Tbody>
                        </Table>
                    )}
                </Paper>
            </Group >
            <Modal
                opened={imageModalOpened}
                onClose={() => setImageModalOpened(false)}
                title={figure.name}
                centered
                size="xl"
                overlayProps={{ backgroundOpacity: 0.75, blur: 3 }}
            >
                <Box pos="relative">
                    <Image
                        src={selectedImageUrl}
                        alt={figure.name}
                        h="min(75vh, 800px)"
                        fit="contain"
                    />
                    {imageCount > 1 && (
                        <Box
                            pos="absolute"
                            top={0}
                            right={0}
                            bottom={0}
                            left={0}
                            px="sm"
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                pointerEvents: 'none',
                            }}
                        >
                            <ActionIcon
                                onClick={showPreviousImage}
                                aria-label="Show previous image"
                                variant="light"
                                radius="m"
                                size="lg"
                                opacity={0.7}
                                style={{ pointerEvents: 'auto' }}
                            >
                                <CaretLeftIcon size={32} />
                            </ActionIcon>
                            <ActionIcon
                                onClick={showNextImage}
                                aria-label="Show next image"
                                variant="light"
                                radius="m"
                                size="lg"
                                opacity={0.7}
                                style={{ pointerEvents: 'auto' }}
                            >
                                <CaretRightIcon size={32} />
                            </ActionIcon>
                        </Box>
                    )}
                </Box>
            </Modal>
        </Container >
    )
}

function MarketStat({ label, value }) {
    return (
        <Paper withBorder p="sm">
            <Text size="xs" c="dimmed">{label}</Text>
            <Text fw={600}>{value}</Text>
        </Paper>
    )
}

function formatPrice(value, currency) {
    if (value === null || value === undefined) {
        return '—'
    }
    return `${Number(value).toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    })} ${currency}`
}

export default FigurePage
