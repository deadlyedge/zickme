import time
import pickle
import pymongo
import cv2
import numpy as np
from pymongo.errors import DuplicateKeyError
from quart import Quart, render_template, request, jsonify
from urllib.request import urlopen

SAMPLE_POINTS = 200  # 图像细节取样数
MATCH_POINT = 0.1  # 接近1则比较严格

myclient = pymongo.MongoClient('mongodb://xdream:sima5654@192.168.50.22/')
mydb = myclient['zickme']

app = Quart(__name__)
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
    matches = bf.knnMatch(code1, code2, k=2)
    goodMatch = [m for (m, n) in matches if m.distance < 0.8 * n.distance]
    print(len(goodMatch) / len(matches))
    if len(goodMatch) / len(matches) > MATCH_POINT:
        return True
    return False


@app.errorhandler(404)
async def page_not_found(e):
    return await render_template('404.html'), 404


@app.errorhandler(500)
async def internal_server_error(e):
    return await render_template('500.html'), 500


@app.route('/', methods=['GET', 'POST'])
async def index():
    if request.method == 'POST':
        data = await request.get_json()
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
                return '图片PASS不匹配'
    return await render_template('index.html')


@app.route('/maker', methods=['GET', 'POST'])
async def maker():
    if request.method == 'POST':
        data = await request.get_json()
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
    return await render_template('maker.html')


@app.route('/passCheck', methods=['POST'])
async def passCheck():
    if request.method == 'POST':
        data = await request.get_json()
        readBack = mydb.aZick.find_one({'passCode': data['username']})
        if readBack:
            resp = jsonify('PASS unavailable')
            resp.status_code = 200
            return resp
        else:
            resp = jsonify('')
            resp.status_code = 200
            return resp


if __name__ == '__main__':
    app.run()
