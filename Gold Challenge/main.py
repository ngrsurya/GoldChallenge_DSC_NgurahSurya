import re
import string
from flask import Flask, jsonify, request #import objects from the Flask model
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flasgger import swag_from
import numpy as np

import pandas as pd
import sqlite3 as sql



app = Flask(__name__) #define app using Flask
app.json_encoder = LazyJSONEncoder

swagger_template = dict(
    info = {
        'title': LazyString(lambda:'API Data Cleansing Hate Speech Twitter Gold Challenge'),
        'version': LazyString(lambda:'1.0.0'),
        'description': LazyString(lambda:'Dokumentasi Cleansing data hate speech')
        }, host = LazyString(lambda: request.host)
)

swagger_config = {
        "headers":[],
        "specs":[
            {
            "endpoint":'docs',
            "route":'/docs.json'
            }
        ],
        "static_url_path":"/flasgger_static",
        "swagger_ui":True,
        "specs_route":"/docs/"
}
swagger = Swagger(app, template=swagger_template, config=swagger_config)
# ===============================================================================
#IMPORT CSV FILE
def filterAbusive():
    list_abusive = pd.read_csv('abusive.csv')
    list_abusive = pd.read_csv('abusive.csv')
    list_abusive = list_abusive['ABUSIVE'].str.lower().tolist()
    return list_abusive

def filterAlay():
    list_kamusalay = pd.read_csv('new_kamusalay.csv', encoding= 'unicode_escape')
    list_alay = list_kamusalay['anakjakartaasikasik'].str.lower().tolist()
    return list_alay

def filterAlayFix():
    list_kamusalay = pd.read_csv('new_kamusalay.csv', encoding= 'unicode_escape')
    list_alay_fix = list_kamusalay['anak jakarta asyik asyik'].str.lower().tolist()
    return list_alay_fix

# ===============================================================================
# FILTERING/CLEANSING WORD

def filterBadWord(val):
    i = val
    i = val.lower()
    list_abusive = filterAbusive()
    for j in list_abusive:
        if j in i:
            holder = i.replace(j, '*******')
            val = holder
            i = holder
    print(val)
    return val

def filterListBadWord(val):
    list_abusive = filterAbusive()
    for i in val:
        for j in list_abusive:
            if j in i:
                holder = val[val.index(i)].replace(j,'*******')
                val[val.index(i)] = holder
                i = holder
    return val


def filterAlayWord(val):
    list_alay = filterAlay()
    list_alay_fix = filterAlayFix()
    val = val.lower()
    i = val
    for j in list_alay:
        if j in i:
            a = list_alay.index(j)
            print(a)
            k = val.replace(j,list_alay_fix[a])
            val = k
            i = k
            break

    return val

def filterListAlayWord(val):
    list_alay = filterAlay()
    list_alay_fix = filterAlayFix()
    for i in val:
        for j in list_alay:
            if j in i:
                print(i)
                a = list_alay.index(j)
                k = val[val.index(i)].replace(j,list_alay_fix[a])
                val[val.index(i)] = k
                break
    return val

# ===============================================================================
# MY SQL FUNCTION

def inputToTable(val):
    _database = sql.connect('gold.db')
    _database.execute(''' insert into text_cleansing (teks) values (?) ''', (val,))
    _database.commit()
    _database.close()

def inputListTable(val):
    for i in val:
        inputToTable(i)


def getAllTableData():
    _database = sql.connect('gold.db')
    query = ''' select * from text_cleansing '''
    df = pd.read_sql_query(query, _database)
    _database.commit()
    _database.close()
    df_file = pd.DataFrame(df).to_numpy()
    return df_file.tolist()


def getTableDataByID(val):
    _database = sql.connect('gold.db')
    query = """ select * from text_cleansing where teksID  = (?) """,(val,)
    df = _database.execute(*query)
    _database.commit()
    df = df.fetchall()
    _database.close()
    return df

# ===============================================================================
def importFileCsv(val):
    input_file = pd.read_csv(val, encoding='latin-1')
    tweet_file = input_file[['Tweet']]
    tweet_list = tweet_file['Tweet'].tolist()
    for j in tweet_list:
        a = tweet_list.index(j)
        j = str(j).lower()
        j = re.sub("[,]", "", j)
        j = re.sub("[.]", "", j)
        j = re.sub("[]]", "", j)
        j = re.sub("[[]", "", j)
        j = re.sub("[?]", "", j)
        j = re.sub("[!]", "", j)
        j = re.sub("[\"]", "", j)
        j = re.sub("[']", "", j)
        j = re.sub("[;]", "", j)
        j = re.sub("[_]", "", j)
        j = re.sub("[||]", "", j)
        j = re.sub("[+]", "", j)
        j = re.sub("[#]", "", j)
        j = re.sub("[(]", "", j)
        j = re.sub("[)]", "", j)
        j = re.sub("[ð]", "", j)
        j = re.sub(r'^\s*(-\s*)?|(\s*-)?\s*$', '', j)
        tweet_list[a] = j
    return tweet_list
#===============================================================================
#SWAGGER UI CODE
#===============================================================================

#POST METHOD
@swag_from("docs/text_post.yml", methods=['POST'])
@app.route('/post_text', methods=['POST'])
def addOne():
    text = request.form.get('text')
    print(text) 
    filteredWord = filterBadWord(text)
    filteredWord = filterAlayWord(filteredWord)
    inputToTable(filteredWord)
    return jsonify({'text ' : filteredWord})


@swag_from("docs/text_file.yml", methods=['POST'])
@app.route('/post_file', methods=['POST'])
def addFile():
    file = request.files['file']
    input_file = importFileCsv(file)
    input_file = filterListBadWord(input_file)
    input_file = filterListAlayWord(input_file)
    inputListTable(input_file)
    return jsonify({'text file uploaded ' : input_file})

#GET METHOD 
@swag_from("docs/get_file.yml", methods=['GET'])
@app.route('/get_text', methods=['GET'])
def readAllFile():
    returnData = getAllTableData()
    return jsonify({'data ' : returnData})
    
@swag_from("docs/get_file_id.yml", methods=['GET'])
@app.route('/get_text/<string:idText>', methods=['GET'])
def readFileByID(idText):
    dataToReturn = getTableDataByID(idText)
    return jsonify({'data ' : dataToReturn})
    
#===============================================================================
if __name__ == '__main__':
    app.run() #run app on port 8080 in debug mode