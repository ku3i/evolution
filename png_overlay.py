#!/usr/bin/python

import imageio

im1 = imageio.imread('data/frame2500.ppm')
im2 = imageio.imread('data/frame2520.ppm')
im3 = imageio.imread('data/frame2540.ppm')
print(im1.shape)


re = 0.3*im1 + 0.3*im2 + 0.3*im3
print(re.shape)

imageio.imwrite('result.jpg', re)
