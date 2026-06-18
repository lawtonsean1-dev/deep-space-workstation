# 🌌 Deep Space System Dossier Workstation

![Streamlit App](https://img.shields.io/badge/Streamlit-Live%20App-ff4b4b?style=for-the-badge&logo=streamlit)
![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Contributions](https://img.shields.io/badge/Contributions-Welcome-brightgreen?style=for-the-badge)

A sleek, night-vision-friendly cockpit for rapid exoplanet profiling, powered by Python, Streamlit, Astropy, and Lightkurve.

## 🚀 Key Features

*   **NASA Exoplanet Archive Integration:** Automates data retrieval pipelines to pull physical, orbital, and atmospheric metrics directly from official NASA archives.
*   **Live Transit Plotting:** Leverages `lightkurve` to process and plot stellar brightness data, allowing users to visualise exoplanet transit dips in real time.
*   **Tactical Night-Vision UI:** Features a custom, low-light-friendly "cyberpunk dark-sky" theme optimised for amateur astronomers to use in the field without ruining their night adaptation.
*   **Rapid Profiling Workflow:** Designed as a streamlined, intuitive cockpit for quickly cross-referencing and analysing candidate target stars.

🔗 **Live App Link:** https://deep-space-workstation.streamlit.app/

<img width="1919" height="821" alt="Screenshot 2026-06-17 101336" src="https://github.com/user-attachments/assets/efd8d6d2-6b22-4220-95e3-d97a0275785d" />
<img width="1919" height="825" alt="Screenshot 2026-06-17 101359" src="https://github.com/user-attachments/assets/5c662ed8-e9e8-462b-a0c5-cc4d6868ac32" />
<img width="1919" height="822" alt="Screenshot 2026-06-17 101418" src="https://github.com/user-attachments/assets/0dbb0b3e-676b-4365-9849-34a64d4692eb" />
<img width="1919" height="815" alt="Screenshot 2026-06-17 101431" src="https://github.com/user-attachments/assets/68586adc-baf7-4485-aaae-ff1f29939b50" />


## 🗺️ Project Roadmap
Help us build the ultimate amateur astronomy workstation! Here is what we are building next:
- [x] Create a core NASA `pscomppars` data retrieval pipeline.
- [x] Implement live `lightkurve` transit plotting.
- [x] Cyberpunk dark-sky theme overhaul.
- [ ] Add error margins (\pm) to host stellar metrics.
- [ ] Build a 2D orbital trajectory visualiser using `matplotlib`.
- [ ] Integrate a SIMBAD coordinate resolver for non-indexed target stars.

## 🛠️ How to Give Feedback & Report Bugs
I would love to hear from amateur astronomers and hobbyists! If you want to request a feature or report a bug:
1. Click on the **Issues** tab at the top of this page.
2. Click the green **New Issue** button.
3. Email me at lawtonsean1@gmail.com

## 🌌 Data Sources & Acknowledgments

This workstation is built upon the incredible open data and open-source software provided by the astronomical community. Project data and core functionality are powered by:

* **[NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/):** Providing the foundational data pipelines for known exoplanets, including comprehensive physical and orbital characteristics.
* **[Lightkurve](https://docs.lightkurve.org/):** A beautiful Python package for analysing astronomical light curves, specifically utilised here for live transit plotting using Kepler, K2, and TESS data.
* **[Astropy](https://www.astropy.org/):** A core community-led Python package providing critical tools, coordinate transformations, and astronomical calculations.
* **[SIMBAD Astronomical Database](http://simbad.u-strasbg.fr/simbad/):** Utilised for coordinate resolving and cross-referencing non-indexed target stars.
