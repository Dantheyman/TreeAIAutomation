import os
from fastapi import FastAPI, File, UploadFile , Response, HTTPException, Form
import image_handler 
import dataset_handler
import model_handler
import traceback
import db
import uvicorn



app = FastAPI()

######################## Image Requests ########################

# handles the uploading of a image from a ICS instance 
@app.post("/trees")
async def upload_image(file: UploadFile = File(...)):

   
    # extracts metadata from image name and then saves into image storage
    metadata = await image_handler.save_uploaded_image(file)
    if metadata == None:
        return Response(status_code=500)
    
    #stores metadata into database
    db.insert_image_metadata(metadata)
    return Response(status_code=200)


################ Dataset Requests ###################


#handles the creation of a dataset, returns id of created dataset
@app.post("/dataset/photos")
async def create_dataset(filters: dict, split: str, name: str, classes: str):
    try:
        dataset_id = db.create_dataset(filters,split,name,classes)
        if dataset_id == 0:
            raise HTTPException(status_code=500, detail="Failed to create dataset")
        return {"id":dataset_id}
    except Exception as e:
        print("Exception occurred:", e)
        traceback.print_exc()
        return {"error": str(e)}


# groups the images into a folder so they can be accessed by IPS,
# assumes IPS and Database Handler are on the same computer 
@app.get("/dataset/photos")
async def dataset_photos(dataset_id: str):
    try:
       
        path = dataset_handler.get_dataset_photos(dataset_id)

        return {"path" : path}
    except Exception as e:
        print("Exception occurred:", e)
        traceback.print_exc()
        return Response(status_code=500)

#removes a photo from a given dataset
@app.delete("/dataset/photo")
async def remove_photo_from_dataset(dataset_id: str, photo_id: str):
    try:
       
        db.remove_photo_from_dataset(dataset_id,photo_id)

        return Response(status_code=200)
    except Exception as e:
        print("Exception occurred:", e)
        traceback.print_exc()
        return Response(status_code=500)

#returns true or false depending if the name as been used for a given dataset
@app.get("/dataset/name")
async def dataset_name_exists(name: str):
    return {"name_exists": db.dataset_name_exists(name)}


#returns the id belonging to the dataset provided 
@app.get("/dataset/id")
async def dataset_get_id(name: str):
    dataset = db.get_dataset_from_name(name)
    return {"id": dataset["_id"]}

    
# returns a list of all names of datasets in alphabetical order 
@app.get("/datasets/names")
async def get_dataset_names():

    names = db.get_all_dataset_names()
    return {"names" : names}

#returns all dataset metadata
@app.get("/dataset/metadata")
async def get_dataset(dataset_id: str):
    try: 
        return db.get_dataset_from_id(dataset_id)
    except Exception as e:
        print("Exception occurred:", e)
        traceback.print_exc()
        return Response(status_code=500)

#loads dataset into the working DIR
@app.get ("/dataset")
async def load_dataset(dataset_id: str):
    dataset_handler.load_dataset(dataset_id)
 

######################## Annotation Requests ########################

#adds annotations to the dataset
@app.post("/annotations")
async def add_annotations(payload :dict):
    
    try:   

        success = db.save_annotations(payload)
        
        if success:
            return Response(status_code=200)
        else:
            return Response(status_code=500)
    except Exception as e:
        print("Exception occurred:", e)
        traceback.print_exc()
        return Response(status_code=500)


# gets all annotations for a given photo
@app.get("/annotations/photo")
async def  get_annotations(photo_id: str):
    try:
       
        annotations = list(db.get_annotations_for_photo(photo_id))
        return {"annotations": annotations }
    except Exception as e:
        print("Exception occurred:", e)
        traceback.print_exc()
        return Response(status_code=500)

######################## Model Requests ########################

#gets all models
@app.get("/models")
async def get_all_models():
    try:
       models = db.get_all_models()

       return {"models" : models}
        
    except Exception as e:
        print("Exception occurred:", e)
        traceback.print_exc()
        return Response(status_code=500)

#gets the path to the model weights, assumes IPS and DMS on same system
@app.get("/models/path")
async def get_model_path(model_name:str):

    try:
       
        model_path = db.get_model_path(model_name)
        return {"file_path" : model_path}
       
    except Exception as e:
        print("Exception occurred:", e)
        traceback.print_exc()
        return Response(status_code=500)

#checks if a given model name exists already
@app.get("/models/name")
async def model_name_exists(model_name:str):
    try:
       
       model_name_exists = db.model_name_exists(model_name)
       return {"name_exists" : model_name_exists}

       
    except Exception as e:
        print("Exception occurred:", e)
        traceback.print_exc()
        return Response(status_code=500)

#handles uploading of model to the DMS 
@app.post("/models/path")
async def upload_model_file(model_id: str = Form(...),file: UploadFile = File(...)):
    try:
        await  model_handler.upload_model(file,model_id)

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")



@app.post("/models")
async def upload_model_data(model_data: dict):
   
    try:

        model_id = db.save_model(model_data)
        return {"id": model_id}
       
    except Exception as e:
        print("Exception occurred:", e)
        traceback.print_exc()
        return Response(status_code=500)



# start the server 
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
