cd ./data
ffmpeg -pattern_type glob -framerate 100 -i "*.ppm" $1_hq.mp4
rm *.ppm
ffmpeg -i $1_hq.mp4 -vf "scale=-1:720" -framerate 25 $1_lq.mp4
cd ..


