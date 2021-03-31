import time
import pickle
import pymongo
import cv2
import numpy as np
from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from urllib.request import urlopen

SAMPLE_POINTS = 200  # 图像细节取样数
MATCH_POINT = 0.1  # 接近1则比较严格

myclient = pymongo.MongoClient('mongodb://xdream:sima5654@192.168.50.22/')
mydb = myclient['zickme']

app = Flask(__name__)
app.config['SECRET_KEY'] = 'some more hard work to do'
bootstrap = Bootstrap(app)


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
    matches = bf.knnMatch(code1, code2, k=2)
    goodMatch = [m for (m, n) in matches if m.distance < 0.8 * n.distance]
    print(len(goodMatch) / len(matches))
    if len(goodMatch) / len(matches) > MATCH_POINT:
        return True
    return False


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.get_json()
        picture = data['picture']
        passCode = data['passArea']
        readBack = mydb.aZick.find_one({'passCode': passCode})
        try:                                 # try to get image code from database
            readCode = pickle.loads(readBack['imageCode'])
        except TypeError:
            return '没有这个pass！'
        else:
            with urlopen(picture) as response:  # convert base64 to array
                picture = response.read()
            if matchWithDB(readCode, getImageCode(picture)[1]):  # compare incoming picture with database
                return readBack["words"]
            else:
                return '图片密码不匹配'
    return render_template('index.html')


@app.route('/maker', methods=['GET', 'POST'])
def maker():
    if request.method == 'POST':
        data = request.get_json()
        picture = data['picture']
        words = data['wordsArea']
        passCode = data['passArea']
        with urlopen(picture) as response:      # convert base64 to array
            picture = response.read()
        imageCode = getImageCode(picture)[1]
        print(imageCode, words, passCode)
        writeDB(imageCode, words, passCode)
        return words
    return render_template('maker.html')


if __name__ == '__main__':
    app.run()
