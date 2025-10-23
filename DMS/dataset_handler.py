from config import WORKING_DIR
import db
import shutil
import os
from concurrent.futures import ThreadPoolExecutor
import subprocess
import yaml

#this file handles moving datasets around the file system


#copies the photos in a dataset into the working directory
# param: dataset_id: id of dataset 
def get_dataset_photos(dataset_id):

    # Define the full paths
    folder_name = f"loaded_dataset"
     # added .zip extension
    dataset_folder = os.path.join(WORKING_DIR, folder_name)
    image_folder = os.path.join(dataset_folder, "images")       
    annotations_folder = os.path.join(dataset_folder, "labels") 

    # Ensure the temp folder is clean
    if os.path.exists(dataset_folder):
        shutil.rmtree(dataset_folder)
    os.makedirs(dataset_folder)
    os.makedirs(image_folder)
    os.makedirs(annotations_folder)

    dataset = db.get_dataset_from_id(dataset_id)
    photo_types = ["train_photos", "test_photos", "val_photos"]

    for photo_type in photo_types:
        # Get photo IDs for all images of this type
        photo_ids = dataset[photo_type]

        photos = db.get_photos(photo_ids)
        photo_paths = [photo["file_path"] for photo in photos]

        # Create subfolder in images (e.g., images/train, images/test, images/val)
        subfolder_name = photo_type.split("_")[0]  # 'train', 'test', 'val'
        subfolder = os.path.join(image_folder, subfolder_name)
        os.makedirs(subfolder, exist_ok=True)

        # Copy images into relevant subfolder
        total_photos = len(photo_paths)

        for i, photo_path in enumerate(photo_paths, start=1):
            if os.path.isfile(photo_path):
                with ThreadPoolExecutor(max_workers=6) as executor:
                    executor.submit(copy_file, photo_path, subfolder)
            
            if i % 50 == 0 or i == total_photos:
                percent_done = (i / total_photos) * 100
                print(f"{percent_done:.2f}% done")
        print(f"Subfolder {photo_type.split('_')[0]} Done")
    return dataset_folder

#writes the data.yaml file into the working directory
# param: classes: list of classes that have been annotated for 
def write_yaml(classes):
    # Define the paths to train, val, and test directories
    train_path = os.path.join(WORKING_DIR,"loaded_dataset/images", "train")
    val_path = os.path.join(WORKING_DIR, "loaded_dataset/images", "val")
    test_path = os.path.join(WORKING_DIR, "loaded_dataset/images", "test")

    
    # Prepare the YAML content
    data_yaml = {
        "train": train_path,
        "val": val_path,
        "test": test_path,
        "nc": len(classes),  # Number of classes
        "names": classes  # Class names
    }
    
    # Define the output path for the YAML file
    yaml_file_path = os.path.join(WORKING_DIR, "data.yaml")

    # If the YAML file exists, delete it
    if os.path.exists(yaml_file_path):
        os.remove(yaml_file_path)
    
    # Write the YAML file
    with open(yaml_file_path, "w") as yaml_file:
        yaml.dump(data_yaml, yaml_file, default_flow_style=False)
    
#loads an entire dataset into the working directory including annotations in YOLO ready format
# param: dataset_id: id of dataset being loaded
def load_dataset(dataset_id):
    # Define the full paths
    folder_name = f"loaded_dataset"
    dataset_folder = os.path.join(WORKING_DIR, folder_name)
    image_folder = os.path.join(dataset_folder, "images")       
    annotations_folder = os.path.join(dataset_folder, "labels")
    
    # Ensure the temp folder is clean
    if os.path.exists(dataset_folder):
        shutil.rmtree(dataset_folder)
    os.makedirs(dataset_folder)
    os.makedirs(image_folder)
    os.makedirs(annotations_folder)

    dataset = db.get_dataset_from_id(dataset_id)
    photo_types = ["train_photos", "test_photos", "val_photos"]

    # Load the classes list for YOLOv5 format
    dataset_classes = dataset.get("classes", [])

    for photo_type in photo_types:
        # Get photo IDs for all images of this type
        photo_ids = dataset[photo_type]
     
       
        photos = db.get_photos(photo_ids)
        photo_paths = [photo["file_path"] for photo in photos] 

        # Create subfolder in images 
        subfolder_name = photo_type.split("_")[0]  
        subfolder = os.path.join(image_folder, subfolder_name)
        os.makedirs(subfolder, exist_ok=True)

        # Copy images into relevant subfolder
        total_photos = len(photo_paths)

        for i, photo_path in enumerate(photo_paths, start=1):
            if os.path.isfile(photo_path):
                with ThreadPoolExecutor(max_workers=6) as executor:
                    executor.submit(copy_file, photo_path, subfolder)
            
            if i % 50 == 0 or i == total_photos:
                percent_done = (i / total_photos) * 100
                print(f"{percent_done:.2f}% done")
        print(f"Subfolder {photo_type.split('_')[0]} Done")

     
       
        # Now handle annotations
        for photo_id in photo_ids:
            annotations = db.get_annotations_for_photo(photo_id)
           
            
            if annotations:
                subfolder_annotations = os.path.join(annotations_folder, subfolder_name)
                os.makedirs(subfolder_annotations, exist_ok=True)

                for annotation in annotations:
                    annotation_classes = annotation["classes"]
                 
                    if set(annotation_classes) == set(dataset_classes):
                        annotation_data = annotation["annotation"]
                    
                        # Create a .txt file for each image with YOLOv5 annotations
                        annotation_filename = os.path.join(subfolder_annotations,f"{photo_id}.txt")

                        with open(annotation_filename, "w") as f:
                            for line in annotation_data:
                                f.write(line+"\n")
        
            if i % 50 == 0 or i == total_photos:
                percent_done = (i / total_photos) * 100
                print(f"{percent_done:.2f}% done for annotations")

    write_yaml(dataset_classes)

    print("Dataset loading complete")

#creates symlink at the dest_path for pointing to src_path
# method in its current form does not support windows
def copy_file(src_path, dest_path):
    result = subprocess.run(
        ["ln", "-s", src_path, dest_path],
        check=True
    )