import os
import toml
import time
import pickle
import pymongo
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify
from urllib.request import urlopen
from pymongo.errors import DuplicateKeyError

# load config file, reference to '_config.toml', by the way, '.toml' looks nice!
config = toml.load('config.toml')

# connect mongoDB
myclient = pymongo.MongoClient(
    'mongodb://%s:%s@%s/' % (config['database']['user'],
                             config['database']['password'],
                             config['database']['address'])
)
mydb = myclient[config['database']['name']]

# read constant
SAMPLE_POINTS = config['app']['SAMPLE_POINTS']  # 图像细节取样数
MATCH_POINT = config['app']['MATCH_POINT']  # 接近1则比较严格
APP_VERSION = config['app']['version']  # show in the end of pages, showing the last modified time of this .py

app = Flask(__name__)
app.config['SECRET_KEY'] = 'some more hard work to do'


def getImageCode(imageFileCode: str) -> tuple:
    """
    Use openCV.orb model to detect and compute the image code.
    """
    fileString = imageFileCode  # .read() if it's a file and not a string
    imgArray = np.frombuffer(fileString, np.uint8)  # change from 'fromstring'
    imageGray = cv2.imdecode(imgArray, cv2.COLOR_RGB2GRAY)
    orb = cv2.ORB_create(SAMPLE_POINTS)
    keypoints, descriptors = orb.detectAndCompute(imageGray, None)
    return keypoints, descriptors  # , image


def writeDB(codes: list, words: str, passCode: str):
    timestamp = time.time()
    imageCode = pickle.dumps(codes, protocol=pickle.HIGHEST_PROTOCOL)
    mydb.aZick.insert_one({
        'dataTime': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp)),
        'timestamp': timestamp,
        'imageCode': imageCode,
        'words': words,
        'passCode': passCode
    })


def matchWithDB(code1: list, code2: list):
    """
    Use NORM_HAMMING function to match the two images, calculate the distance of vectors
    from them, and if the match points stay in a close distance, thinking they are similar.
    :param code1: list
    :param code2: list
    :return: bool
    """
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    try:
        matches = bf.knnMatch(code1, code2, k=2)
    except cv2.error:  # this could be cause by a network lag or break, i thought.
        return False
    try:
        goodMatch = [m for (m, n) in matches if m.distance < 0.8 * n.distance]
    except ValueError:  # could be network problem either, sorry...
        return False
    # if you run this locally, print a 'similarity point' could help adjusting constant for a acceptable result.
    print(len(goodMatch) / len(matches))
    if len(goodMatch) / len(matches) > MATCH_POINT:
        return True
    return False


def versionUpdate():
    """
        this function generate a version info, helps sync the local and remote files,
        if you want to use a server...
    """
    def TimeStampToTime(timestamp):
        timeStruct = time.localtime(timestamp)
        return time.strftime('%Y.%m%d.%H%M', timeStruct)

    def get_FileModifyTime(filePath):
        t = os.path.getmtime(filePath)
        return TimeStampToTime(t)

    config['app']['version'] = get_FileModifyTime('main.py')
    with open('config.toml', 'w', encoding='utf-8') as config_file:
        toml.dump(config, config_file)


"""
Flask routers
"""


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', version=APP_VERSION), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html', version=APP_VERSION), 500


@app.route('/', methods=['GET', 'POST'])
def about():
    return render_template('about.html', version=APP_VERSION)


@app.route('/maker', methods=['GET', 'POST'])
def maker():
    """
    Render the maker page.
    Accept POST JSON by ajax request, decode from BASE64 and then write to database
    """
    if request.method == 'POST':
        data = request.get_json()
        words = data['wordsArea']
        passCode = data['passArea']
        with urlopen(data['picture']) as response:  # convert base64 to array
            picture = response.read()
        imageCode = getImageCode(picture)[1]
        # print(imageCode, words, passCode)
        try:
            """
            for some reason in frontend, the pass may be duplicate,
            I set the mongoDB with 'mongoDB compass', set the 'passCode' to a UNIQUE index to catch this error.
            """
            writeDB(imageCode, words, passCode)
        except DuplicateKeyError:
            return '请尝试其他PASS', 400
        return words
    return render_template('maker.html', version=APP_VERSION)


@app.route('/passCheck', methods=['POST'])
def passCheck():
    """
    Check if the PASS available.
    """
    if request.method == 'POST':
        data = request.get_json()
        readBack = mydb.aZick.find_one({'passCode': data['passCode']})
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
    """
    Render the 'get words' page, for some historical reason, it's named 'vTag'.
    Find WORDS by the PASS client gives,
    return them to client if the image captured similar to the original one.
    There should be some middleware to process the matching for security reason,
    but as a project for fun, I leave this part to a future function.
    """
    if request.method == 'POST':
        data = request.get_json()
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
