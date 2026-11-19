"""Where does the voice enter near each LRC line? Centre-channel (mid minus side) energy, 0.1 s steps."""
import librosa, numpy as np
y, sr = librosa.load("inputs/yujian/song.m4a", sr=22050, mono=False)
M = np.abs(librosa.stft((y[0] + y[1]) / 2, n_fft=2048, hop_length=256))
S = np.abs(librosa.stft((y[0] - y[1]) / 2, n_fft=2048, hop_length=256))
f = librosa.fft_frequencies(sr=sr, n_fft=2048)
band = (f > 500) & (f < 3500)
c = np.clip(M - 1.5 * S, 0, None)[band].mean(0)
t = librosa.frames_to_time(np.arange(len(c)), sr=sr, hop_length=256)
for name, lrc in [("阴天", 53.92), ("未来有", 59.23), ("向左", 64.34), ("爱要", 69.78), ("我遇见谁", 74.84), ("我等的人", 80.18), ("我听见风", 85.34), ("我排着队", 90.74), ("end", 96.5)]:
    row = []
    for a in np.arange(lrc - 0.6, lrc + 1.6, 0.1):
        m = (t >= a) & (t < a + 0.1)
        row.append(20 * np.log10(c[m].mean() + 1e-6))
    base = lrc - 0.6
    print(name, lrc, " ".join("%.0f" % v for v in row))
