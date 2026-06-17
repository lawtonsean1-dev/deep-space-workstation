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
            PIPELINE VERSION: 2.0.0
        </div>
        """,
        unsafe_allow_html=True
    )

def fetch_nasa_archive_data(star_name):
    clean_name = star_name.strip().upper().replace("-", "%").replace(" ", "%")
    query = f"select top 1 pl_name, hostname, ra, dec, sy_dist, pl_orbsmax, pl_orbeccen, st_rad, st_mass, st_teff, sy_pnum from pscomppars where upper(hostname) like '%{clean_name}%'"
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
            
            # Extract Metrics
            ra_raw = archive_data.get('ra')
            dec_raw = archive_data.get('dec')
            distance_pc = archive_data.get('sy_dist')
            semi_major_au = archive_data.get('pl_orbsmax')
            eccentricity = archive_data.get('pl_orbeccen', 0.0)
            r_star = archive_data.get('st_rad', 1.0) if archive_data.get('st_rad') else 1.0
            m_star = archive_data.get('st_mass', 1.0) if archive_data.get('st_mass') else 1.0
            teff = archive_data.get('st_teff', 5778) if archive_data.get('st_teff') else 5778
            
            eccentricity = eccentricity if eccentricity is not None else 0.0
            distance_ly = distance_pc * 3.26156 if distance_pc else None
            
            if semi_major_au:
                semi_minor_au = semi_major_au * np.sqrt(1 - eccentricity**2)
            else:
                semi_minor_au = None

            if lc_found:
                try:
                    r_planet_solar = np.sqrt(transit_depth) * r_star
                    r_planet_earth = getattr(r_planet_solar, 'value', r_planet_solar) * 109.2
                except:
                    r_planet_earth = None

            constellation = "Unknown"
            if ra_raw is not None and dec_raw is not None:
                try:
                    coord = SkyCoord(ra=ra_raw*u.degree, dec=dec_raw*u.degree, frame='icrs')
                    constellation = coord.get_constellation()
                except:
                    pass

            # Classification & Color Coding
            if r_planet_earth is not None:
                if r_planet_earth < 1.2:
                    classification = "Earth-sized Rocky Planet"
                    class_color = "#10b981" # Emerald Green
                elif r_planet_earth < 2.0:
                    classification = "Super-Earth"
                    class_color = "#3b82f6" # Sky Blue
                elif r_planet_earth < 4.0:
                    classification = "Sub-Neptune"
                    class_color = "#f59e0b" # Warning Amber
                else:
                    classification = "Gas Giant"
                    class_color = "#ef4444" # Alert Red
            else:
                classification = "Unknown Classification"
                class_color = "#64748b"

            # --- MULTI-TAB SCI-FI WORKSPACE ---
            tab1, tab2, tab3 = st.tabs(["🗺️ CELESTIAL POSITIONING", "📐 ORBITAL TELEMETRY", "🔭 SENSOR PLOTS"])
            
            with tab1:
                st.markdown("<h4 style='color: #00e6ff; font-family: monospace; margin-top:15px;'>📍 EQUATORIAL PROFILE</h4>", unsafe_allow_html=True)
                with st.container(border=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Right Ascension (RA)", f"{ra_raw:.4f}°" if ra_raw else "N/A")
                        st.metric("Declination (Dec)", f"{dec_raw:+.4f}°" if dec_raw else "N/A")
                    with col2:
                        st.metric("Distance", f"{distance_ly:.2f} Light Years" if distance_ly else "N/A")
                        st.markdown(
                            f"""
                            <div style='padding: 10px; background-color: #1e293b; border-left: 4px solid #00e6ff; margin-top: 15px; font-family: monospace; border-radius: 4px;'>
                                <span style='color: #8a99ad;'>CONSTELLATION SECTOR:</span><br>
                                <strong style='color: #e2e8f0; font-size: 16px;'>{constellation.upper()}</strong>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )

            with tab2:
                st.markdown("<h4 style='color: #00e6ff; font-family: monospace; margin-top:15px;'>🌟 HOST STELLAR ARCHITECTURE</h4>", unsafe_allow_html=True)
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Confirmed System Planets", f"{archive_data.get('sy_pnum', '1')}")
                    c2.metric("Stellar Mass (M☉)", f"{m_star:.2f}" if m_star else "N/A")
                    c3.metric("Stellar Radius (R☉)", f"{r_star:.2f}" if r_star else "N/A")
                    c4.metric("Stellar Temperature", f"{int(teff):,} K" if teff else "N/A")
                
                st.markdown(f"<h4 style='color: #00e6ff; font-family: monospace; margin-top:20px;'>🪐 PLANETARY PROFILE: {archive_data.get('pl_name')}</h4>", unsafe_allow_html=True)
                with st.container(border=True):
                    cx1, cx2, cx3 = st.columns(3)
                    cx1.metric("Semi-Major Axis (a)", f"{semi_major_au:.4f} AU" if semi_major_au else "N/A")
                    cx2.metric("Semi-Minor Axis (b)", f"{semi_minor_au:.4f} AU" if semi_minor_au else "N/A")
                    cx3.metric("Orbital Eccentricity (e)", f"{eccentricity:.4f}" if eccentricity else "0.0000")
                    
                    if r_planet_earth is not None:
                        st.markdown(
                            f"""
                            <div style='padding: 12px; background-color: #1e293b; border-left: 5px solid {class_color}; margin-top: 20px; font-family: monospace; border-radius: 4px;'>
                                <span style='color: #8a99ad;'>DERIVED PHYSICAL CLASSIFICATION:</span><br>
                                <strong style='color: {class_color}; font-size: 18px;'>{r_planet_earth:.2f} Earth Radii — {classification.upper()}</strong>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )

            with tab3:
                st.markdown("<h4 style='color: #00e6ff; font-family: monospace; margin-top:15px;'>📊 RAW MISSION DATA TIME-SERIES</h4>", unsafe_allow_html=True)
                if lc_found and periodogram is not None and folded_lc is not None:
                    
                    # Force Matplotlib into a clean dark-sky format
                    plt.style.use('dark_background')
                    
                    col_plot1, col_plot2 = st.columns(2)
                    
                    with col_plot1:
                        with st.container(border=True):
                            fig1, ax1 = plt.subplots(figsize=(6, 3.5))
                            fig1.patch.set_facecolor('#0f172a') # Matches Streamlit container background
                            ax1.set_facecolor('#0f172a')
                            
                            periodogram.plot(ax=ax1, color='#00e6ff', lw=1.5)
                            ax1.set_title("BLS Periodogram Power Scan", color='#00e6ff', fontfamily='monospace', fontsize=11)
                            ax1.grid(True, color='#334155', linestyle=':', alpha=0.6)
                            st.pyplot(fig1)
                            
                    with col_plot2:
                        with st.container(border=True):
                            fig2, ax2 = plt.subplots(figsize=(6, 3.5))
                            fig2.patch.set_facecolor('#0f172a')
                            ax2.set_facecolor('#0f172a')
                            
                            folded_lc.scatter(ax=ax2, color='#ff4500', alpha=0.4, s=3)
                            ax2.set_title("Folded Light Curve Transit Signature", color='#00e6ff', fontfamily='monospace', fontsize=11)
                            ax2.grid(True, color='#334155', linestyle=':', alpha=0.6)
                            st.pyplot(fig2)
                else:
                    st.warning("📡 Photometric light curve files are currently unavailable for this specific sector configuration.")
