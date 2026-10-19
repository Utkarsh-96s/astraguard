"""Helper script to create notebooks/phase1_data_exploration.ipynb."""
import json
import os

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# ASTRA-GUARD: Phase 1 — Data & Simulation Exploration\n",
                "**AI-Powered Integrated Space Mission Safety & Intelligence**\n",
                "Team OMEN · AITHON 2.0\n",
                "\n",
                "This notebook demonstrates ingestion, synthetic fault injection, and API query validation for:\n",
                "1. Spacecraft Telemetry (Thermal drift, electrical spikes, sensor flatlining)\n",
                "2. Space Debris Encounter Conjunctions & CDM Pc evolution\n",
                "3. Earth Observation Disaster Imagery (Sentinel-1 SAR chips & flood masks)\n"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": 1,
            "metadata": {},
            "outputs": [],
            "source": [
                "import sys, os\n",
                "sys.path.insert(0, os.path.abspath('..'))\n",
                "import pandas as pd\n",
                "import numpy as np\n",
                "import matplotlib.pyplot as plt\n",
                "from data.synthetic.telemetry_gen import generate_telemetry_series\n",
                "from data.synthetic.debris_gen import generate_cdm_progression\n",
                "from data.synthetic.disaster_gen import generate_synthetic_chip_arrays\n",
                "print('Libraries loaded successfully.')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 1. Spacecraft Telemetry & Synthetic Fault Injection"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": 2,
            "metadata": {},
            "outputs": [],
            "source": [
                "df_telem = generate_telemetry_series(asset_id='SENTINEL-2A', duration_minutes=60, step_seconds=10, fault_type='drift', fault_start_minute=30)\n",
                "print(f'Total telemetry rows: {len(df_telem)}')\n",
                "df_telem.head(10)"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 2. Debris Encounter & Conjunction Assessment Progression"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": 3,
            "metadata": {},
            "outputs": [],
            "source": [
                "df_cdm = generate_cdm_progression(conjunction_id='CONJ-S2A-DEB', initial_pc=1e-6, final_pc=2.8e-4)\n",
                "print(f'Generated CDMs: {len(df_cdm)}')\n",
                "df_cdm[['cdm_id', 'time_to_tca_hours', 'miss_distance_m', 'pc', 'risk_level']]"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 3. Earth Observation Disaster Imagery & Segmentation"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": 4,
            "metadata": {},
            "outputs": [],
            "source": [
                "chip_backscatter, flood_mask = generate_synthetic_chip_arrays(size=128, water_ratio=0.32)\n",
                "print(f'Chip shape: {chip_backscatter.shape}, Flood pixels: {(flood_mask == 1).sum()}')"
            ]
        }
    ],
    "metadata": {
        "language_info": {
            "name": "python"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 2
}

os.makedirs("notebooks", exist_ok=True)
with open("notebooks/phase1_data_exploration.ipynb", "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=1)
print("Created notebooks/phase1_data_exploration.ipynb")
