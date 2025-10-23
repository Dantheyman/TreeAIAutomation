from pymongo import MongoClient
from pymongo.errors import PyMongoError
from config import MONGO_URI, DB_NAME, TREE_COLLECTION_NAME,DATASET_COLLECTION_NAME, MODEL_COLLECTION_NAME, ANNOTATION_COLLECTION_NAME
import random
from bson import ObjectId
from datetime import datetime


client = MongoClient(MONGO_URI)
db = client[DB_NAME]
tree_collection = db[TREE_COLLECTION_NAME]
dataset_collection = db[DATASET_COLLECTION_NAME]
model_collection = db[MODEL_COLLECTION_NAME]
annotation_collection = db[ANNOTATION_COLLECTION_NAME]

#This file handles direct interactions with the database 



######################## Non-Specific Methods ########################

#generates a unique id
# return: id string
def generate_id():
    return str(ObjectId())

# Perform a dynamic find query.
# param: collection: The collection to run query on 
# param: field_filters: Dict of exact matches, e.g., {"location": "auckland"}
# param: range_filters: Dict of range filters, e.g., {"capture_date": {"gte": "2024-12-01", "lte": "2024-12-05"}}
# return: Cursor to the matching documents        
def dynamic_find(collection, exact_filters, range_filters):

    query = {}
    # Exact match fields
    if exact_filters:
        query.update(exact_filters)

    # Range filters
    if range_filters:
        for field, conditions in range_filters.items():
            range_query = {}
            if "gte" in conditions:
                range_query["$gte"] = conditions["gte"]
            if "lte" in conditions:
                range_query["$lte"] = conditions["lte"]
            query[field] = range_query
    return collection.find(query)


# query's a collection using ID
# param: collection: The collection to run query on
# param: id_list: Array of ids to be queried 
# return: Cursor to the matching documents
def id_find(collection,id_list):
    return collection.find({"_id": {"$in": id_list}})


######################## Image Related Methods ########################

# Insert Image Metadata into tree collection
# param: doc: the Document to be inserted
# return: success status of insertion
def insert_image_metadata(doc):
    try:
        result = tree_collection .insert_one(doc)
        return result.acknowledged
    except PyMongoError as e:
        return False

# Get a list of photos from db
# param: id_list: list of photo id's
# return: Cursor to the matching documents
def get_photos(id_list):
    return id_find(tree_collection, id_list)

######################## Dataset Related Methods ########################

# generate a dataset given the filters provided 
# param: filters: Dict of filters should follow syntax of 
#{
#   "exact":{
#             "field": "exact value"
#           },
#   "range":{
#             "field": {"gte": "max value", "lte": "min value"}
#           }
#}
# param: split: String represeting the Train/Test/Val Split 
# return: Id of dataset created, returns 0 if an error occurs
def create_dataset(filters,split,name,classes):
    try:

        #verify name

        if dataset_name_exists(name):
            return 0 

        # Insert an empty document 
        id = generate_id()
        created_at_str = datetime.now().strftime("%Y-%m-%d")
        dataset_collection.insert_one({"_id": id, "created_at": created_at_str})
       
        #get photos with regards to filters
        exact_filters = filters.get("exact", {})
        range_filters = filters.get("range", {})
       
        photos = dynamic_find(tree_collection, exact_filters,range_filters)
    
        photos = list(photos)
    
        #turn classes into a list
        classes = classes.split(",")
       

        # split photos up into Train,Test, and Validation sets
        random.shuffle(photos)

        train = int(split.split("/")[0])*0.01
        val = int(split.split("/")[2])*0.01
 

        total = len(photos)
        train_end = int(total * train)
        val_end = train_end + int(total * val)

        train_set = photos[:train_end]
        val_set = photos[train_end:val_end]
        test_set = photos[val_end:]

       
        # Update the dataset document with the photo IDs
        train_photo_ids = [photo["_id"] for photo in train_set]
        test_photo_ids = [photo["_id"] for photo in test_set]
        val_photo_ids = [photo ["_id"] for photo in val_set]
       
        dataset_collection.update_one(
            {"_id": id},
            {
                "$set": {
                    "classes": classes,
                    "train_photos": train_photo_ids,
                    "test_photos": test_photo_ids,
                    "val_photos": val_photo_ids,
                    "name": name
                }
            }
        )
        
        return id 
        
    except PyMongoError as e:
        return 0


# determines if a dataset name already exists in the database
# param: name: name to be checked 
# return: boolean of existing status 
def dataset_name_exists(name):
    
    count = dataset_collection.count_documents({"name": name})
    if count > 0:
        return True
    return False

#retrieves dataset document from db based on name
# param: name: name of dataset
# return: Cursor to the matching document
def get_dataset_from_name(name):
    return dataset_collection.find_one({"name": name} )


# Gets all dataset names
# return: list of all dataset names in order A-Z
def get_all_dataset_names():
    
    all_datasets = dataset_collection.find({}, {"name": 1}).sort("name", 1)
    names = [doc["name"] for doc in all_datasets if "name" in doc]
    return names


# Removes a photo from a dataset, to be used when no annotations can be generated
# param: dataset_id: id of dataset
# param photo_id: id of photo
def remove_photo_from_dataset(dataset_id, photo_id):

    query = {"_id": dataset_id}

    changes = [{"$pull": {"train_photos": photo_id}}, {"$pull": {"test_photos": photo_id}},{"$pull": {"val_photos": photo_id}} ]

    for change in changes:
        result = dataset_collection.update_one(query,change)
        if result.modified_count > 0:
            print(f"Removed photo_id {photo_id} from dataset {dataset_id}")
            return 
    
    raise Exception("Failed to removed photo_id: {photo_id}, from dataset {dataset_id}: ")

# Gets a dataset based of dataset id
# param: dataset_id: dataset id
# return: Cursor to the matching document
def get_dataset_from_id(dataset_id):
    return dataset_collection.find_one({"_id": dataset_id})


######################## Annotation Related Methods ########################

# Saves annotation to database
# param: document: document containing annotations, classes, and photo id
# return: boolean indicating success
def save_annotations(document):
    
    try:
        annotation_id = generate_id()
        created_at_str = datetime.now().strftime("%Y-%m-%d")
        document["_id"] = annotation_id
        document["created_at"] = created_at_str 
        annotation_collection.insert_one(document)
        return True
    except:
        return False


# Retrieves annotations for a given photo 
# param: photo_id: photo id
# return: Cursor to the matching documents
def get_annotations_for_photo(photo_id):

  return annotation_collection.find({"photo_id" : photo_id })


######################## Model Related Methods ########################

# Saves a model to the database
# param: model_doc: document containing all info sent by IPS
# return: id of model
def save_model(model_doc):
    model_id = generate_id()
    model_doc["_id"] = model_id
    model_doc["base_model"] = False
    model_collection.insert_one(model_doc)
    return model_id

# saves path of model weights to the corresponding model document
# param: model_id: id of the model
# param: file_path: path to model weights 
def save_model_path(model_id,file_path):
    model_collection.update_one({"_id": model_id},{"$set": {"path": file_path}})

# returns a list of all models
# return: list of all models
def get_all_models():
    return list(model_collection.find({}))

# gets the path to a models weights
# param: model_name: name of the model
# return: path to model weights
def get_model_path(model_name):
    model = model_collection.find_one({"name":model_name})
    return model["path"]

# determines if a model name already exists in the database
# param: model_name: name to be checked 
# return: boolean of existing status 
def model_name_exists(model_name):
    count = model_collection.count_documents({"name": model_name})
    if count > 0:
        return True
    return False




