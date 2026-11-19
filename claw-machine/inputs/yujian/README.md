# Inputs (not included)

The film is cut to a commercially released song, 孙燕姿 (Stefanie Sun) 《遇见》 (*Yu Jian*). The song and its lyrics are not ours to publish, so nothing here is included. To rebuild the soundtrack, bring your own copy:

| File | What | Used by |
|---|---|---|
| `song.m4a` | the full song (the official MV's audio track is 206.66 s long) | `analyze.py` |
| `out/yujian/clip.wav` | 46.60–105.10 s of it, 48 kHz stereo, 0.08 s fade in, last 1.4 s faded out | `mix.py` |
| `subtitles.tsv` | optional: `start<TAB>end<TAB>text` per line, in clip seconds | `post.py` |

```sh
mkdir -p out/yujian
ffmpeg -ss 46.60 -t 58.5 -i inputs/yujian/song.m4a -af "afade=t=in:d=0.08,afade=t=out:st=57.1:d=1.4" -ar 48000 -ac 2 out/yujian/clip.wav
```

Without `subtitles.tsv` the film renders without subtitles. Timings in the storyboard came from LRCLIB entry 30558675, shifted by −46.60 + 0.15 s.
