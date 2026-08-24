import { Button, Modal } from '@mantine/core'
function FigureModal({ selectedFigure, opened, onClose }) {
    const sizeDisplay = selectedFigure?.scale
        ? `${selectedFigure.scale} Scale`
        : selectedFigure?.height_mm
            ? `${selectedFigure.height_mm} mm`
            : 'Size unknown'

    return (
        <Modal opened={opened} onClose={onClose}>
            {selectedFigure && (
                <div>
                    <img src={selectedFigure.picture_url} alt={selectedFigure.name} />
                    <p>{selectedFigure.name}</p>
                    <p>{selectedFigure.manufacturer}</p>
                    <p>{selectedFigure.origin}</p>
                    <p>{selectedFigure.category}</p>
                    <p>{sizeDisplay}</p>
                    <p>{selectedFigure.release_date}</p>
                    <p>{selectedFigure.rating}</p>
                    <p>{selectedFigure.barcode}</p>
                    <p>----------My Collection----------</p>
                    <p>{selectedFigure.status}</p>
                    <p>{selectedFigure.purchase_price ? selectedFigure.purchase_price : "---"}</p>
                    <p>{selectedFigure.store ? selectedFigure.store : "---"}</p>
                    <p>{selectedFigure.condition ? selectedFigure.condition : "---"}</p>
                    <p>{selectedFigure.notes ? selectedFigure.notes : "---"}</p>
                </div>
            )}
            <Button>Edit</Button>
        </Modal>
    )
}
export default FigureModal