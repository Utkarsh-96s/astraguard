"""SGP4 analytical orbit propagator for satellite and debris TLEs."""
from datetime import UTC, datetime

import numpy as np
from sgp4.api import Satrec, jday

# WGS-72 / WGS-84 Earth physical constants
EARTH_RADIUS_KM = 6378.137
MU_EARTH = 398600.4418  # km^3 / s^2


class SGP4Propagator:
    """High-accuracy SGP4 analytical propagator wrapping official sgp4 library."""

    def __init__(self, line1: str, line2: str, name: str = "UNKNOWN") -> None:
        self.line1 = line1.strip()
        self.line2 = line2.strip()
        self.name = name
        self.satrec = Satrec.twoline2rv(self.line1, self.line2)
        if self.satrec.error != 0:
            raise ValueError(f"Failed to parse TLE for {name}: error code {self.satrec.error}")

    @classmethod
    def from_tle(cls, line1: str, line2: str, name: str = "UNKNOWN") -> "SGP4Propagator":
        """Factory method to instantiate propagator from two TLE lines."""
        return cls(line1, line2, name=name)

    def propagate_datetime(self, dt: datetime) -> tuple[np.ndarray, np.ndarray]:
        """Propagate state vector to specified UTC datetime.

        Returns:
            r: 3D position vector [x, y, z] in km (ECI TEME frame)
            v: 3D velocity vector [vx, vy, vz] in km/s
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)

        sec = dt.second + dt.microsecond * 1e-6
        jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, sec)
        error, r, v = self.satrec.sgp4(jd, fr)

        if error != 0:
            raise RuntimeError(
                f"SGP4 error {error} propagating {self.name} at {dt.isoformat()} "
                f"(error code {error}: see sgp4 documentation)"
            )

        return np.array(r, dtype=np.float64), np.array(v, dtype=np.float64)

    def propagate_series(
        self,
        dts: list[datetime],
    ) -> tuple[np.ndarray, np.ndarray]:
        """Propagate state vector across a sequence of datetimes.

        Returns:
            positions: (N, 3) array in km
            velocities: (N, 3) array in km/s
        """
        n = len(dts)
        positions = np.zeros((n, 3), dtype=np.float64)
        velocities = np.zeros((n, 3), dtype=np.float64)

        for i, dt in enumerate(dts):
            r, v = self.propagate_datetime(dt)
            positions[i] = r
            velocities[i] = v

        return positions, velocities

    def get_orbit_envelope(self) -> dict[str, float]:
        """Compute apogee, perigee, and inclination from TLE parameters."""
        # Mean motion in revs per day
        n_rev_day = self.satrec.no_kozai * (1440.0 / (2.0 * np.pi))
        period_sec = 86400.0 / (n_rev_day + 1e-8)
        period_min = period_sec / 60.0

        # Semi-major axis in km
        a = (MU_EARTH * (period_sec / (2.0 * np.pi)) ** 2) ** (1.0 / 3.0)
        e = float(self.satrec.ecco)
        inc_deg = float(np.degrees(self.satrec.inclo))

        perigee_km = a * (1.0 - e) - EARTH_RADIUS_KM
        apogee_km = a * (1.0 + e) - EARTH_RADIUS_KM

        return {
            "semi_major_axis_km": round(float(a), 3),
            "eccentricity": round(e, 6),
            "inclination_deg": round(inc_deg, 4),
            "period_minutes": round(period_min, 3),
            "perigee_altitude_km": round(float(perigee_km), 3),
            "apogee_altitude_km": round(float(apogee_km), 3),
        }

    def relative_state(
        self,
        other: "SGP4Propagator",
        dt: datetime,
    ) -> tuple[float, float, np.ndarray, np.ndarray]:
        """Compute relative state between self and other satellite.

        Returns:
            miss_distance_km: Euclidean separation in km
            rel_speed_kms: Magnitude of relative velocity in km/s
            rel_pos_km: Vector r_other - r_self in km
            rel_vel_kms: Vector v_other - v_self in km/s
        """
        r1, v1 = self.propagate_datetime(dt)
        r2, v2 = other.propagate_datetime(dt)

        rel_pos = r2 - r1
        rel_vel = v2 - v1

        miss_km = float(np.linalg.norm(rel_pos))
        rel_speed = float(np.linalg.norm(rel_vel))

        return miss_km, rel_speed, rel_pos, rel_vel
