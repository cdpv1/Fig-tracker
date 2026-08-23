from fastapi import FastAPI

app = FastAPI()

@app.get("/api/figures")
def get_figures():\
    return [
        {
            "id":1,
            "name":"test figure",
            "scale":1/6
        }
    ]