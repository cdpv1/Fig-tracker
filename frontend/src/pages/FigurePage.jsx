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
            : 'Size unknown'

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
        <div>
            <img src={figure.picture_url} alt={figure.name} />
            <p>{figure.name}</p>
            <p>{figure.manufacturer}</p>
            <p>{figure.origin}</p>
            <p>{figure.category}</p>
            <p>{sizeDisplay}</p>
            <p>{figure.release_date}</p>
            <p>{figure.rating}</p>
            <p>{figure.barcode}</p>
            <p>----------My Collection----------</p>
            <p>{figure.status}</p>
            <p>{figure.purchase_price ? figure.purchase_price : "---"}</p>
            <p>{figure.store ? figure.store : "---"}</p>
            <p>{figure.condition ? figure.condition : "---"}</p>
            <p>{figure.notes ? figure.notes : "---"}</p>
        </div>
    )
}

export default FigurePage
