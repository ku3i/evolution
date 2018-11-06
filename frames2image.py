#!/usr/bin/python

"""
    This script draws the recorded frames from the 'path' folder into a single sequence image.

    example:

        ./frames2image.py -p ./data/ -s frame0791.ppm -n 10 -x 2 -c 250 -v

        + folder: ./data/
        + starting at specific frame
        + 10 images
        + take only every 2nd frame
        + crop to 250 px width
        + be verbose
"""


import os
import argparse
from PIL import Image


class default:
    folder   = "./data/"
    filetype = ".ppm"
    outname  = "result.jpg"
    quality  = 100
    width    = 2048


def find_all_frames(path, filetype):
    filenames = []
    path = path.rstrip("/")
    for f in sorted(os.listdir(path)):
        if f.endswith(filetype):
            filenames.append(path+"/"+f)
    if len(filenames) == 0:
        print("no images found.")
        exit()
    return filenames


def reduce_frames(filenames, start, number, step):
    print("stepsize is "+str(step))
    if start:
        try:
            s = filenames.index(start)
        except:
            print("WARNING: invalid start frame.")
            s = 0
    else:
        s = 0

    print("starting with frame {0} (index:{1})".format(start,s))
    if number > 0:
        number = min(number, len(filenames)-s-1)
        print("taking {0} frames only".format(number))
        return filenames[s:s+number*step-1:step]
    else:
        return filenames[s::step]

    print("will take all frames")
    return filenames[::step]


def read_img(filenames):
    print("reading:")
    images = []
    for idx,f in enumerate(filenames):
        im = Image.open(f)
        print("{4:2d}: {0} format:{1} size:{2} color:{3}".format(f, im.format, im.size, im.mode, idx))
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


def crop(images, cropw):
    if cropw == 0:
        return images
    res_images = []
    for im in images:
        b = min(im.size[0], cropw)
        box = (im.size[0]//2-b//2, 0, im.size[0]//2+b//2, im.size[1])
        print(box)
        out = im.crop(box)
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
    parser.add_argument('-w', '--width'  , default=default.width  , type=int)
    parser.add_argument('-q', '--quality', default=default.quality, type=int)
    parser.add_argument('-s', '--start'  , default=None)
    parser.add_argument('-n', '--number' , default=0, type=int)
    parser.add_argument('-x', '--step'   , default=1, type=int)
    parser.add_argument('-c', '--crop'   , default=0, type=int)
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    filenames = find_all_frames(args.path, args.intype)
    filenames = reduce_frames(filenames, args.path+args.start, args.number, args.step)
    images = read_img(filenames)
    images = crop(images, args.crop)
    images = resize(images, args.width)
    nim = concatenate(images)

    if args.verbose:
        nim.show()
    nim.save(args.outfile, 'JPEG', quality=args.quality)

    print("____\nDONE.")


if __name__ == "__main__": main()
