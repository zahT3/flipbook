"""The claw: carriage on rails, a coiled cord, a hub and three hinged fingers."""
import bpy, bmesh, math
from mathutils import Vector, Euler, Matrix, Quaternion
from .common import *
from . import mats as M

S = 1.32                               # claw scale
PIV_R = 0.015 * S                      # finger hinge radius on the hub
FINGER = [(0.0, 0.0), (0.016, -0.006), (0.031, -0.022), (0.036, -0.040), (0.031, -0.058), (0.020, -0.072), (0.011, -0.080)]
TIP = Vector((FINGER[-1][0] * S, 0, FINGER[-1][1] * S))
RAIL_Z = ZT - 0.035
TOP_Z = RAIL_Z - 0.030                 # where the cord leaves the carriage
HUB_H = 0.040 * S
REACH = -TIP.z + 0.004                 # hub origin (hinge level) down to the finger tips, closed

def tip_radius(deg):
    a = math.radians(deg)
    return PIV_R + TIP.x * math.cos(a) - TIP.z * math.sin(a)
def tip_drop(deg):
    a = math.radians(deg)
    return -(TIP.x * math.sin(a) + TIP.z * math.cos(a))
def finger_extent(deg):
    """Furthest any part of a finger gets from the hub axis at this opening (the knee when closed, the tip when open)."""
    a = math.radians(deg)
    return max(PIV_R + x * S * math.cos(a) - z * S * math.sin(a) for x, z in FINGER)
def angle_for_radius(r):
    """Finger angle (deg) whose tips sit at radius r from the axis."""
    lo, hi = -14.0, 75.0
    for _ in range(30):
        mid = (lo + hi) / 2
        if tip_radius(mid) < r: lo = mid
        else: hi = mid
    return (lo + hi) / 2

class Claw:
    def __init__(self, c):
        self.c = coll("claw", c)
        cc = self.c
        metal = M.worn_metal("claw_metal")
        dark = M.worn_metal("claw_dark", col="#6f6a64", oil=0.9)
        rubber = M.plain("claw_rubber", "#B23A2E", rough=0.55, noise_bump=0.4, noise_scale=600)
        cord_m = M.plain("claw_cord", "#2b2623", rough=0.35, coat=0.3)
        paint = M.plain("claw_paint", "#C9493B", rough=0.35, coat=0.6, noise_bump=0.15, noise_scale=300)
        self.cord_m = cord_m
        # --- rails and carriage
        for i, y in enumerate((Y0 + 0.035, Y1 - 0.035)):
            cyl("rail%d" % i, 0.006, 0.006, X1 - X0, cc, (0, y, RAIL_Z), metal, rot=(0, 90, 0), seg_n=16)
        self.bridge = empty("bridge", cc, None, (0, 0, RAIL_Z))
        box("bridge_bar", (0.022, Y1 - Y0 - 0.04, 0.012), cc, (0, 0, 0.004), dark, bevel=0.002, parent=self.bridge)
        for i, y in enumerate((Y0 + 0.035, Y1 - 0.035)):
            box("bridge_shoe%d" % i, (0.04, 0.024, 0.026), cc, (0, y, 0), paint, bevel=0.004, parent=self.bridge)
        self.car = empty("carriage", cc, self.bridge, (0, 0, 0))
        box("car_body", (0.060, 0.052, 0.034), cc, (0, 0, -0.012), paint, bevel=0.006, parent=self.car)
        cyl("car_spool", 0.014, 0.014, 0.040, cc, (0, 0, -0.012), metal, self.car, rot=(0, 90, 0), seg_n=24)
        cyl("car_noz", 0.007, 0.005, 0.012, cc, (0, 0, -0.030), dark, self.car, seg_n=16)
        for i, (x, y) in enumerate(((-0.022, -0.02), (0.022, -0.02), (-0.022, 0.02), (0.022, 0.02))):
            cyl("car_bolt%d" % i, 0.0028, 0.0028, 0.003, cc, (x, y, 0.0055), metal, self.car, seg_n=6)
        # --- hub (origin at the finger hinge level, on the axis)
        self.hub = empty("hub", cc)
        self.hub.rotation_mode = "QUATERNION"
        cyl("hub_body", 0.0135 * S, 0.0165 * S, 0.026 * S, cc, (0, 0, 0.016 * S), metal, self.hub, seg_n=32)
        dome = ell("hub_dome", (0.0135 * S, 0.0135 * S, 0.008 * S), cc, (0, 0, 0.029 * S), paint, self.hub, u=32, v=16)
        cyl("hub_neck", 0.0045 * S, 0.0035 * S, 0.010 * S, cc, (0, 0, 0.038 * S), dark, self.hub, seg_n=16)
        cyl("hub_skirt", 0.0185 * S, 0.0185 * S, 0.0045 * S, cc, (0, 0, 0.003 * S), dark, self.hub, seg_n=32)
        cyl("hub_rod", 0.0035 * S, 0.0035 * S, 0.030 * S, cc, (0, 0, -0.012 * S), metal, self.hub, seg_n=12)
        cyl("hub_foot", 0.008 * S, 0.006 * S, 0.004 * S, cc, (0, 0, -0.028 * S), dark, self.hub, seg_n=20)
        ring = cyl("hub_band", 0.0142 * S, 0.0142 * S, 0.003 * S, cc, (0, 0, 0.019 * S), paint, self.hub, seg_n=32)
        self.top_off = 0.043 * S              # cord attaches here above the hub origin
        # --- fingers
        self.fingers = []
        self.finger_az = [90, 210, 330]
        for i, az in enumerate(self.finger_az):
            a = math.radians(az)
            base = empty("fing_base%d" % i, cc, self.hub, (math.cos(a) * PIV_R, math.sin(a) * PIV_R, 0))
            base.rotation_euler.z = a                      # local +x points outward
            piv = empty("fing_piv%d" % i, cc, base)
            pts = [(x * S, 0, z * S) for x, z in FINGER]
            # resample for a smooth bar
            fine = []
            for k in range(len(pts) - 1):
                for j in range(4): fine.append(Vector(pts[k]).lerp(Vector(pts[k + 1]), j / 4))
            fine.append(Vector(pts[-1]))
            # round the corners a little
            sm = [fine[0]] + [(fine[j - 1] + fine[j] * 2 + fine[j + 1]) / 4 for j in range(1, len(fine) - 1)] + [fine[-1]]
            n = len(sm)
            bar = new_obj("finger%d" % i, tube_mesh("finger", sm, [0.0040 * S * (1.0 - 0.25 * j / n) for j in range(n)], metal, sides=10, axis=(0, 1, 0)), cc, piv)
            bar.scale = (1, 1.9, 1)                         # a flat stamped bar
            tipm = new_obj("finger_tip%d" % i, tube_mesh("tip", sm[-5:], 0.0052 * S, rubber, sides=10, axis=(0, 1, 0)), cc, piv)
            tipm.scale = (1, 1.7, 1)
            cyl("fing_pin%d" % i, 0.0032 * S, 0.0032 * S, 0.014 * S, cc, (0, 0, 0), dark, piv, rot=(90, 0, 0), seg_n=10)
            cyl("fing_rivet%d" % i, 0.0024 * S, 0.0024 * S, 0.0075 * S, cc, (sm[10].x, 0, sm[10].z), dark, piv, rot=(90, 0, 0), seg_n=8)
            self.fingers.append(piv)
        self.cord = new_obj("cord", bpy.data.meshes.new("cord"), cc)
        self.state = dict(x=0.0, y=0.0, z=0.40, open=[30, 30, 30], swing=(0.0, 0.0), tilt=(0.0, 0.0), slack=0.0, spin=0.0)

    def pose(self, x, y, z, open=30.0, swing=(0.0, 0.0), tilt=(0.0, 0.0), slack=0.0, spin=0.0, clamp=True):
        """x, y: carriage. z: height of the hub origin (hinge level) when hanging straight.
        open: degrees, one value or three. swing: pendulum angles (deg) about the carriage, in x and y.
        tilt: extra hub lean (deg). slack: 0..1, the cord sags and the hub drops a little. spin: hub yaw (deg)."""
        if isinstance(open, (int, float)): open = [open] * 3
        self.bridge.location.x = x
        self.car.location.y = y
        top = Vector((x, y, TOP_Z))
        L = top.z - (z + self.top_off)
        sx, sy = math.radians(swing[0]), math.radians(swing[1])
        d = Vector((math.sin(sx), math.sin(sy), -math.cos(sx) * math.cos(sy))).normalized()
        attach = top + d * L
        q = Vector((0, 0, -1)).rotation_difference(d)
        # the lean is in the room's axes whatever way the hub is turned: lean first, then spin about the hub's own axis
        qt = Euler((math.radians(tilt[1]), math.radians(tilt[0]), 0.0)).to_quaternion() @ Quaternion((0, 0, 1), math.radians(spin))
        rot = q @ qt
        self.hub.rotation_quaternion = rot
        self.hub.location = attach - rot @ Vector((0, 0, self.top_off))
        if clamp:
            # a finger that would go through the glass stops against it instead; the others open as asked
            open = list(open)
            hx, hy = self.hub.location.x, self.hub.location.y
            m = 0.009
            for i, a in enumerate(open):
                az = math.radians(self.finger_az[i] + spin)
                cx, cy = math.cos(az), math.sin(az)
                def fits(deg):
                    r = finger_extent(deg)
                    return X0 + m <= hx + r * cx <= X1 - m and Y0 + m <= hy + r * cy <= Y1 - m
                if not fits(a):
                    lo, hi = -14.0, a
                    for _ in range(18):
                        mid = (lo + hi) / 2
                        if fits(mid): lo = mid
                        else: hi = mid
                    open[i] = lo
        for piv, a in zip(self.fingers, open):
            piv.rotation_euler.y = -math.radians(a)
        self._cord(top, attach, slack)
        self.state = dict(x=x, y=y, z=z, open=list(open), swing=swing, tilt=tilt, slack=slack, spin=spin)
        return self.hub.location.copy(), rot

    def hold_point(self, drop):
        """World point `drop` below the hub origin along its axis."""
        return self.hub.location + self.hub.rotation_quaternion @ Vector((0, 0, -drop))

    def _cord(self, top, attach, slack):
        turns, per = 15, 12
        n = turns * per
        axis = attach - top
        L = axis.length
        d = axis / L
        a = d.cross(Vector((0, 1, 0))).normalized(); b = d.cross(a)
        pts, rad = [], []
        for i in range(n + 1):
            u = i / n
            ang = u * turns * 2 * math.pi
            env = min(1.0, u * 12, (1 - u) * 12)
            r = 0.0062 * env * (1.0 + 0.25 * slack)
            sag = slack * 0.02 * math.sin(u * math.pi) + slack * 0.006 * math.sin(u * 3 * math.pi)
            p = top + d * (L * u) + (a * math.cos(ang) + b * math.sin(ang)) * r + a * sag
            pts.append(p)
        me = tube_mesh("cord", pts, 0.00135, self.cord_m, sides=5, cap=True)
        old = self.cord.data
        self.cord.data = me
        bpy.data.meshes.remove(old)
