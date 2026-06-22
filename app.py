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
    clean_name = star_name.strip().upper()
    
    # FIX: Using exact match "=" instead of loose "like %" to avoid fetching wrong targets
    query = (
        f"select top 1 pl_name, hostname, ra, dec, sy_dist, pl_orbsmax, pl_orbeccen, "
        f"st_rad, st_raderr1, st_mass, st_masserr1, st_teff, st_tefferr1, sy_pnum "
        f"from pscomppars where upper(hostname) = '{clean_name}'"
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
if st.
