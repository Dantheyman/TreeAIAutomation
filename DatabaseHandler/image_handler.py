import os
from datetime import datetime

from bson import ObjectId
from fastapi import UploadFile
from config import BASE_IMAGE_DIR

# saves an uploaded image to file system and saves metadata
async def save_uploaded_image(file):
    
    fileName = file.filename
    #extract info from filename
    parts = fileName.split("_")
    lat = float(parts[3])      
    lon = float(parts[5])      
    date = parts[7].split(".")[0]
    extension = parts[7].split(".")[1]

    # convert date to required format
    subfolderName = convert_to_yyyymmdd(date)

    #create new directory for date 
    target_dir = os.path.join(BASE_IMAGE_DIR, subfolderName)
    os.makedirs(target_dir, exist_ok=True)

    #generate unique ID
    id = str(ObjectId())
    file_path = os.path.join(target_dir,id+"."+extension)

    
    

    #save image to disk
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # return metadata
    return {
        "_id":id,
        "latitude": lat,
        "longitude":lon,
        "capture_date" : date,
        "file_path" : file_path
    }
    

def convert_to_yyyymmdd(date_str):
    # Parse the original date
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    # Format to desired output
    return date_obj.strftime("%Y%m%d")