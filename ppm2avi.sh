cd ./data
rm *.jpg
for f in *.ppm; do convert -quality 100 $f `basename $f .ppm`.jpg; rm $f; done
mencoder mf://*.jpg -mf fps=25:type=jpg -ovc x264 -x264encopts preset=veryslow:tune=film:crf=15:frameref=15:fast_pskip=0:threads=auto -o $1.avi
rm *.jpg
cd ..


