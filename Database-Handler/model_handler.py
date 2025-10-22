import os
from config import BASE_MODEL_DIR
import db

async def upload_model(file, model_id):

    contents = await file.read()


    save_path = os.path.join(BASE_MODEL_DIR,model_id+".pt")
    with open(save_path, "wb") as f:
        f.write(contents)
    
    db.save_model_path(model_id,save_path)