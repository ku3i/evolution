#!/usr/bin/python
import numpy as np
import cv2

from cv2 import bitwise_and as AND
from cv2 import bitwise_or as OR
from cv2 import bitwise_not as NOT
from cv2 import subtract as SUB

from copy import deepcopy

from frames2image import find_all_frames, reduce_frames


filenames = find_all_frames("./data/wide/", ".ppm")
filenames = reduce_frames(filenames, None, 5, 25)

print(len(filenames))

images = [cv2.imread(f) for f in filenames]

images16 = [(i/256.).astype('float32') for i in images]

sets = range(len(images))

x,y,c = images[0].shape
bwshape = (x,y)
colorshape = (x,y,c)

def blank_mask(shape = bwshape):
    return np.zeros(shape, dtype = "uint8")

def white_mask(shape = bwshape):
    return 255*np.ones(shape, dtype = "uint8")

def or_all(masks):
    mask_or = blank_mask()
    for m in masks:
        mask_or = OR(mask_or, m)
    return mask_or


def show(imag):
    im2show = []
    for e in imag:
        small = cv2.resize(e, (0,0), fx=0.5, fy=0.5)
        im2show.append(small)
    
    for k,im in enumerate(im2show):
        cv2.imshow(str(k), im)


def waitshow(img):
    cv2.imshow("foo", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    exit()

def union(tar1,tar2):
    diff = cv2.absdiff(tar1,tar2)
    diffgray = cv2.cvtColor(diff,cv2.COLOR_BGR2GRAY)
    ret, mask = cv2.threshold(diffgray, 0.00000001, 1.0, cv2.THRESH_BINARY)
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)
    also do erode
    #waitshow(mask)

    return (255*mask).astype('uint8')


def create_union((i, j)):
    return union(images16[i],images16[j])


# def find_pairs(tuples):
#     #print("valid pairs")
#     pairs = {}
#     for i,u in enumerate(tuples):
#         start = tuples.index(u)+2 # TODO improve here
#         for j,v in enumerate(tuples[start:]):
#             c = get_common_item(u,v)
#             if c is not None:
#                 if c in pairs:
#                     #print("appen")
#                     pairs[c].append((i,j+start))
#                 else:
#                     pairs[c] = [(i,j+start)]
#                 #pairs.append((u,v))
#    return pairs

def find_pairs_2(tuples):
    pairs = {}
    for r in sets:
        for idx,t in enumerate(tuples):
            if r == t[0] or r == t[1]: #valid tuple
                if r in pairs:
                    #print("appen")
                    pairs[r].append(idx)
                else:
                    pairs[r] = [idx]
    # TODO sort pairs by max distance,
    return pairs

def find_pairs_3(tuples):
    pairs = {}
    for r in sets:
        for idx,t in enumerate(tuples):
            if r == t[0] or r == t[1]: #valid tuple
                tup = (idx, float(abs(t[0]-t[1])))
                if r in pairs:
                    pairs[r].append(tup)
                else:
                    pairs[r] = [tup]
    return pairs


tuples = []
allunions = []

N = len(sets)

for i in sets:
    start = sets.index(i)
    for j in sets[start:]:
        if i is not j:
            tuples.append((i,j))
            u = create_union((i,j))
            allunions.append(u)

#print("tuples")
#for i,t in enumerate(tuples):
    #print("{0}: {1}".format(i, t))

assert len(tuples) == (N*N -N)//2

# find pairs
pairs = find_pairs_3(tuples)
for key, value in pairs.items():
    value = sorted(value, key=lambda x: x[1], reverse=True)
    value = value[:2]
    print(value)


# ------------------------------

exim = []

for key, value in pairs.items():
    #print("creating ", value)
    di = white_mask()
    for v in value: # value is a list if indeces, actually
        #iu = allunions[v[0]]
        #iv = allunions[v[1]]
        im = allunions[v[0]]
        di = AND(di,im)
        #mm = AND(iu,iv)
    #di = AND(di,mm)
    exim.append(di)

assert len(exim) == len(pairs)


result = []
temp = blank_mask()
for e in reversed(exim):
    last = deepcopy(temp)
    temp = OR(last, e)
    res  = SUB(temp, last)
    result.append(res)

# create foreground
imparts = []
foreground = blank_mask(colorshape)
for j,im in enumerate(images):
    mask = result[-j-1]
    p = AND(im,im, mask = mask)
    imparts.append(p)
    #foreground = cv2.addWeighted(foreground,0.5, p,0.5,0)
    foreground = cv2.add(foreground,p)

# create background
a = or_all(allunions)
nota = NOT(a)
background = AND(images[0],images[0], mask = nota)

final = cv2.add(foreground,background)



show(exim)

cv2.imshow("final", final)

cv2.waitKey(0)
cv2.destroyAllWindows()
