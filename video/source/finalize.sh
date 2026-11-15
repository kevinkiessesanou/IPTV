S=/tmp/claude-0/-home-user-IPTV/b9e51017-d5db-5fcc-a8a3-7ddce133fdb6/scratchpad
DST=/home/user/IPTV/video/web_mobile/campagne
mkdir -p $DST
export ELVOICE="/root/.claude/uploads/b9e51017-d5db-5fcc-a8a3-7ddce133fdb6/dcbc007d-ElevenLabs_2026-11-15T08_49_07_Tony_-_Punchy_Ad__Social_eleven_v4.mp3"
cd /tmp
fin() { # dir name burn margv size ph
  D=$S/$1
  python3 -I $S/audio5.py $D >/dev/null || return 1
  if [ "$3" = "1" ]; then
    python3 -I $S/caps5.py $D $4 $5 $6
    VF="-vf ass=$D/caps.ass:fontsdir=/usr/share/fonts/opentype/inter"
  else VF=""; fi
  ffmpeg -v error -y -i $D/video.mp4 -i $D/mix.wav $VF -af "loudnorm=I=-14:TP=-1:LRA=9" -ar 44100 \
    -c:v libx264 -preset slow -b:v 6500k -maxrate 8M -bufsize 12M -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart -shortest $DST/$2.mp4 \
    && echo "final $2"
}
#fin o_916_full   NTIC_Web_A_Complet_9x16        1 580 58 1920
#fin o_45_full    NTIC_Web_A_Complet_4x5         1 50  52 1350
#fin o_169_full   NTIC_Web_A_Complet_16x9        0
fin o_916_prix   NTIC_Web_B_Prix-Paiement_9x16  1 580 58 1920
fin o_45_prix    NTIC_Web_B_Prix-Paiement_4x5   1 50  52 1350
fin o_916_metiers NTIC_Web_C_Metiers_9x16       1 580 58 1920
fin o_45_metiers  NTIC_Web_C_Metiers_4x5        1 50  52 1350
