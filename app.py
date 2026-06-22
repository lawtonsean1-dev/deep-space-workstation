import streamlit as st
import lightkurve as lk
import matplotlib.pyplot as plt
import numpy as np
import requests
import urllib.parse
from astropy.coordinates import SkyCoord
import astropy.units as u

# --- THEME & CONFIGURATION ---
st.set_page_config(
    page_title="Deep Space Workstation", 
    page_icon="🌌", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom HUD Header Layout
st.markdown(
    """
    <div style='text-align: center; padding: 10px; margin-bottom: 20px;'>
        <h1 style='color: #00ffff; text-shadow: 0 0 15px rgba(0,255,255,0.6); font-family: monospace; letter-spacing: 2px; margin-bottom: 5px;'>
            🌌 DEEP SPACE SYSTEM DOSSIER WORKSTATION
        </h1>
        <p style='color: #8a99ad; font-family: monospace; font-size: 14px; margin-top: 0px;'>
            Sub-Orbital Data Pipeline // Connected to NASA Composite Archives
        </p>
    </div>
    """, 
    unsafe_allow_html=True
)

# --- SIDEBAR CONTROL COCKPIT ---
with st.sidebar:
    st.markdown("<h3 style='color: #00e6ff; font-family: monospace;'>🎛️ TARGET CONTROL</h3>", unsafe_allow_html=True)
    target = st.text_input("Enter Target Star Name:", "Kepler-10")
    st.markdown("---")
    st.markdown(
        """
        <div style='font-size: 12px; color: #64748b; font-family: monospace;'>
            SYSTEM STATUS: <span style='color: #10b981;'>ONLINE</span><br>
            ARCHIVE REGISTRY: PSCOMPPARS<br>
            PIPELINE VERSION: 2.1.0
        </div>
        """,
        unsafe_allow_html=True
    )

def fetch_nasa_archive_data(star_name):
    clean_name = star_name.strip().upper().replace("-", "%").replace(" ", "%")
    
    # UPGRADED: Core SQL query now grabs scientific error boundaries
    query = (
        f"select top 1 pl_name, hostname, ra, dec, sy_dist, pl_orbsmax, pl_orbeccen, "
        f"st_rad, st_raderr1, st_mass, st_masserr1, st_teff, st_tefferr1, sy_pnum "
        f"from pscomppars where upper(hostname) like '%{clean_name}%'"
    )
    
    url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=" + urllib.parse.quote(query) + "&format=json"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data[0], url
    except:
        pass
    return None, url

# --- MAIN WORKSPACE PIPELINE ---
if st.sidebar.button("Run System Compilation", use_container_width=True):
    with st.spinner("Harvesting comprehensive system metrics from NASA Composite Archives..."):
        archive_data, last_url = fetch_nasa_archive_data(target)
        
        lc_found = False
        periodogram = None
        folded_lc = None
        r_planet_earth = None
        transit_depth = 0.0
        
        if archive_data is not None:
            lk_target = archive_data.get('hostname', target)
            try:
                search_result = lk.search_lightcurve(lk_target, cadence='long')
                if len(search_result) == 0:
                    search_result = lk.search_lightcurve(target, cadence='long')
                    
                if len(search_result) > 0:
                    lc = search_result[0].download()
                    if lc is not None:
                        flat_lc = lc.flatten(window_length=401)
                        periodogram = flat_lc.to_periodogram(method='bls', minimum_period=0.5, maximum_period=5)
                        best_period = periodogram.period_at_max_power
                        best_t0 = periodogram.transit_time_at_max_power
                        transit_depth = periodogram.depth_at_max_power
                        folded_lc = flat_lc.fold(period=best_period, epoch_time=best_t0)
                        lc_found = True
            except Exception as e:
                st.sidebar.warning(f"Lightkurve skipped plotting processing: {e}")

        if archive_data is None:
            st.error(f"❌ Could not find comprehensive archive data for '{target}'.")
        else:
            st.success(f"🌌 Full Dossier Compiled for the {archive_data['hostname']} System!")
            
            # Extract Metrics and Error Boundaries
            ra_raw = archive_data.get('ra')
            dec_raw = archive_data.get('dec')
            distance_pc = archive_data.get('sy_dist')
            semi_major_au = archive_data.get('pl_orbsmax')
            eccentricity = archive_data.get('pl_orbeccen', 0.0)
            
            # Primary Values
            r_star = archive_data.get('st_rad')
            m_star = archive_data.get('st_mass')
            teff = archive_data.get('st_teff')
            
            # UPGRADED: Extract uncertainty boundaries (defaulting to 0.0 if empty)
            r_star
