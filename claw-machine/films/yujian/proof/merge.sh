#!/bin/sh
# Film + proof, one horizontal video (for B站): the finished film in full with its own sound, then the proof film.
# The proof film carries the author's mark already; it is put on the film part here.
#   sh films/yujian/proof/merge.sh            (run from the project root)
set -e
python3 films/yujian/proof/compose.py --fmt h --mark-png /tmp/yujian-mark-h.png
ffmpeg -y -loglevel error -i out/yujian/yujian-claw.mp4 -i out/yujian/proof/yujian-proof.mp4 -i /tmp/yujian-mark-h.png \
  -filter_complex "[0:v][2:v]overlay=0:0,fps=24,format=yuv420p,setsar=1[v0];[1:v]fps=24,format=yuv420p,setsar=1[v1];[0:a]aresample=48000,aformat=channel_layouts=stereo[a0];[1:a]aresample=48000,aformat=channel_layouts=stereo[a1];[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]" \
  -map "[v]" -map "[a]" -c:v libx264 -crf 17 -preset slow -pix_fmt yuv420p -c:a aac -b:a 224k -movflags +faststart out/yujian/proof/yujian-film-and-proof.mp4
echo wrote out/yujian/proof/yujian-film-and-proof.mp4
