# main.py
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from image_handler import save_uploaded_image
import db
import uvicorn

app = FastAPI()




# handles the uploading of a image from a ICS instance 
@app.post("/uploadTreeImage")
async def upload_image(file: UploadFile = File(...), label: str = Form(None)):

   
    # extracts metadata from image name and then saves into image storage
    metadata = await save_uploaded_image(file)
    #stores metadata into database
    success = db.insert_image_metadata(metadata)
    return {"success": success}

##handles the creation of a dataset
@app.post("/createDataset")
async def create_dataset(data: dict):
    success = db.insert_dataset(data)
    return {"success": success}
# start the server 
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
