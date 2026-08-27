import { Container, Divider, Grid, Group, Stack, Title, Text, Badge, Paper, Image, Button, Checkbox, TextInput, Textarea, NumberInput, Alert } from "@mantine/core"
import { useForm } from '@mantine/form';
import { DateInput } from '@mantine/dates';
import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"

function FigurePage() {
    const { mfc_id } = useParams()
    const [figure, setFigure] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(false)
    const [editing, setEditing] = useState(false)
    const [saving, setSaving] = useState(false)
    const [saveError, setSaveError] = useState(null)
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
                        {editing ? (<Button onClick={handleCancel} color="red">Cancel</Button>) : (<Button onClick={() => setEditing(true)}>Edit</Button>)}

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
                    ) : (
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
                    )}
                </Paper>
            </Group >
        </Container >
    )
}

export default FigurePage
