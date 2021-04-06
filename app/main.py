import os
import json
import time
import pickle
import pymongo
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, redirect, url_for
from urllib.request import urlopen
from pymongo.errors import DuplicateKeyError

with open('config.json', encoding='utf-8') as config_file:
    config = json.load(config_file)

myclient = pymongo.MongoClient(
    'mongodb://%s:%s@%s/' % (config['database']['user'],
                             config['database']['password'],
                             config['database']['address'])
)
mydb = myclient[config['database']['name']]

SAMPLE_POINTS = config['app']['SAMPLE_POINTS']  # 图像细节取样数
MATCH_POINT = config['app']['MATCH_POINT']  # 接近1则比较严格
APP_VERSION = config['app']['version']

app = Flask(__name__)
app.config['SECRET_KEY'] = 'some more hard work to do'


def getImageCode(imageFile):
    fileString = imageFile  # .read() if it's a file and not a string
    imgArray = np.frombuffer(fileString, np.uint8)  # change from 'fromstring'
    imageGray = cv2.imdecode(imgArray, cv2.COLOR_RGB2GRAY)
    orb = cv2.ORB_create(SAMPLE_POINTS)
    keypoints, descriptors = orb.detectAndCompute(imageGray, None)
    return keypoints, descriptors  # , image


def writeDB(codes, words, passCode):
    timestamp = time.time()
    imageCode = pickle.dumps(codes, protocol=pickle.HIGHEST_PROTOCOL)
    mydb.aZick.insert_one({
        'dataTime': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp)),
        'timestamp': timestamp,
        'imageCode': imageCode,
        'words': words,
        'passCode': passCode
    })


def matchWithDB(code1, code2):
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    try:
        matches = bf.knnMatch(code1, code2, k=2)
    except cv2.error:
        return False
    goodMatch = [m for (m, n) in matches if m.distance < 0.8 * n.distance]
    print(len(goodMatch) / len(matches))
    if len(goodMatch) / len(matches) > MATCH_POINT:
        return True
    return False


def TimeStampToTime(timestamp):
    timeStruct = time.localtime(timestamp)
    return time.strftime('%Y.%m%d.%H%M', timeStruct)


def get_FileModifyTime(filePath):
    t = os.path.getmtime(filePath)
    return TimeStampToTime(t)


config['app']['version'] = get_FileModifyTime('main.py')
with open('config.json', 'w', encoding='utf-8') as config_file:
    json.dump(config, config_file, ensure_ascii=False, indent=4)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', version=APP_VERSION), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html', version=APP_VERSION), 500


@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect(url_for('vTag'))
    # if request.method == 'POST':
    #     data = request.get_json()
    #     passCode = data['passArea']
    #     readBack = mydb.aZick.find_one({'passCode': passCode})
    #     try:  # try to get image code from database
    #         readCode = pickle.loads(readBack['imageCode'])
    #     except TypeError:
    #         return '没有这个!PASS'
    #     else:
    #         with urlopen(data['picture']) as response:  # convert base64 to array
    #             picture = response.read()
    #         if matchWithDB(readCode, getImageCode(picture)[1]):  # compare incoming picture with database
    #             return readBack["words"]
    #         else:
    #             return '图片PASS不匹配'
    # return render_template('index.html')


@app.route('/maker', methods=['GET', 'POST'])
def maker():
    if request.method == 'POST':
        data = request.get_json()
        words = data['wordsArea']
        passCode = data['passArea']
        with urlopen(data['picture']) as response:  # convert base64 to array
            picture = response.read()
        imageCode = getImageCode(picture)[1]
        print(imageCode, words, passCode)
        try:
            writeDB(imageCode, words, passCode)
        except DuplicateKeyError:
            # raise Exception('请尝试其他PASS')
            return '请尝试其他PASS', 400
        return words
    return render_template('maker.html', version=APP_VERSION)


@app.route('/passCheck', methods=['POST'])
def passCheck():
    if request.method == 'POST':
        data = request.get_json()
        readBack = mydb.aZick.find_one({'passCode': data['username']})
        if readBack:
            resp = jsonify('PASS unavailable')
            resp.status_code = 200
            return resp
        else:
            resp = jsonify('')
            resp.status_code = 200
            return resp


@app.route('/vTag', methods=['GET', 'POST'])
def vTag():
    if request.method == 'POST':
        data = request.get_json()
        # print(data)
        passCode = data['passArea']
        readBack = mydb.aZick.find_one({'passCode': passCode})
        try:  # try to get image code from database
            readCode = pickle.loads(readBack['imageCode'])
        except TypeError:
            return '没有这个!PASS'
        else:
            with urlopen(data['picture']) as response:  # convert base64 to array
                picture = response.read()
            if matchWithDB(readCode, getImageCode(picture)[1]):  # compare incoming picture with database
                return readBack["words"]
            else:
                return ''
    return render_template('vtag.html', version=APP_VERSION)


if __name__ == '__main__':
    app.run()
