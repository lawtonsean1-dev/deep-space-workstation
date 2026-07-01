# 🌌 DEEP SPACE SYSTEM DOSSIER WORKSTATION (v2.3.2)

An interactive, responsive dark-sky cockpit and data pipeline designed for rapid exoplanet target profiling, dual-registry coordinate resolution, and live transit light curve processing. 

Built using Python, Streamlit, and advanced astrophysical libraries, this application delivers a night-vision-friendly HUD panel for amateur astronomers and researchers to analyze deep-space objects on desktop or mobile.

---

## 🛠️ Core Architecture & Pipeline Features

The workstation operates on a multi-stage routing pipeline designed to guarantee target resolution.

### 1. Dual-Registry Telemetry Engine
* **Primary Log:** Executes automated ADQL database selections against Caltech's master **Planetary Systems Composite Parameters (`pscomppars`)** archive.
* **Intelligent Fallback Routing:** If a target star is missing from the exoplanet catalog (e.g., *Vega* or *Betelgeuse*), the system instantly queries the **CDS SIMBAD Network**. It leverages native `SkyCoord` string interpretation to securely parse byte sequences and prevent data delivery failure.

### 2. 2D Orbital Trajectory Map
Using parametric coordinate loops plotted via vector geometry, the workstation draws an anatomically proportional system map using the planet's **Semi-Major Axis ($a$)**, **Semi-Minor Axis ($b$)**, and **Orbital Eccentricity ($e$)**.
* **Focal Shift Math:** To honor Keplerian mechanics, the orbit is dynamically offset by the true focal distance:
  $$c = \sqrt{a^2 - b^2}$$
  This positions the host star perfectly at one of the true geometric orbital foci.

### 3. Precision Scientific Telemetry
* Data cards display critical physical stellar properties: **Mass ($M_\odot$)**, **Radius ($R_\odot$)**, and **Effective Temperature ($K$)**.
* All core host parameters are displayed alongside their official **scientific error margins ($\pm$)** formatted cleanly in neutral technical indicators to protect dark-adapted field vision.

### 4. Live Sensor Photometry Processing
* Knocks on the door of the Mikulski Archive for Space Telescopes (MAST) via `lightkurve`.
* Smooths background stellar noise using a rolling window algorithm (`window_length=401`).
* Runs a live **Box Least Squares (BLS) periodogram power scan** to calculate transit frequency and primary epochs, then folds the data points to reveal the planet's actual transit light curve signature.

---

## 🚀 Live Deployment

📦 **GitHub Repository:** `https://github.com/lawtonsean1-dev/deep-space-workstation`  
🔗 **Live Web Application:** `https://deep-space-workstation.streamlit.app`


<img width="1917" height="867" alt="Screenshot 2026-06-22 115355" src="https://github.com/user-attachments/assets/ea5ed8f5-5769-4b25-b36c-5c23c8eb40cc" />
<img width="1918" height="1078" alt="Screenshot 2026-06-22 115437" src="https://github.com/user-attachments/assets/1c5d949d-0fe0-4bde-b99a-5822e046bfcd" />
<img width="1918" height="1078" alt="Screenshot 2026-06-22 115452" src="https://github.com/user-attachments/assets/b265fd28-66c8-459c-8472-68e5e491a333" />

---

## 🧱 Technical Stack Dependencies

The system pipeline relies on the following open-source frameworks:
* **`streamlit`** - Frontend UI component layout grid and HTML/CSS styling injection.
* **`lightkurve`** - Time-series photometry archive search, noise flattening, and BLS periodogram scans.
* **`astropy`** - Equatorial coordinate handling (`SkyCoord`) and celestial constellation boundary resolution.
* **`astroquery`** - SIMBAD coordinate resolver API connections.
* **`matplotlib`** - System vector trajectory graphics and photometric plotting.
* **`numpy`** - High-performance array mechanics and trigonometric orbital math.
* **`requests`** - Secure connection management for NASA's database endpoints.

---

## 🗺️ Next-Gen Project Roadmap

- [ ] **Interactive Plotly Engine Migration** — Upgrade static light curves and system maps to fully interactive, touch-zoomable Plotly graphs for enhanced mobile tracking and precision point hover readouts.
- [ ] **Asymmetric Scientific Error Intervals** — Refactor database queries to extract both `err1` (upper bounds) and `err2` (lower bounds) to display advanced scientific precision blocks (e.g., $1.25_{-0.05}^{+0.08}$).
- [ ] **Multi-Planet System Orbit Stacking** — Implement nested parametric loops to automatically draw every planet's trajectory simultaneously if the system parameters register multiple confirmed worlds (`sy_pnum > 1`).
- [ ] **Real-time Spectral Class Estimation** — Process effective temperatures ($T_{\text{eff}}$) through Morgan-Keenan criteria to display the star's actual spectral class classification (e.g., *M-Dwarf*, *G-Type Main Sequence*) with custom color-coded indicators.

---
*Developed as an open-source tool for rapid target profiling and deep-space exoplanetary analysis. Clear skies!*
