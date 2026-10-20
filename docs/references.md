# ASTRA-GUARD — Literature References & Data Sources

This document validates and traces all academic citations, public space datasets, and algorithmic baselines used in the ASTRA-GUARD platform per `rules.md` (Prime Directive 6: Verify References).

---

## 1. Spacecraft Health & Anomaly Detection

1. **ESA Anomaly Detection Benchmark (ESA-ADB):**
   - *Title:* Artificial Intelligence for Spacecraft Telemetry Anomaly Detection (ESA-ADB)
   - *Organization:* European Space Agency (ESA) Operations Data Systems Division (ESOC, Darmstadt)
   - *Dataset:* Multi-mission telemetry dataset (Mission 1, 2, 3) covering thermal, power, and ADCS channels.
   - *URL:* [ESA Open Data Portal](https://kelvins.esa.int/)
   - *Usage in ASTRA-GUARD:* Synthetic telemetry generator mirrors the 7-channel schema (wheel temperature, bus voltage, battery current, ADCS gyro rates, sun sensor).

2. **LSTM Autoencoders for Time Series Anomaly Detection:**
   - *Authors:* Malhotra, P., Ramakrishnan, A., Anand, G., Vig, L., Agarwal, P., Shroff, G. (2016)
   - *Title:* LSTM-based Encoder-Decoder for Multi-sensor Anomaly Detection
   - *ArXiv:* [arXiv:1607.00148](https://arxiv.org/abs/1607.00148)
   - *Usage in ASTRA-GUARD:* Primary neural architecture in `ml/health/lstm_ae.py` ($64 \to 32 \to 16 \to 32 \to 64$).

3. **SHAP (SHapley Additive exPlanations):**
   - *Authors:* Lundberg, S. M., Lee, S.-I. (2017)
   - *Title:* A Unified Approach to Interpreting Model Predictions
   - *Venue:* Advances in Neural Information Processing Systems (NeurIPS 30)
   - *URL:* [NeurIPS Proceedings](https://papers.nips.cc/paper/7062-a-unified-approach-to-interpreting-model-predictions)
   - *Usage in ASTRA-GUARD:* Feature importance and residual channel attribution in `ml/health/explainability.py`.

---

## 2. Orbital Mechanics & Debris Collision Assessment

4. **SGP4 Orbital Propagator (Vallado et al.):**
   - *Authors:* Vallado, D. A., Crawford, P., Hujsak, R., Kelso, T. S. (2006)
   - *Title:* Revisiting Spacetrack Report #3: Rev 2
   - *Venue:* AIAA/AAS Astrodynamics Specialist Conference, Keystone, CO
   - *DOI:* [10.2514/6.2006-6753](https://doi.org/10.2514/6.2006-6753)
   - *Implementation:* Python `sgp4.api.Satrec` (`sgp4>=2.23`) analytical ephemeris propagation in `ml/debris/sgp4_propagator.py`.

5. **Foster 2-D B-Plane Collision Probability Method:**
   - *Authors:* Foster, J. L., Estes, H. S. (1992)
   - *Title:* A Parametric Analysis of Orbital Debris Collision Probability and Maneuver Strategy for Space Station Freedom
   - *Report:* NASA Technical Memorandum NASA-TM-104752 / JSC-25898
   - *URL:* [NASA Technical Reports Server](https://ntrs.nasa.gov/citations/19920023847)
   - *Usage in ASTRA-GUARD:* Analytical 2-D normal integration in conjunction encounters in `ml/debris/foster_pc.py`.

6. **ESA Kelvins Collision Avoidance Challenge:**
   - *Organization:* European Space Operations Centre (ESOC) Space Debris Office
   - *Dataset:* Conjunction Data Messages (CDMs) from real ESA operational missions.
   - *URL:* [ESA Kelvins CDM Benchmark](https://kelvins.esa.int/collision-avoidance-challenge/)
   - *Usage in ASTRA-GUARD:* Training and evaluation of the XGBoost CDM risk classifier in `ml/debris/cdm_classifier.py`.

7. **CelesTrak Space Track GP Catalog:**
   - *Curator:* Dr. T. S. Kelso (Center for Space Standards & Innovation)
   - *Dataset:* Public Two-Line Element (TLE) and General Perturbations (GP) ephemeris for active satellites and debris.
   - *URL:* [CelesTrak](https://celestrak.org/)
   - *Usage in ASTRA-GUARD:* Active orbital element ingestion in `apps/api/app/routers/ingest.py`.

---

## 3. Earth Observation & Radar Disaster Mapping

8. **Sen1Floods11 Benchmark Dataset:**
   - *Authors:* Bonafilia, D., Tellman, B., Anderson, T., Issenberg, E. (2020)
   - *Title:* Sen1Floods11: A Georeferenced Dataset to Train and Test Deep Learning Flood Algorithms for Sentinel-1
   - *Venue:* IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR) Workshops
   - *DOI:* [10.1109/CVPRW50498.2020.00113](https://doi.org/10.1109/CVPRW50498.2020.00113)
   - *Usage in ASTRA-GUARD:* Dual-polarization SAR backscatter training and test chips in `ml/disaster/sar_detector.py`.

9. **U-Net: Convolutional Networks for Biomedical Image Segmentation:**
   - *Authors:* Ronneberger, O., Fischer, P., Brox, T. (2015)
   - *Venue:* Medical Image Computing and Computer-Assisted Intervention (MICCAI)
   - *ArXiv:* [arXiv:1505.04597](https://arxiv.org/abs/1505.04597)
   - *Usage in ASTRA-GUARD:* Lightweight 2-level U-Net architecture with skip connections in `ml/disaster/unet.py`.

---

## 4. Multi-Hazard Decision Fusion & Explainability

10. **Noisy-OR Probabilistic Hazard Fusion:**
    - *Authors:* Pearl, J. (1988)
    - *Title:* Probabilistic Reasoning in Intelligent Systems: Networks of Plausible Inference
    - *Publisher:* Morgan Kaufmann Publishers, San Mateo, CA
    - *Formulation:* $R_{safety} = 1 - \prod_{i=1}^N (1 - r_i)$
    - *Usage in ASTRA-GUARD:* Independent failure probability fusion in `ml/risk_engine/fusion.py`.
