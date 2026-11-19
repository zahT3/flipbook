"""Sound: the song clip plus machine sounds, mixed under it.  python3 films/yujian/mix.py
  in:  out/yujian/clip.wav (the song, 58.5 s), films/yujian/sfx/*.wav (earshot bank takes)
  out: out/yujian/mix.wav (48 kHz stereo, true peak under -1 dBTP), out/yujian/sfx_only.wav
The motor is synthesised here: a small geared motor is a buzz whose pitch follows its speed.
"""
import os, numpy as np, soundfile as sf, subprocess
SR = 48000
DUR = 58.5
HERE = os.path.dirname(os.path.abspath(__file__))
N = int(SR * DUR)
bus = np.zeros((N, 2), np.float32)
rng = np.random.default_rng(3)

def load(name):
    a, sr = sf.read(os.path.join(HERE, "sfx", name + ".wav"), dtype="float32")
    assert sr == SR
    return a if a.ndim == 1 else a.mean(1)

def put(name, t, db=-20.0, pan=0.0, rate=1.0, lp=None):
    """Place a take with its attack at time t. pan -1..1. rate > 1 plays it higher and shorter."""
    a = load(name)
    if rate != 1.0:
        idx = np.arange(0, len(a) - 1, rate)
        a = np.interp(idx, np.arange(len(a)), a).astype(np.float32)
    if lp:                                   # one-pole low-pass, for things heard through glass or cloth
        k = np.exp(-2 * np.pi * lp / SR); y = np.zeros_like(a); z = 0.0
        for i in range(len(a)): z = (1 - k) * a[i] + k * z; y[i] = z
        a = y
    g = 10 ** (db / 20)
    i0 = int(t * SR)
    if i0 >= N: return
    a = a[:N - i0] * g
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    bus[i0:i0 + len(a), 0] += a * l; bus[i0:i0 + len(a), 1] += a * r

def motor(t0, t1, db=-30.0, pitch=118.0, pan=0.0):
    """Carriage / winch motor from t0 to t1: spins up, runs, spins down."""
    n = int((t1 - t0) * SR)
    if n <= 0: return
    t = np.arange(n) / SR
    env = np.clip(t / 0.07, 0, 1) * np.clip((t[-1] - t) / 0.10, 0, 1)
    f = pitch * (0.72 + 0.28 * env) * (1 + 0.01 * np.sin(2 * np.pi * 9 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    buzz = sum(np.sin(ph * k) / k ** 1.15 for k in (1, 2, 3, 4, 5, 7, 9))
    gear = np.sin(ph * 14.0) * 0.10 * (0.6 + 0.4 * np.sin(ph * 0.5))          # gear whine
    hiss = rng.normal(0, 1, n).astype(np.float32); hiss = np.convolve(hiss, np.ones(24) / 24, "same") * 0.5
    a = (buzz * 0.35 + gear + hiss) * env * 10 ** (db / 20)
    i0 = int(t0 * SR); a = a[:N - i0].astype(np.float32)
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    bus[i0:i0 + len(a), 0] += a * l; bus[i0:i0 + len(a), 1] += a * r

CUES = os.path.join(HERE, "cues.py")
exec(open(CUES).read())                      # the cue list lives next to the animation timings

# ---- mix
music, sr = sf.read("out/yujian/clip.wav", dtype="float32")
assert sr == SR
music = music[:N]
mg = 10 ** (-2.0 / 20)                       # the song's own peaks sit at 0 dBFS; leave headroom for the machine
bus *= 10 ** (8.0 / 20)                      # first pass sat 27 LU under the song: inaudible. Now about 19 LU under
mix = music * mg + bus
sf.write("out/yujian/sfx_only.wav", bus, SR, subtype="PCM_24")
sf.write("out/yujian/mix_raw.wav", mix, SR, subtype="PCM_24")
# true-peak safe: a look-ahead limiter at -1.5 dBFS, measured afterwards with earshot
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "out/yujian/mix_raw.wav", "-af", "alimiter=limit=-1.6dB:level=disabled:attack=3:release=60", "-ar", "48000", "-c:a", "pcm_s24le", "out/yujian/mix.wav"], check=True)
os.remove("out/yujian/mix_raw.wav")
print("sfx peak dBFS %.1f" % (20 * np.log10(np.abs(bus).max() + 1e-9)), "| wrote out/yujian/mix.wav")
