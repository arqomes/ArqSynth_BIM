"""(0.365) The sun as the ArqSynth Presentation places it (its lib/editor3d/sun.ts): from the site's latitude and
longitude, a day of the year and a time of the day on the local standard clock (the longitude's 15° meridian, no
summer time) — a compact model, for pictures, not core/sun.py's NOAA one: the preview here shows the sun the
Presentation will show. North is the model's +y (the Presentation's −Z). Pure Python."""

import math

from ..core import sun as core_sun

DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
ANIMATIONS = ("none", "day", "year")


def _equation_of_time(day):
    b = 2.0 * math.pi * (day - 81) / 364.0
    return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def _meridian(longitude):
    return math.floor(longitude / 15.0 + 0.5) * 15.0           # (JavaScript's Math.round: halves up, not to even)


def angles(latitude, longitude, day, minutes):
    """(azimuth from north towards east, elevation) in degrees — sun.ts's solarAngles."""
    lat = math.radians(latitude)
    decl = math.radians(23.45) * math.sin(2.0 * math.pi * (day - 81) / 365.0)
    solar = minutes + _equation_of_time(day) + 4.0 * (longitude - _meridian(longitude))
    h = math.radians((solar / 60.0 - 12.0) * 15.0)
    up = math.sin(lat) * math.sin(decl) + math.cos(lat) * math.cos(decl) * math.cos(h)
    elevation = math.degrees(math.asin(max(-1.0, min(1.0, up))))
    az = math.degrees(math.atan2(math.sin(h), math.cos(h) * math.sin(lat) - math.tan(decl) * math.cos(lat))) + 180.0
    return az % 360.0, elevation


def direction(latitude, longitude, day, minutes):
    """Towards the sun, in the model's axes (x east, y north, z up)."""
    azimuth, elevation = angles(latitude, longitude, day, minutes)
    return core_sun.direction(azimuth, elevation)


def day_of(month, day):
    """The day of the year (1–365) of a day of a month (1–12)."""
    return sum(DAYS[:max(1, min(12, int(month))) - 1]) + max(1, min(DAYS[int(month) - 1], int(day)))


def month_day(day):
    """(month, day of the month) of a day of the year."""
    day = max(1, min(365, int(day)))
    for month, length in enumerate(DAYS, 1):
        if day <= length:
            return month, day
        day -= length
    return 12, 31


def daylight(latitude, longitude, day):
    """(sunrise, sunset) in minutes of the day (sun.ts's solarDayMarkers)."""
    lat = math.radians(latitude)
    decl = math.radians(23.45) * math.sin(2.0 * math.pi * (day - 81) / 365.0)
    half = math.degrees(math.acos(max(-1.0, min(1.0, -math.tan(lat) * math.tan(decl))))) / 15.0
    noon = 12 * 60 - _equation_of_time(day) - 4.0 * (longitude - _meridian(longitude))
    return max(0.0, noon - half * 60.0), min(1439.0, noon + half * 60.0)


def sweep(latitude, longitude, day, minutes, animation, frames=240):
    """A sun animation played: [(day, minutes)] — "day": from sunrise to sunset on that day; "year": the twelve
    months at that hour; "none": that moment alone."""
    if animation == "day":
        rise, sets = daylight(latitude, longitude, day)
        return [(day, rise + (sets - rise) * k / (frames - 1)) for k in range(frames)]
    if animation == "year":
        return [(1 + round(364 * k / (frames - 1)), minutes) for k in range(frames)]
    return [(day, minutes)]
