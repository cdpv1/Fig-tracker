import { useParams } from "react-router-dom"

function FigurePage(){
    const {mfc_id} = useParams()
    return(
        <div>
            <h1>Figure Details</h1>
            <p>{mfc_id}</p>
        </div>
    )
}

export default FigurePage
