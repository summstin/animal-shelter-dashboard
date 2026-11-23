# Example Python Code to Insert a Document 

from pymongo import MongoClient 
from bson.objectid import ObjectId 

class AnimalShelter(object): 
    """ CRUD operations for Animal collection in MongoDB """ 

    def __init__(self): 
        # Initializing the MongoClient. This helps to access the MongoDB 
        # databases and collections. This is hard-wired to use the aac 
        # database, the animals collection, and the aac user. 
        # 
        # You must edit the password below for your environment. 
         
        # Connection Variables 
         
        USER = 'aacuser' 
        PASS = 'aactest' 
        HOST = 'localhost' 
        PORT = 27017 
        DB = 'aac' 
        COL = 'animals' 
        
        # Initialize Connection 
        
        self.client = MongoClient('mongodb://%s:%s@%s:%d' % (USER,PASS,HOST,PORT)) 
        self.database = self.client['%s' % (DB)] 
        self.collection = self.database['%s' % (COL)] 
        
    # Create a method to return the next available record number for use in the create method
            
    # create method 
    def create(self, data):
        if data is not None and isinstance(data, dict): # check to ensure data is dictionary and not empty
            # inserts into data, returns true
            try:
                self.database.animals.insert_one(data)
                return True
            # prints error, returns false
            except: 
                print("Create error")
                return False
        else:
            return False

    # read method
    def read(self, query):
        results = [] # empty array
        # ensures a query is given
        if query is not None:
            # indexes the data that matches the query
            try:
                cursor = self.database.animals.find(query)
                # combines the data together into one document
                for document in cursor:
                    results.append(document)
                # returns results of query
                return results
            # prints error, returns empty array
            except: 
                print("Read error")
                return []
            # returns empty array
        else:
            return []
    # update method
    def update(self, query, new_values, multiple=False):
        # ensures an adequate query and replacement is given as well as dictionary
        if query is not None and new_values is not None and isinstance(query,dict) and isinstance(new_values, dict):
            try:
                # updates all matching queries with the new value
                if multiple:
                    result = self.database.animals.update_many(query, new_values)
                # updates first matching query found with new value 
                else:
                    result = self.database.animals.update_one(query, new_values)
                # returns count of result  
                return result.modified_count
            # prints error, returns 0
            except: 
                print("Update error")
                return 0
        # returns 0
        else:
            return 0
        
    # delete method
    def delete(self, query, multiple=False):
        # ensures an adequate query is given as well as dictionary
        if query is not None and isinstance(query,dict):
            try:
                # deletes all matching queries
                if multiple:
                    result = self.database.animals.delete_many(query)
                # deletes first matching query found
                else:
                    result = self.database.animals.delete_one(query)
                # returns count of result
                return result.deleted_count
            # prints error, returns 0
            except: 
                print("Delete error")
                return 0
            # returns 0
        else:
            return 0