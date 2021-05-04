import json
import os
import csv
########################### write data ###########################          
def write_csv(dict_order,filename): #'log.csv'
    csv_columns=[]
    for i in dict_order.keys():
        csv_columns.append(i)
    if(os.path.isfile(filename) == False):
        with open(filename, 'w', newline='') as csv_object: 
            writer = csv.DictWriter(csv_object, fieldnames=csv_columns)
            writer.writeheader()
            writer.writerow(dict_order) 
    else:
        with open(filename, 'a', newline='') as csv_object: 
            writer = csv.DictWriter(csv_object, fieldnames=csv_columns)
            writer.writerow(dict_order)   
        
def load_json(filename):#'data.json'
    order={}
    if(os.path.isfile(filename) == True):
        with open(filename) as infile:
            order = json.load(infile)   
    return order
        
def save_json(order,filename): 
    with open(filename, 'w') as outfile: 
        json.dump(order, outfile)