# Sound cues (clip seconds), read by mix.py. Times follow yj/anim.py; pan follows where the thing is on screen.
# put(take, time, dB, pan, rate, lowpass)   motor(t0, t1, dB, pitch, pan)

# --- 1: down onto the dog, the careful close
motor(0.0, 1.25, -31, 112, 0.1)
put("tick", 1.58, -27, 0.1)                       # fingers stop half way
put("clamp", 2.0, -25, 0.1, 0.8)                  # ...and close softly
motor(2.17, 4.58, -32, 100, 0.1)
# --- 2: it lets go, one finger at a time
motor(4.75, 5.75, -34, 92, 0.1)
for t in (5.17, 5.5, 5.83): put("tick", t, -27, 0.1, 0.85)
put("pat", 5.86, -24, 0.1)
put("cloth", 6.5, -32, 0.5, 0.8, 1800)            # the mitten slides off the glass
motor(6.6, 7.5, -34, 104, 0.1)
# --- 3: honest work, twice
motor(7.42, 7.92, -29, 124, -0.2); put("latch", 7.92, -22, -0.2)
motor(8.2, 8.75, -30, 118, -0.2); motor(8.83, 9.67, -30, 132, -0.4)
put("clamp", 9.83, -22, -0.6, 1.2); put("thud", 10.15, -22, -0.6, 0.8)
motor(10.17, 10.67, -30, 132, 0.1); put("clamp", 10.83, -22, -0.4, 1.2); put("thud", 11.15, -22, -0.4, 0.85)
motor(11.08, 11.42, -31, 132, 0.0)
motor(11.42, 11.92, -30, 132, 0.1); put("clamp", 12.08, -22, -0.4, 1.25); put("thud", 12.40, -22, -0.4, 0.9)
motor(12.33, 12.83, -32, 132, 0.2)
# --- 4: it comes by with the star and stops
motor(14.4, 15.5, -34, 120, 0.3)
motor(17.3, 17.9, -35, 120, -0.2)
# --- 5: left, right, forward
motor(17.92, 18.67, -30, 132, -0.3); put("clamp", 18.83, -22, -0.6, 1.2); put("thud", 19.15, -22, -0.6, 0.8)
motor(19.58, 20.33, -30, 124, 0.4); put("latch", 20.37, -22, 0.6); motor(20.6, 21.3, -31, 118, 0.6)
motor(21.4, 22.1, -33, 96, 0.3); put("tick", 22.25, -28, 0.3); motor(22.6, 23.3, -34, 104, 0.3)
# --- 6: hides it in the corner
motor(23.33, 24.3, -33, 100, 0.3)
put("pat", 24.33, -26, 0.4)
for t in (24.38, 24.47, 24.56): put("tick", t, -29, 0.4, 0.9)
motor(24.72, 24.95, -33, 118, 0.4)
put("pat", 25.08, -24, 0.4, 0.9); put("cloth", 25.05, -29, 0.4, 0.9, 2500); put("thud", 25.25, -25, 0.4, 0.8)      # tipped onto its back
motor(25.25, 25.5, -33, 118, 0.2); motor(25.5, 26.1, -32, 108, 0.3); put("cloth", 25.52, -30, 0.3, 0.8, 2500)
put("tick", 26.4, -27, 0.3, 1.1); put("tick", 26.58, -27, 0.3, 1.2)       # pleased: a little clap
put("cloth", 26.95, -31, 0.4, 1.1, 3000)                                   # it sits up
put("thud", 27.58, -24, 0.3, 0.9)                                          # lands on the near side of the cloud
for t in (27.92, 28.25): put("pat", t, -27, 0.3, 1.25)
put("tick", 27.85, -30, 0.2, 0.7)
# --- 7: only two left
for t in (28.92, 29.34): put("pat", t, -27, 0.3, 1.25)
motor(29.0, 29.4, -35, 118, 0.2); motor(29.9, 30.4, -35, 118, 0.3)
motor(31.0, 31.75, -34, 96, 0.3)
# --- 8: the person; the coin
put("glass", 34.67, -21, 0.4, 0.9)                 # the mitten on the glass
put("bulb", 36.5, -27, 0.0); put("bulb", 36.75, -27, 0.0)                 # the lights blink
put("coin", 38.42, -19, 0.2); put("coin", 38.58, -22, 0.2, 0.8); put("ding", 38.66, -27, 0.2, 0.75)
# --- 9: for real this time
motor(38.95, 39.2, -30, 128, 0.3)
motor(39.45, 39.83, -27, 140, 0.3)
put("latch", 39.80, -17, 0.3, 0.85); put("clamp", 39.93, -17, 0.3, 0.7)
motor(40.4, 41.33, -29, 110, 0.3); motor(41.33, 44.0, -31, 126, -0.1)
# --- 10: the hug, the open hand, the way out, goodbye at the glass
put("tick", 44.8, -27, -0.5, 0.8)
put("clamp", 45.83, -19, -0.5, 1.25)
put("cloth", 45.9, -29, -0.5, 1.0, 3000); put("thud", 46.38, -23, -0.5, 0.75)
put("tick", 47.42, -27, -0.3, 0.8); put("tick", 47.58, -25, -0.3, 0.75)    # it knocks on the door from inside, then pushes
put("flap", 47.775, -20, -0.3, 0.8); put("flap", 47.945, -29, -0.3, 0.95)  # the door falls open on the tray (47.83) and bounces once (48.0); the take's slap comes 55 ms after its start
put("pat", 48.25, -24, -0.3)                                               # it lands on the open door
put("pat", 48.75, -25, -0.2, 1.1)                                          # hops onto the mitten
put("cloth", 48.9, -30, -0.2, 0.8, 2500)
motor(49.42, 50.0, -30, 132, 0.0); motor(50.08, 50.45, -34, 96, 0.2)
put("glass", 50.5, -19, 0.2, 1.25); put("tick", 50.5, -27, 0.2, 1.3)      # one finger on the glass
# --- 11: closing time
for t in (51.83, 52.25, 52.5): put("rocker", t, -24, -0.7 + 0.9 * (t - 51.8), 0.7, 1500)
put("cloth", 52.05, -33, 0.2, 0.6, 1800)                                   # the finger slides off the glass
for i in range(18): put("bulb", 52.42 + i * 0.06, -31, (i % 9) / 4 - 1, 0.8)
put("off", 53.55, -27, 0.2, 0.8)
# --- 12: morning
for i in range(18): put("bulb", 54.67 + i * 0.022, -30, (i // 2) / 4 - 1, 1.2)
for i in range(10): put("pat" if i % 2 else "thud", 54.95 + i * 0.085 + 0.42, -25, (i % 5) / 2.5 - 0.8, 0.8 + 0.08 * (i % 4))
put("thud", 56.13, -21, 0.0, 0.9)
motor(56.33, 56.67, -35, 110, 0.2)
put("tick", 56.92, -27, 0.2, 1.1); put("tick", 57.08, -27, 0.2, 1.2)
