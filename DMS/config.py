# Base directories for storing images and models
# affects new uploads does not update location of already stored items
BASE_IMAGE_DIR = "/media/dj66/KINGSTON/Images"
BASE_MODEL_DIR = "/home/dj66/Documents/Honours/Models"

#Directory for temp files such as loaded datasets, the file system  its on must be able to support symlinks
WORKING_DIR ="/home/dj66/Documents/Honours/WorkingDir"

# MongoDB variables
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "TreesDB"
TREE_COLLECTION_NAME = "Trees_Test"
DATASET_COLLECTION_NAME = "Datasets"
MODEL_COLLECTION_NAME = "Models" 
ANNOTATION_COLLECTION_NAME = "Annotations"
