#!/usr/bin/python

import os
import argparse
from PIL import Image


class default:
    folder   = "./data/"
    filetype = ".ppm"
    outname  = "result.jpg"
    quality  = 100
    width    = 1024


def find_all_frames(path, filetype):
    filenames = []
    path = path.rstrip("/")
    for _, _, files in os.walk(path):
        for f in sorted(files):
            if f.endswith(filetype):
                filenames.append(path+"/"+f)
    return filenames

def reduce_frames(filenames, start, number):
    if start:
        s = filenames.index(start)
        if s: 
            print("starting with frame {0} ({1})".format(start,s))
            if number > 0:
                number = min(number, len(filenames)-s-1)
                print("taking {0} frames only".format(number))
                return filenames[s:s+number]
            else:
                return filenames[s:]
    print("will take all frames")
    return filenames


def read_img(filenames):
    print("reading:")
    images = []
    for f in filenames:
        im = Image.open(f)
        print("{0} {1} {2} {3}".format(f, im.format, im.size, im.mode))
        images.append(im)
    return images


def resize(images, max_width):
    res_images = []
    num = len(images)
    nwidth = max_width//num
    for im in images:
        ratio = float(nwidth)/im.size[0]
        nheight = int(round(ratio * im.size[1]))
        out = im.resize((nwidth, nheight), resample=Image.ANTIALIAS)
        res_images.append(out)
    return res_images


def get_new_size(images):
    max_height = 0
    sum_width = 0
    for im in images:
        max_height = max(max_height, im.size[1])
        sum_width += im.size[0]
    return (sum_width,max_height)


def concatenate(images):
    nsize = get_new_size(images)
    print("creating new image with format {0}".format(nsize))
    nim = Image.new(mode="RGB", size=nsize)
    x = 0
    for im in images:
        pos = (x,0, x+im.size[0], im.size[1])
        nim.paste(im, pos)
        x += im.size[0]
    print(nim.format, nim.size, nim.mode)
    return nim


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path'   , default=default.folder)
    parser.add_argument('-o', '--outfile', default=default.outname)
    parser.add_argument('-t', '--intype' , default=default.filetype)
    parser.add_argument('-w', '--width'  , default=default.width, type=int)
    parser.add_argument('-q', '--quality', default=default.quality, type=int)
    parser.add_argument('-s', '--start'  , default=None)
    parser.add_argument('-n', '--number' , default=0, type=int)
    args = parser.parse_args()

    filenames = find_all_frames(args.path, args.intype)
    filenames = reduce_frames(filenames, args.start, args.number)
    images = read_img(filenames)
    images = resize(images,args.width)
    nim = concatenate(images)

    #nim.show()
    nim.save(args.outfile, 'JPEG', quality=args.quality)

    print("____\nDONE.")


if __name__ == "__main__": main()
