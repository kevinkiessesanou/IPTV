S=/tmp/claude-0/-home-user-IPTV/b9e51017-d5db-5fcc-a8a3-7ddce133fdb6/scratchpad
cd /tmp
for job in "916 full" "45 full" "169 full" "916 prix" "45 prix" "916 metiers" "45 metiers"; do
  set -- $job
  python3 -I $S/v5.py $S/o_$1_$2 $1 $2 && (cd $S/o_$1_$2 && ffmpeg -v error -y -f concat -safe 0 -i list.txt -c copy video.mp4) && echo "rendered $1 $2"
done
