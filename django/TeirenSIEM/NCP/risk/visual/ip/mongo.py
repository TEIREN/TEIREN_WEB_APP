from pymongo import MongoClient, ASCENDING, DESCENDING
from django.conf import settings
import datetime
import json
import time
import psutil

client = MongoClient (
    host = settings.MONGODB['HOST'],
    port = settings.MONGODB['PORT'],
    username = settings.MONGODB['USERNAME'],
    password = settings.MONGODB['PASSWORD']
)

def get_db_handle(db_name):
    global client
    db_handle = client[db_name]
    return db_handle

def get_collection_handle(db_handle,collection_name):
    return db_handle[collection_name]

def get_log_detail(request):
    cloud = request['cloud']
    id = request['id']
    global client
    db = client['ts_db']
    collection = db[cloud]
    result = list(collection.find({'historyId': id}).sort('historyid', DESCENDING).limit(1))[0]
    response = {'id': id , 'details': result}
    return response