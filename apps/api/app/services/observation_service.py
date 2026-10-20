"""Observation Tasking Optimizer Service.

Implements F12: Observation Tasking Optimizer.
Schedules ground-based optical telescopes and tracking radar passes
(TIRA, ESA Teide, Maui AMOS, Learmonth) to track high-uncertainty conjunctions,
projecting covariance shrinkage and avoiding unnecessary collision avoidance maneuvers.
"""
from datetime import UTC, datetime, timedelta
from typing import Any


class ObservationService:
    """Service for optimizing sensor tasking windows across global SSA ground stations."""

    STATIONS = [
        {
            "id": "GS-TIRA",
            "name": "TIRA Tracking & Imaging Radar",
            "operator": "Fraunhofer FHR",
            "location": "Wachtberg, Germany",
            "lat": 50.6167,
            "lon": 7.1306,
            "alt_m": 269,
            "type": "Radar (L/Ku-band Monopulse)",
            "min_elevation_deg": 10.0,
            "accuracy_m": 3.5,
            "all_weather": True,
        },
        {
            "id": "GS-TEIDE",
            "name": "ESA Optical Ground Station (OGS)",
            "operator": "ESA Space Debris Office",
            "location": "Teide Observatory, Tenerife, Spain",
            "lat": 28.3006,
            "lon": -16.5108,
            "alt_m": 2393,
            "type": "Optical (1.0m Zeiss Telescope)",
            "min_elevation_deg": 15.0,
            "accuracy_m": 8.0,
            "all_weather": False,
        },
        {
            "id": "GS-MAUI",
            "name": "Maui Space Surveillance System (AMOS)",
            "operator": "US Space Force / AFRL",
            "location": "Haleakala, Hawaii, USA",
            "lat": 20.7083,
            "lon": -156.2575,
            "alt_m": 3058,
            "type": "Optical & Laser (3.6m AEOS)",
            "min_elevation_deg": 15.0,
            "accuracy_m": 5.0,
            "all_weather": False,
        },
        {
            "id": "GS-LEARMONTH",
            "name": "Learmonth Space Surveillance Station",
            "operator": "Australian Defence Force",
            "location": "Exmouth, WA, Australia",
            "lat": -22.2356,
            "lon": 114.0889,
            "alt_m": 12,
            "type": "Radar (C-band SSA Radar)",
            "min_elevation_deg": 5.0,
            "accuracy_m": 6.2,
            "all_weather": True,
        },
    ]

    def optimize_tasking(
        self,
        conjunction_id: str = "CONJ-29834",
        secondary_name: str = "FENGYUN-1C-DEB-29834",
        hours_to_tca: float = 14.2,
        initial_sigma_y_m: float = 250.0,
        initial_sigma_x_m: float = 50.0,
    ) -> dict[str, Any]:
        """Compute optimal sensor pass schedule and projected covariance reduction."""
        now = datetime.now(UTC)
        tca_epoch = now + timedelta(hours=hours_to_tca)

        passes = [
            {
                "pass_id": "PASS-01-TIRA",
                "station": self.STATIONS[0],
                "start_utc": (now + timedelta(hours=2.4)).isoformat(),
                "peak_utc": (now + timedelta(hours=2.52)).isoformat(),
                "end_utc": (now + timedelta(hours=2.64)).isoformat(),
                "duration_sec": 860,
                "duration_min": 14.3,
                "max_elevation_deg": 68.4,
                "approach_azimuth_deg": 194.2,
                "departure_azimuth_deg": 18.5,
                "track_quality_snr_db": 28.5,
                "sensor_modality": "Radar (L-band monopulse)",
                "recommended": True,
                "shrinkage_contribution_pct": 74.2,
            },
            {
                "pass_id": "PASS-02-TEIDE",
                "station": self.STATIONS[1],
                "start_utc": (now + timedelta(hours=5.8)).isoformat(),
                "peak_utc": (now + timedelta(hours=5.9)).isoformat(),
                "end_utc": (now + timedelta(hours=6.01)).isoformat(),
                "duration_sec": 750,
                "duration_min": 12.5,
                "max_elevation_deg": 44.1,
                "approach_azimuth_deg": 210.0,
                "departure_azimuth_deg": 32.0,
                "track_quality_snr_db": 21.0,
                "sensor_modality": "Optical (night solar phase angle 118°)",
                "recommended": True,
                "shrinkage_contribution_pct": 18.4,
            },
            {
                "pass_id": "PASS-03-LEARMONTH",
                "station": self.STATIONS[3],
                "start_utc": (now + timedelta(hours=8.9)).isoformat(),
                "peak_utc": (now + timedelta(hours=9.02)).isoformat(),
                "end_utc": (now + timedelta(hours=9.14)).isoformat(),
                "duration_sec": 840,
                "duration_min": 14.0,
                "max_elevation_deg": 52.8,
                "approach_azimuth_deg": 175.4,
                "departure_azimuth_deg": 358.1,
                "track_quality_snr_db": 25.2,
                "sensor_modality": "Radar (C-band)",
                "recommended": False,
                "shrinkage_contribution_pct": 7.4,
            },
        ]

        # Covariance shrinkage math: post-tracking radar measurements shrink in-track variance
        post_track_sigma_y = round(initial_sigma_y_m * 0.154, 1)  # 250 -> 38.5m
        post_track_sigma_x = round(initial_sigma_x_m * 0.364, 1)  # 50 -> 18.2m
        sigma_reduction_pct = round((1.0 - (post_track_sigma_y / initial_sigma_y_m)) * 100.0, 1)

        # Projected impact on collision decision:
        # If true separation is nominal (>100m), shrinking covariance proves safety without CAM burn
        projected_pc_if_separated = 4.2e-7
        projected_fuel_savings_g = 128.4

        tdm_preview = (
            "CCSDS_TDM_VERS = 2.0\n"
            f"CREATION_DATE = {now.strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
            "ORIGINATOR = ASTRA-GUARD_SSA_DIRECTORATE\n"
            f"TARGET_NAME = {secondary_name}\n"
            "SENSOR_REQUEST = TIRA_RADAR_TRACKING\n"
            f"START_TIME = {passes[0]['start_utc']}\n"
            f"STOP_TIME = {passes[0]['end_utc']}\n"
            "MODE = HIGH_PRECISION_RANGE_RANGE_RATE"
        )

        return {
            "conjunction_id": conjunction_id,
            "secondary_name": secondary_name,
            "hours_to_tca": hours_to_tca,
            "tca_epoch_utc": tca_epoch.isoformat(),
            "station_network_size": len(self.STATIONS),
            "stations_available": self.STATIONS,
            "scheduled_passes": passes,
            "optimal_primary_pass": passes[0],
            "covariance_projection": {
                "initial_sigma_in_track_m": initial_sigma_y_m,
                "initial_sigma_normal_m": initial_sigma_x_m,
                "projected_sigma_in_track_m": post_track_sigma_y,
                "projected_sigma_normal_m": post_track_sigma_x,
                "uncertainty_reduction_pct": sigma_reduction_pct,
                "projected_pc_resolution": projected_pc_if_separated,
                "potential_cam_avoidance": True,
                "projected_fuel_savings_g": projected_fuel_savings_g,
            },
            "tdm_command_preview": tdm_preview,
            "synthetic": True,
        }


observation_service = ObservationService()
