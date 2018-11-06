#!/usr/bin/python
import numpy as np
import cv2

img1 = cv2.imread("./data/frame2825.ppm")
img2 = cv2.imread("./data/frame2890.ppm")
img3 = cv2.imread("./data/frame2936.ppm")

images = [img1,img2,img3]


s1 = cv2.addWeighted(img1,0.7,img2,0.3,0)
s2 = cv2.addWeighted(s1  ,0.7,img3,0.3,0)


small_1 = cv2.resize(img1, (0,0), fx=0.5, fy=0.5) 
small_2 = cv2.resize(s1, (0,0), fx=0.5, fy=0.5) 
small_3 = cv2.resize(s2, (0,0), fx=0.5, fy=0.5) 

cv2.imshow('1',small_1 )
cv2.imshow('2',small_2 )
cv2.imshow('3',small_3 )


cv2.waitKey(0)
cv2.destroyAllWindows()
