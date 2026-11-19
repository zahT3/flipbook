"""Beat/vocal analysis of the song. python3 films/yujian/analyze.py"""
import librosa, numpy as np, re, json
y, sr = librosa.load("inputs/yujian/song.m4a", sr=22050, mono=False)
mid = (y[0] + y[1]) / 2
tempo, beats = librosa.beat.beat_track(y=mid, sr=sr, units="time")
print("tempo", tempo)
print("beats 40-110:", [round(float(b), 2) for b in beats if 40 <= b <= 110])
# vocal proxy: centre-channel energy in 250-3500 Hz after harmonic separation
S = librosa.stft(mid, n_fft=2048, hop_length=512)
H, P = librosa.decompose.hpss(S)
f = librosa.fft_frequencies(sr=sr, n_fft=2048)
band = (f > 300) & (f < 3400)
e = librosa.amplitude_to_db(np.abs(H[band]).mean(0) + 1e-9)
t = librosa.frames_to_time(np.arange(len(e)), sr=sr, hop_length=512)
rms = librosa.amplitude_to_db(librosa.feature.rms(y=mid, hop_length=512)[0] + 1e-9)
for a in np.arange(40, 112, 0.5):
    m = (t >= a) & (t < a + 0.5)
    print("%6.1f voc %6.1f rms %6.1f %s" % (a, e[m].mean(), rms[m].mean(), "#" * int(max(0, e[m].mean() + 45))))
json.dump({"tempo": float(np.atleast_1d(tempo)[0]), "beats": [float(b) for b in beats]}, open("out/yujian/beats.json", "w"))
