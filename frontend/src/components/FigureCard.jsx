import {
    Card,
    Image,
    Text,
    Badge,
    Group,
    Stack,
    Box
} from '@mantine/core'
import { useNavigate } from 'react-router-dom'
function FigureCard({ figure }) {
    const navigate = useNavigate()
    return (
        <Card className="figure-card" shadow="sm" padding="lg" radius="md" withBorder h="100%" target="_blank" onClick={() => navigate(`/figures/${figure.mfc_id}`)} style={{ cursor: 'pointer' }}>
            <Card.Section>
                <Box h={240} p="md">
                    <Image src={figure.picture_url} alt={figure.name} h="100%" w="100%" fit="contain" />
                </Box>
            </Card.Section>

            <Stack gap="sm">
                <Text fw={600} lineClamp={2}>{figure.name}</Text>
                <Text size="sm" c="dimmed">{figure.manufacturer || 'Unknown manufacturer'}</Text>
                <Group gap="xs" mt="xs">
                    {figure.scale && (
                        <Badge variant="light">
                            {figure.scale} Scale
                        </Badge>
                    )}

                    {figure.category && (
                        <Badge size="sm" variant="light">
                            {figure.category}
                        </Badge>
                    )}

                    {figure.status && (
                        <Badge size="sm" variant="outline">
                            {figure.status}
                        </Badge>
                    )}

                    {!figure.scale && figure.height_mm && (
                        <Text size="sm" c="dimmed">
                            {figure.height_mm} mm
                        </Text>
                    )}
                </Group>
            </Stack>
        </Card>
    )
}

export default FigureCard