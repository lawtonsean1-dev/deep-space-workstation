import streamlit as st
import lightkurve as lk
import matplotlib.pyplot as plt
import numpy as np
import requests
import urllib.parse
from astropy.coordinates import SkyCoord
import astropy.units as u
from astroquery.simbad import Simbad

# --- THEME & CONFIGURATION ---
st.set_page_config(
    page_title="Orbit-Sentinel", 
    page_icon="🌌", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom HUD Header Layout
st.markdown(
    """
    <div style='text-align: center; padding: 10px; margin-bottom: 20px;'>
        <h1 style='color: #00ffff; text-shadow: 0 0 15px rgba(0,255,255,0.6); font-family: monospace; letter-spacing: 2px; margin-bottom: 5px;'>
            🌌 ORBIT-SENTINEL
        </h1>
        <p style='color: #8a99ad; font-family: monospace; font-size: 14px; margin-top: 0px;'>
            Sub-Orbital Data Pipeline // Connected to NASA & SIMBAD Registries
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
            PRIMARY LOG: NASA PSCOMPPARS<br>
            FALLBACK LOG: CDS SIMBAD RESOLVER<br>
            PIPELINE VERSION: 2.4.0
        </div>
        """,
        unsafe_allow_html=True
    )

def fetch_nasa_archive_data(star_name):
    clean_name = star_name.strip().upper()
    query = (
        f"select pl_name, hostname, ra, dec, sy_dist, pl_orbsmax, pl_orbeccen, "
        f"st_rad, st_raderr1, st_mass, st_masserr1, st_teff, st_tefferr1, sy_pnum "
        f"from pscomppars where upper(hostname) = '{clean_name}'"
    )
    url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=" + urllib.parse.quote(query) + "&format=json"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data  # Returns all rows matching the system
    except:
        pass
    return None

def resolve_via_simbad(star_name):
    try:
        clean_name = star_name.strip()
        
        # 1. Ask Astropy to hit the CDS name resolver database directly
        coord = SkyCoord.from_name(clean_name)
        
        # 2. Try to grab a standardized Main ID using a simpler query type
        id_table = Simbad.query_objectids(clean_name)
        if id_table is not None and len(id_table) > 0:
            raw_id = id_table[0][0]
            id_str = raw_id.decode('utf-8') if isinstance(raw_id, bytes) else str(raw_id)
        else:
            id_str = clean_name
            
        # 3. Deliver a clean pseudo-payload back wrapped in an iterable list format
        simbad_payload = [{
            'pl_name': f"{clean_name} b (Candidate)",
            'hostname': id_str,
            'ra': float(coord.ra.deg),
            'dec': float(coord.dec.deg),
            'sy_dist': None,
            'pl_orbsmax': 1.0, 
            'pl_orbeccen': 0.0,
            'st_rad': 1.0,
            'st_mass': 1.0,
            'st_teff': 5778.0,
            'sy_pnum': 1,
            'source': 'SIMBAD Astronomical Database'
        }]
        return simbad_payload
    except Exception as e:
        st.sidebar.error(f"Engine Fallback Notice: {e}")
    return None

# --- MAIN WORKSPACE PIPELINE ---

# Initialize operational state values if missing from run history
if "system_planets" not in st.session_state:
    st.session_state.system_planets = None
if "dataSource" not in st.session_state:
    st.session_state.dataSource = ""

# Data execution block triggered on explicit request form execution
if st.sidebar.button("Run System Compilation", use_container_width=True):
    with st.spinner("Harvesting telemetry from international sky catalogs..."):
        fetched_data = fetch_nasa_archive_data(target)
        dataSource = "NASA Exoplanet Archive"
        
        if fetched_data is None:
            fetched_data = resolve_via_simbad(target)
            dataSource = "CDS SIMBAD Network"
            
        st.session_state.system_planets = fetched_data
        st.session_state.dataSource = dataSource

# Render layout structures if system telemetry records exist in session storage
if st.session_state.system_planets is not None:
    system_planets = st.session_state.system_planets
    dataSource = st.session_state.dataSource
    
    st.success(f"🌌 Full System Dossier Compiled via {dataSource}! Found {len(system_planets)} planetary body/bodies.")
    
    # Selection component triggers safe full-script reruns without deleting session memory pools
    planet_names = [planet.get('pl_name') for planet in system_planets]
    selected_planet_name = st.selectbox("🪐 SELECT PLANETARY OBJECT TO ANALYZE:", planet_names)
    
    # Isolate selected record data structures
    archive_data = next(p for p in system_planets if p.get('pl_name') == selected_planet_name)
    
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

    # Numeric structural extractions
    ra_raw = archive_data.get('ra')
    dec_raw = archive_data.get('dec')
    distance_pc = archive_data.get('sy_dist')
    semi_major_au = archive_data.get('pl_orbsmax')
    
    eccentricity = archive_data.get('pl_orbeccen')
    eccentricity = float(eccentricity) if eccentricity is not None else 0.0
    
    r_star = archive_data.get('st_rad')
    r_star = float(r_star) if r_star is not None else 1.0
    
    m_star = archive_data.get('st_mass')
    m_star = float(m_star) if m_star is not None else 1.0
    
    teff = archive_data.get('st_teff')
    teff = float(teff) if teff is not None else 5778.0
    
    r_star_err = archive_data.get('st_raderr1', 0.0)
    m_star_err = archive_data.get('st_masserr1', 0.0)
    teff_err = archive_data.get('st_tefferr1', 0.0)
    
    distance_ly = distance_pc * 3.26156 if distance_pc else None
    
    if semi_major_au:
        semi_major_au = float(semi_major_au)
        semi_minor_au = semi_major_au * np.sqrt(1 - eccentricity**2)
    else:
        semi_major_au = None
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

    # Classification & Color Mapping Layout
    if r_planet_earth is not None:
        if r_planet_earth < 1.2:
            classification = "Earth-sized Rocky Planet"
            class_color = "#10b981"
        elif r_planet_earth < 2.0:
            classification = "Super-Earth"
            class_color = "#3b82f6"
        elif r_planet_earth < 4.0:
            classification = "Sub-Neptune"
            class_color = "#f59e0b"
        else:
            classification = "Gas Giant"
            class_color = "#ef4444"
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
            
            mass_val = f"{m_star:.2f}" if m_star else "N/A"
            mass_delta = f"± {m_star_err:.2f}" if m_star and m_star_err else None
            c2.metric("Stellar Mass (M☉)", mass_val, delta=mass_delta, delta_color="off")
            
            rad_val = f"{r_star:.2f}" if r_star else "N/A"
            rad_delta = f"± {r_star_err:.2f}" if r_star and r_star_err else None
            c3.metric("Stellar Radius (R☉)", rad_val, delta=rad_delta, delta_color="off")
            
            teff_val = f"{int(teff):,}" if teff else "N/A"
            teff_delta = f"± {int(teff_err):,}" if teff and teff_err else None
            c4.metric("Stellar Temperature (K)", teff_val, delta=teff_delta, delta_color="off")
        
        st.markdown(f"<h4 style='color: #00e6ff; font-family: monospace; margin-top:20px;'>🪐 PLANETARY PROFILE: {archive_data.get('pl_name')}</h4>", unsafe_allow_html=True)
        
        with st.container(border=True):
            col_num, col_viz = st.columns([1, 1.2])
            
            with col_num:
                st.metric("Semi-Major Axis (a)", f"{semi_major_au:.4f} AU" if semi_major_au else "N/A")
                st.metric("Semi-Minor Axis (b)", f"{semi_minor_au:.4f} AU" if semi_minor_au else "N/A")
                st.metric("Orbital Eccentricity (e)", f"{eccentricity:.4f}" if eccentricity else "0.0000")
                
                if r_planet_earth is not None:
                    st.markdown(
                        f"""
                        <div style='padding: 12px; background-color: #1e293b; border-left: 5px solid {class_color}; margin-top: 20px; font-family: monospace; border-radius: 4px;'>
                            <span style='color: #8a99ad;'>DERIVED PHYSICAL CLASSIFICATION:</span><br>
                            <strong style='color: {class_color}; font-size: 16px;'>{r_planet_earth:.2f} Earth Radii<br>{classification.upper()}</strong>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                    
            with col_viz:
                if semi_major_au and semi_minor_au:
                    plt.style.use('dark_background')
                    fig_orb, ax_orb = plt.subplots(figsize=(5, 4.5))
                    fig_orb.patch.set_facecolor('#0f172a')
                    ax_orb.set_facecolor('#0f172a')
                    
                    theta = np.linspace(0, 2*np.pi, 200)
                    x_orbit = semi_major_au * np.cos(theta)
                    y_orbit = semi_minor_au * np.sin(theta)
                    
                    focal_shift = np.sqrt(semi_major_au**2 - semi_minor_au**2)
                    x_orbit_shifted = x_orbit - focal_shift
                    
                    ax_orb.plot(x_orbit_shifted, y_orbit, color='#38bdf8', linestyle='--', alpha=0.8, lw=1.5, label='Orbital Path')
                    ax_orb.scatter(0, 0, color='#f59e0b', s=180, edgecolors='#fff', linewidths=1.5, zorder=5, label='Host Star')
                    ax_orb.scatter(semi_major_au - focal_shift, 0, color=class_color, s=90, zorder=5, label='Current Sector Vector')
                    
                    ax_orb.set_xlabel('Distance Axis (AU)', color='#8a99ad', fontfamily='monospace', fontsize=9)
                    ax_orb.set_ylabel('Distance Axis (AU)', color='#8a99ad', fontfamily='monospace', fontsize=9)
                    ax_orb.set_title("2D ORBITAL TRAJECTORY SYSTEM MAP", color='#00e6ff', fontfamily='monospace', fontsize=11, pad=10)
                    ax_orb.grid(True, color='#334155', linestyle=':', alpha=0.5)
                    ax_orb.legend(loc='upper right', facecolor='#1e293b', edgecolor='#334155', fontsize=8)
                    ax_orb.set_aspect('equal', 'datalim')
                    st.pyplot(fig_orb)
                else:
                    st.info("📊 Orbital matrix trajectories cannot be drawn: Missing Semi-Major Axis parameters.")

    with tab3:
        st.markdown("<h4 style='color: #00e6ff; font-family: monospace; margin-top:15px;'>📊 RAW MISSION DATA TIME-SERIES</h4>", unsafe_allow_html=True)
        if lc_found and periodogram is not None and folded_lc is not None:
            plt.style.use('dark_background')
            col_plot1, col_plot2 = st.columns(2)
            
            with col_plot1:
                with st.container(border=True):
                    fig1, ax1 = plt.subplots(figsize=(6, 3.5))
                    fig1.patch.set_facecolor('#0f172a')
                    ax1.set_facecolor('#0f172a')
                    
                    periodogram.plot(ax=ax1, color='#00ffff', lw=1.5)
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
            
elif target:
    st.info("📡 System offline. Input a target star and select 'Run System Compilation' to initiate pipeline diagnostics.")
