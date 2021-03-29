import os
import time
import cv2
import numpy as np
import matplotlib.pyplot as plt

FILE_TYPE = ['jpg', 'png']
SAMPLE_POINTS = 100  # 图像细节取样数量
STRICT_LEVEL = 0.8  # 接近1则比较宽松
MATCH_POINT = 0.65  # 接近1则比较严格


def getImageCode(imagePath):
    image = cv2.imread(imagePath, cv2.IMREAD_GRAYSCALE)
    orb = cv2.ORB_create(SAMPLE_POINTS)
    keypoints, descriptors = orb.detectAndCompute(image, None)
    # print(f'image descriptors:\n'
    #       f'{descriptors}\n'
    #       f'length:{len(descriptors)}\n'
    #       f'{descriptors.shape=}')
    # np.save('arraySave.npy', descriptors)
    return keypoints, descriptors, image


def getFileList(fullPath):
    onlyPath = fullPath.rsplit('/', 1)[0]
    fileList = [x for x in os.listdir(onlyPath) if x.rsplit('.')[-1] in FILE_TYPE]
    return [onlyPath + '/' + x for x in fileList]


def compareImage(imageOrigin, image2):
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    _image2Code = getImageCode(image2)
    _matches = bf.knnMatch(imageOrigin[1], _image2Code[1], k=2)
    _goodMatch = [m for (m, n) in _matches if m.distance < 0.8 * n.distance]
    return len(_goodMatch) / len(_matches), _goodMatch, _matches, _image2Code


if __name__ == '__main__':
    start = time.time()
    originImagePath = 'data/images/EM5X2108.png'
    originImageCode = getImageCode(originImagePath)
    np.save('arraySave.npy', originImageCode[1])
    # codeLoad = np.load('arraySave.npy')
    for file in getFileList(originImagePath):
        similarity, goodMatch, matches, image2Code = compareImage(originImageCode, file)
        print(file, 'similar to original is ', similarity)
        if similarity > MATCH_POINT and similarity != 1:
            print('MATCH!')
            compareImg = cv2.drawMatches(
                originImageCode[2], originImageCode[0],
                image2Code[2], image2Code[0],
                goodMatch, image2Code[2],
                flags=2
            )
            plt.figure(file)
            plt.imshow(compareImg,)
            plt.grid(True)
    end = time.time()
    print('程序运行时间：%s' % (end - start))
    plt.show()
