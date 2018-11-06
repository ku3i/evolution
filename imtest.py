#!/usr/bin/python
import numpy as np
import cv2

img3 = cv2.imread("./data/frame2825.ppm")
img2 = cv2.imread("./data/frame2890.ppm")
img1 = cv2.imread("./data/frame2936.ppm")

images = [img1,img2,img3]
x,y,_ = img1.shape

def get_mask_without(images):
    mask_xor = np.zeros((x,y), dtype = "uint8")
    assert(len(images)>1)
    tar = images[0]
    for im in images[1:]:
        diff = cv2.absdiff(tar, im)
        diffgray = cv2.cvtColor(diff,cv2.COLOR_BGR2GRAY)
        ret, mask = cv2.threshold(diffgray, 0, 255, cv2.THRESH_BINARY)
        mask_xor = cv2.bitwise_xor(mask_xor,mask)
    return mask_xor


def get_all_or(target,images):
    mask_or = np.zeros((x,y), dtype = "uint8")
    for im in images:
        diff = cv2.absdiff(target,im)
        diffgray = cv2.cvtColor(diff,cv2.COLOR_BGR2GRAY)
        ret, mask = cv2.threshold(diffgray, 10, 255, cv2.THRESH_BINARY)
        mask_or = cv2.bitwise_or(mask_or,mask)# !
    return mask_or

def get_all_xor(target,images):
    mask_xor = np.zeros((x,y), dtype = "uint8")
    for im in images:
        diff = cv2.absdiff(target,im)
        diffgray = cv2.cvtColor(diff,cv2.COLOR_BGR2GRAY)
        ret, mask = cv2.threshold(diffgray, 10, 255, cv2.THRESH_BINARY)
        mask_xor = cv2.bitwise_xor(mask_xor,mask)# !
    return mask_xor


def suprise(tar1,tar2):
    diff = cv2.absdiff(tar1,tar2)
    diffgray = cv2.cvtColor(diff,cv2.COLOR_BGR2GRAY)
    ret, mask = cv2.threshold(diffgray, 10, 255, cv2.THRESH_BINARY)
    return mask

wo1 = get_mask_without([img2,img3])# !
wo2 = get_mask_without([img3,img1])# !
wo3 = get_mask_without([img1,img2])# !

wi1 = cv2.bitwise_and(wo2,wo3)# !
wi2 = cv2.bitwise_and(wo1,wo3)# !
wi3 = cv2.bitwise_and(wo1,wo2)# !


wi1_ = cv2.subtract(wi1, cv2.bitwise_and(wi2,wi3))

wiall = get_all_or(img1,images)
woall = cv2.bitwise_not(wiall) # OK

tt = suprise(img1,img2)
wi3_ = cv2.subtract(wiall, suprise(img1,img2)) 
wi2_ = cv2.subtract(wiall, suprise(img1,img3))




alls = cv2.bitwise_and(cv2.bitwise_and(wi3,wi2),wi1)


result1 = cv2.bitwise_and(img1,img1, mask = wi1)# OK
result2 = cv2.bitwise_and(img2,img2, mask = wi2)# OK
result3 = cv2.bitwise_and(img3,img3, mask = cv2.subtract(wi3,wi2)) # OK

foreground = cv2.add(result3, cv2.add(result2,result1)) # OK
background = cv2.bitwise_and(img1,img1, mask = woall) # OK

final = cv2.add(foreground,background)

small_1 = cv2.resize(wi1, (0,0), fx=0.5, fy=0.5) 
small_2 = cv2.resize(wi2, (0,0), fx=0.5, fy=0.5) 
small_3 = cv2.resize(wi3, (0,0), fx=0.5, fy=0.5) 

cv2.imshow('1',small_1 )
cv2.imshow('2',small_2 )
cv2.imshow('3',small_3 )
#cv2.imshow("test", test)


cv2.waitKey(0)
cv2.destroyAllWindows()
