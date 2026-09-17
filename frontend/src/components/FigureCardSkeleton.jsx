import { Card, Skeleton, Stack, Group } from '@mantine/core'

function FigureCardSkeleton() {
    return (
        <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
            <Card.Section>
                <Skeleton height={240} />
            </Card.Section>

            <Stack gap="sm" mt="md">
                <Skeleton height={20} radius="sm" />
                <Skeleton height={16} width="65%" radius="sm" />
                <Group gap="xs" mt="xs">
                    <Skeleton height={22} width={72} radius="sm" />
                    <Skeleton height={22} width={64} radius="sm" />
                </Group>
            </Stack>
        </Card>
    )
}

export default FigureCardSkeleton
