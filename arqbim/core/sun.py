"""(0.316) The sun: its direction from an azimuth and an altitude, and where it is at a place and an hour (NOAA's
general solar position formulas — about a tenth of a degree, plenty for shadows on drawings). North is the model's +y,
east +x; an azimuth is counted from north towards east (90 east, 180 south, 270 west)."""

import math
from datetime import timedelta

import numpy as np


def direction(azimuth, altitude):
    """The unit vector towards the sun (x east, y north, z up)."""
    az, alt = math.radians(azimuth), math.radians(altitude)
    return np.array((math.sin(az) * math.cos(alt), math.cos(az) * math.cos(alt), math.sin(alt)))


def angles(vector):
    """(azimuth, altitude) of a direction towards the sun."""
    x, y, z = (float(c) for c in np.asarray(vector, dtype=float) / max(float(np.linalg.norm(vector)), 1e-12))
    return math.degrees(math.atan2(x, y)) % 360.0, math.degrees(math.asin(max(-1.0, min(1.0, z))))


def position(latitude, longitude, when, utc_offset=0.0):
    """(azimuth, altitude) in degrees of the sun seen from a place (latitude north +, longitude east +) at a date and
    hour `when` (a datetime, the clock of a place `utc_offset` hours ahead of UTC: Portugal 0 in winter, 1 in
    summer). An altitude below 0: night."""
    utc = when - timedelta(hours=float(utc_offset))
    day = utc.timetuple().tm_yday
    hour = utc.hour + utc.minute / 60.0 + utc.second / 3600.0
    g = 2.0 * math.pi / 365.0 * (day - 1 + (hour - 12.0) / 24.0)
    eqtime = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g) - 0.014615 * math.cos(2 * g)
                       - 0.040849 * math.sin(2 * g))                              # minutes
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))   # radians
    solar = hour * 60.0 + eqtime + 4.0 * float(longitude)                         # true solar time, minutes
    ha = math.radians(solar / 4.0 - 180.0)
    lat = math.radians(float(latitude))
    up = math.sin(lat) * math.sin(decl) + math.cos(lat) * math.cos(decl) * math.cos(ha)
    altitude = math.degrees(math.asin(max(-1.0, min(1.0, up))))
    azimuth = math.degrees(math.atan2(math.sin(ha), math.cos(ha) * math.sin(lat) - math.tan(decl) * math.cos(lat)))
    return (azimuth + 180.0) % 360.0, altitude
