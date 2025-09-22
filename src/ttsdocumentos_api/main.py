from fastapi import FastAPI

from routers.tts_router import routerTTS
from routers.documetos_router import routerDocumentos

app = FastAPI()

app.include_router(routerTTS)
app.include_router(routerDocumentos)

@app.get("/")
def read_root():
    return {"Hello": "World"}
