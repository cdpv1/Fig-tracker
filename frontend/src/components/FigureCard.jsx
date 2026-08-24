import {
    Card,
    Image,
    Text,
    Badge,
    Group,
    Stack,
    Box
} from '@mantine/core'
function FigureCard({ figure }) {

    return (
        <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
            <Card.Section>
                <Box h={240} p="md">
                    <Image src={figure.picture_url} alt={figure.name} h="100%" w="100%" fit="contain"/>
                </Box>
            </Card.Section>

            <Stack gap="xs" mt="md">
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