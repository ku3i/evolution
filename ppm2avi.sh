cd ./data
for f in *.ppm; do convert -quality 100 $f `basename $f .ppm`.jpg; rm $f; done
#mencoder mf://*.png -mf fps=25:type=png -ovc lavc -lavcopts vcodec=mpeg4:mbd=2:trell -oac copy -o output.avi
#mencoder mf://*.jpg -mf fps=25:type=jpg -ovc lavc -lavcopts vcodec=mpeg4:mbd=2:mv0:trell:v4mv:cbp:last_pred=3:predia=2:dia=2:vmax_b_frames=2:vb_strategy=1:precmp=2:cmp=2:subcmp=2:preme=2:qns=2 -oac copy -o $1.avi
#mencoder mf://*.jpg -mf fps=25:type=jpg -ovc copy -o $1_hq.avi

mencoder mf://*.jpg -mf fps=25:type=jpg -ovc x264 -x264encopts preset=veryslow:tune=film:crf=15:frameref=15:fast_pskip=0:threads=auto -o $1.avi

rm *.jpg
cd ..


