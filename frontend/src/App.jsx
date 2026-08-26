import { Route, Routes } from 'react-router-dom'
import './App.css'
import CollectionPage from './pages/CollectionPage'
import FigurePage from './pages/FigurePage'
import { AppShell, Title, Group } from '@mantine/core'

function App() {
  return (
    <AppShell header={{ height: 60 }} padding="md">
      <AppShell.Header>
        <Group h="100%" px="md">
          <Title order={2} p="md">Fig Tracker</Title>
        </Group>
      </AppShell.Header>
      <AppShell.Main>
        <Routes>
          <Route path="/" element={<CollectionPage />}></Route>
          <Route path="/figures/:mfc_id" element={<FigurePage />} />
        </Routes>
      </AppShell.Main>
    </AppShell>
  )
}
export default App
