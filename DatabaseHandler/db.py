from pymongo import MongoClient
from config import MONGO_URI, DB_NAME, TREE_COLLECTION_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
tree_collection = db[TREE_COLLECTION_NAME]

def insert_image_metadata(doc):
    result = tree_collection .insert_one(doc)
    return result.acknowledged



def get_all_images():
    return list(tree_collection.find({}))


def insert_dataset(data):