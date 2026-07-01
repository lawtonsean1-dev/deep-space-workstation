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
    page_title="Orbit Sentinel", 
    page_icon="🛰️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 1. CANVAS STARFIELD BACKGROUND ENGINE ---
st.markdown(
    """
    <canvas id="starfield" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -1; pointer-events: none;"></canvas>
    <script>
        const canvas = document.getElementById('starfield');
        const ctx = canvas.getContext('2d');
        let stars = [];
        
        function resize() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
        window.addEventListener('resize', resize);
        resize();

        for(let i=0; i<150; i++) {
            stars.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                size: Math.random() * 1.5,
                speed: Math.random() * 0.15 + 0.05
            });
        }

        function animate() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#0f172a'; 
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            ctx.fillStyle = 'rgba(0, 255, 255, 0.6)';
            stars.forEach(star => {
                ctx.fillRect(star.x, star.y, star.size, star.size);
                star.y += star.speed;
                if(star.y > canvas.height) {
                    star.y = 0;
                    star.x = Math.random() * canvas.width;
                }
            });
            requestAnimationFrame(animate);
        }
        animate();
    </script>
    """,
    unsafe_allow_html=True
)

# --- 2. DYNAMIC RADAR SCANNING HEADER OVERLAY ---
st.markdown(
    """
    <style>
    @keyframes radar-sweep {
        0% { border-color: rgba(0, 255, 255, 0.2); box-shadow: 0 0 5px rgba(0, 255, 255, 0.1); }
        50% { border-color: rgba(0, 255, 255, 0.7); box-shadow: 0 0 20px rgba(0, 255, 255, 0.3); }
        100% { border-color: rgba(0, 255, 255, 0.2); box-shadow: 0 0 5px rgba(0, 255, 255, 0.1); }
    }
    .hud-box {
        text-align: center; 
        padding: 20px; 
        margin-bottom: 25px;
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid #00ffff;
        border-radius: 8px;
        animation: radar-sweep 4s infinite ease-in-out;
        backdrop-filter: blur(4px);
    }
    </style>
    
    <div class="hud-box">
        <h1 style='color: #00ffff; text-shadow: 0 0 15px rgba(0,255,255,0.6); font-family: monospace; letter-spacing: 3px; margin-bottom: 5px; margin-top:0;'>
            🛰️ ORBIT SENTINEL // SENSORS HUD
        </h1>
        <p style='color: #8a99ad; font-family: monospace; font-size: 13px; margin-top: 0px; letter-spacing: 1px;'>
            Orbital Proximity Scan // Bridge Mainframe Telemetry Pipeline
        </p>
    </div>
    """, 
    unsafe_allow_html=True
)

# --- SIDEBAR CONTROL COCKPIT ---
with st.sidebar:
    st.markdown("<h3 style='color: #00e6ff; font-family: monospace;'>🎛️ COCKPIT NAV-RADAR</h3>", unsafe_allow_html=True)
    target = st.text_input("Input Sector Vector Star:", "Kepler-10")
    
    st.markdown("---")
    st.markdown("<h5 style='color: #ff9d00; font-family: monospace;'>📡 COUPLING LINK CONTROLS</h5>", unsafe_allow_html=True)
    enable_lightkurve = st.toggle("DEPLOY DEEP SPACE LIGHT SIGNAL LINK", value=False)
    
    st.markdown("---")
    st.markdown(
        """
        <div style='font-size: 12px; color: #64748b; font-family: monospace;'>
            SHIP SCANNER STATUS: <span style='color: #10b981;'>ONLINE</span><br>
            PRIMARY LOG: NASA EXOPLANET ARCHIVE<br>
            FALLBACK LOG: CDS SIMBAD RECON<br>
            SYS CORE VERSION: 3.3.1 (BUGFIX)
        </div>
        """,
        unsafe_allow_html=True
    )

def fetch_nasa_archive_data(star_name):
    clean_name = star_name.strip().upper()
    query = (
        f"select pl_name, hostname, ra, dec, sy_dist, pl_orbsmax, pl_orbeccen, "
        f"st_rad, st_raderr1, st_mass, st_masserr1, st_teff, st_tefferr1, sy_pnum, "
        f"pl_eqt, pl_insol, pl_bmasse, st_met, discoverymethod, disc_year, disc_facility, st_spectype "
        f"from pscomppars where upper(hostname) = '{clean_name}'"
    )
    url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=" + urllib.parse.quote(query) + "&format=json"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data, "NASA Exoplanet Archive"
    except Exception as e:
        st.sidebar.error(f"NASA Query Error: {e}")
    return None, None

def resolve_via_simbad(star_name):
    try:
        clean_name = star_name.strip()
        custom_simbad = Simbad()
        custom_simbad.add_typed_votable_fields('parallax', 'sp')
        result_table = custom_simbad.query_object(clean_name)
        
        if result_table is not None and len(result_table) > 0:
            coord = SkyCoord.from_name(clean_name)
            
            # Safe parsing for empty parallax cells
            try:
                parallax = result_table['PLX_VALUE'][0]
                distance_pc = (1000 / parallax) if (parallax and parallax > 0) else None
            except:
                distance_pc = None
            
            # Safe decoding for empty or missing spectrum cells
            try:
                raw_sp = result_table['SP_TYPE'][0]
                sp_str = raw_sp.decode('utf-8') if isinstance(raw_sp, bytes) else str(raw_sp)
                if not sp_str or sp_str == 'None' or sp_str == '--' or sp_str == 'masked':
                    sp_str = "UNDETERMINED CLASS"
            except:
                sp_str = "UNDETERMINED CLASS"
            
            simbad_payload = [{
                'pl_name': None, 
                'hostname': clean_name,
                'ra': float(coord.ra.deg),
                'dec': float(coord.dec.deg),
                'sy_dist': distance_pc,
                'pl_orbsmax': None, 
                'pl_orbeccen': None,
                'st_rad': None,
                'st_mass': None,
                'st_teff': None,
                'sy_pnum': 0,
                'pl_eqt': None,
                'pl_insol': None,
                'pl_bmasse': None,
                'st_met': None,
                'discoverymethod': None,
                'disc_year': None,
                'disc_facility': None,
                'st_spectype': sp_str
            }]
            return simbad_payload, "CDS SIMBAD Astronomical Database"
    except Exception as e:
        st.sidebar.error(f"SIMBAD Fallback Error: {e}")
    return None, None

# --- MAIN WORKSPACE PIPELINE ---
if "system_planets" not in st.session_state:
    st.session_state.system_planets = None
if "dataSource" not in st.session_state:
    st.session_state.dataSource = ""

if st.sidebar.button("Execute Planetary Proximity Sweep", use_container_width=True):
    # --- FULL SCREEN SCI-FI RADAR SCANNING LOADING OVERLAY ---
    scan_placeholder = st.empty()
    scan_placeholder.markdown(
        """
        <style>
        @keyframes radar-pulse {
            0% { transform: scale(0.1); opacity: 0.8; }
            80% { opacity: 0.4; }
            100% { transform: scale(1.2); opacity: 0; }
        }
        @keyframes sweep {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        .radar-container {
            position: relative;
            width: 200px;
            height: 200px;
            margin: 40px auto;
            background: radial-gradient(circle, rgba(0,255,255,0.05) 0%, rgba(15,23,42,0.6) 80%);
            border: 2px solid rgba(0, 255, 255, 0.2);
            border-radius: 50%;
            overflow: hidden;
            box-shadow: 0 0 15px rgba(0, 255, 255, 0.1);
        }
        .radar-sweep {
            position: absolute;
            width: 100%;
            height: 100%;
            background: conic-gradient(from 0deg, transparent 50%, rgba(0, 255, 255, 0.4) 100%);
            animation: sweep 2s infinite linear;
            transform-origin: center;
            border-radius: 50%;
        }
        .radar-pulse {
            position: absolute;
            width: 100%;
            height: 100%;
            border: 2px solid rgba(0, 255, 255, 0.4);
            border-radius: 50%;
            animation: radar-pulse 2s infinite ease-out;
            top: 0; left: 0;
            box-sizing: border-box;
        }
        .telemetry-text {
            text-align: center;
            font-family: monospace;
            color: #00ffff;
            text-shadow: 0 0 8px rgba(0,255,255,0.5);
            letter-spacing: 2px;
            font-size: 14px;
            margin-top: 15px;
        }
        </style>
        
        <div class="radar-container">
            <div class="radar-pulse"></div>
            <div class="radar-sweep"></div>
        </div>
        <div class="telemetry-text">🛰️ ENGAGING SENSOR BEAM ARRAY // ANALYZING ORBITAL TARGETS...</div>
        """,
        unsafe_allow_html=True
    )

    fetched_data, source_name = fetch_nasa_archive_data(target)
    if fetched_data is None:
        fetched_data, source_name = resolve_via_simbad(target)
        
    st.session_state.system_planets = fetched_data
    st.session_state.dataSource = source_name
    scan_placeholder.empty()

if st.session_state.system_planets is not None:
    system_planets = st.session_state.system_planets
    dataSource = st.session_state.dataSource
    
    has_planets = any(p.get('pl_name') is not None for p in system_planets)
    
    if has_planets:
        st.success(f"🌌 Sensor lock established via {dataSource}! Found {len(system_planets)} confirmed planets in orbit.")
        planet_names = [planet.get('pl_name') for planet in system_planets]
        selected_planet_name = st.selectbox("🛸 LOCK BRIDGE SENSORS ON PLANET TARGET:", planet_names)
        archive_data = next(p for p in system_planets if p.get('pl_name') == selected_planet_name)
    else:
        st.warning(f"⚠️ Stellar target verified via {dataSource}. Crucial Note: 0 verified orbiting exoplanets detected in archives.")
        archive_data = system_planets[0]

    # Telemetry extraction with safe fallback handling
    ra_raw = archive_data.get('ra')
    dec_raw = archive_data.get('dec')
    distance_pc = archive_data.get('sy_dist')
    distance_ly = distance_pc * 3.26156 if distance_pc else None
    
    st_spectype = archive_data.get('st_spectype')
    if not st_spectype or str(st_spectype).strip() in ['None', '', '--', 'nan']:
        st_spectype = "UNDETERMINED CLASS"
    
    constellation = "Unknown"
    if ra_raw is not None and dec_raw is not None:
        try:
            coord = SkyCoord(ra=ra_raw*u.degree, dec=dec_raw*u.degree, frame='icrs')
            constellation = coord.get_constellation()
        except:
            pass

    # Layout generation
    if has_planets:
        tab1, tab2, tab3, tab4 = st.tabs([
            "🗺️ NAVIGATIONAL COORD", 
            "📐 ORBIT PROFILE", 
            "☣️ ATMOSPHERIC HAZARD MATRIX", 
            "📊 SENSOR TIME-SERIES"
        ])
    else:
        tab1, = st.tabs(["🗺️ NAVIGATIONAL COORD"])

    with tab1:
        st.markdown("<h4 style='color: #00e6ff; font-family: monospace; margin-top:15px;'>📍 TARGET EQUATORIAL PROFILE</h4>", unsafe_allow_html=True)
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Right Ascension (RA)", f"{ra_raw:.4f}°" if ra_raw else "N/A")
                st.metric("Declination (Dec)", f"{dec_raw:+.4f}°" if dec_raw else "N/A")
            with col2:
                st.metric("Sector Range", f"{distance_ly:.2f} Light Years" if distance_ly else "N/A")
                st.markdown(f"""
                    <div style='padding: 10px; background-color: #1e293b; border-left: 4px solid #00e6ff; margin-top: 15px; font-family: monospace; border-radius: 4px;'>
                        <span style='color: #8a99ad;'>CONSTELLATION VECTOR SECTOR:</span><br>
                        <strong style='color: #e2e8f0; font-size: 16px;'>{constellation.upper()}</strong>
                    </div>
                """, unsafe_allow_html=True)

    if has_planets:
        semi_major_au = archive_data.get('pl_orbsmax')
        eccentricity = archive_data.get('pl_orbeccen', 0.0)
        eccentricity = float(eccentricity) if eccentricity is not None else 0.0
        r_star = archive_data.get('st_rad', 1.0)
        m_star = archive_data.get('st_mass', 1.0)
        teff = archive_data.get('st_teff', 5778.0)
        
        pl_eqt = archive_data.get('pl_eqt')
        pl_insol = archive_data.get('pl_insol')
        pl_bmasse = archive_data.get('pl_bmasse')
        st_met = archive_data.get('st_met')
        disc_method = archive_data.get('discoverymethod', 'N/A')
        disc_year = archive_data.get('disc_year', 'N/A')
        disc_fac = archive_data.get('disc_facility', 'N/A')
        
        lc_found = False
        periodogram = None
        folded_lc = None
        r_planet_earth = None
        transit_depth = 0.0
        
        if enable_lightkurve:
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
            except:
                pass

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

        if r_planet_earth is not None:
            if r_planet_earth < 1.2:
                classification, class_color = "Earth-sized Rocky Planet", "#10b981"
            elif r_planet_earth < 2.0:
                classification, class_color = "Super-Earth", "#3b82f6"
            elif r_planet_earth < 4.0:
                classification, class_color = "Sub-Neptune", "#f59e0b"
            else:
                classification, class_color = "Gas Giant", "#ef4444"
        else:
            classification, class_color = "Unknown Classification", "#64748b"

        if pl_eqt:
            if 180 <= pl_eqt <= 310:
                hab_status, hab_color = "TEMPERATE CLIMATE zone // LIQUID H2O POSSIBLE", "#10b981"
            elif pl_eqt < 180:
                hab_status, hab_color = "CRYOGENIC HAZARD // DEEP GLACIAL CRUST", "#3b82f6"
            else:
                hab_status, hab_color = "THERMAL FLUID HAZARD // ATMOSPHERIC SCORCHING", "#ef4444"
        else:
            hab_status, hab_color = "HABITABILITY SPECULATION UNKNOWN // MISSING EMISSION DATA", "#64748b"

        with tab2:
            st.markdown("<h4 style='color: #00e6ff; font-family: monospace; margin-top:15px;'>🌟 STELLAR GRAVITY CORE ARCHITECTURE</h4>", unsafe_allow_html=True)
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Confirmed Planets", f"{archive_data.get('sy_pnum', '1')}")
                c2.metric("Stellar Mass (M☉)", f"{m_star:.2f}" if m_star else "N/A")
                c3.metric("Stellar Radius (R☉)", f"{r_star:.2f}" if r_star else "N/A")
                c4.metric("Photosphere (K)", f"{int(teff):,}" if teff else "N/A")
                
                c5.markdown(f"""
                    <div style='text-align: center; padding: 2px; background-color: #1e293b; border: 1px dashed #00e6ff; border-radius: 4px;'>
                        <span style='font-size: 11px; color: #8a99ad; font-family: monospace;'>STAR TYPE</span><br>
                        <strong style='font-size: 15px; color: #00ffff; font-family: monospace;'>{st_spectype}</strong>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"<h4 style='color: #00e6ff; font-family: monospace; margin-top:20px;'>🪐 TARGET RADIAL RUNWAY: {archive_data.get('pl_name')}</h4>", unsafe_allow_html=True)
            with st.container(border=True):
                col_num, col_viz = st.columns([1, 1.2])
                with col_num:
                    st.metric("Semi-Major Vector Axis (a)", f"{semi_major_au:.4f} AU" if semi_major_au else "N/A")
                    st.metric("Semi-Minor Vector Axis (b)", f"{semi_minor_au:.4f} AU" if semi_minor_au else "N/A")
                    st.metric("Orbital Deviation (e)", f"{eccentricity:.4f}" if eccentricity else "0.0000")
                    if r_planet_earth is not None:
                        st.markdown(f"""
                            <div style='padding: 12px; background-color: #1e293b; border-left: 5px solid {class_color}; margin-top: 20px; font-family: monospace; border-radius: 4px;'>
                                <span style='color: #8a99ad;'>SCANNER MASS DIMENSION ANALYSIS:</span><br>
                                <strong style='color: {class_color}; font-size: 16px;'>{r_planet_earth:.2f} Earth Radii<br>{classification.upper()}</strong>
                            </div>
                        """, unsafe_allow_html=True)
                        
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
                        
                        ax_orb.plot(x_orbit_shifted, y_orbit, color='#38bdf8', linestyle='--', alpha=0.8, lw=1.5, label='Flight Vector Track')
                        ax_orb.scatter(0, 0, color='#f59e0b', s=180, edgecolors='#fff', linewidths=1.5, zorder=5, label='System Gravity Center')
                        ax_orb.scatter(semi_major_au - focal_shift, 0, color=class_color, s=90, zorder=5, label='Target Proximity Vector')
                        
                        ax_orb.set_xlabel('Distance Axis (AU)', color='#8a99ad', fontfamily='monospace', fontsize=9)
                        ax_orb.set_ylabel('Distance Axis (AU)', color='#8a99ad', fontfamily='monospace', fontsize=9)
                        ax_orb.grid(True, color='#334155', linestyle=':', alpha=0.5)
                        ax_orb.legend(loc='upper right', facecolor='#1e293b', edgecolor='#334155', fontsize=8)
                        ax_orb.set_aspect('equal', 'datalim')
                        st.pyplot(fig_orb)

        with tab3:
            st.markdown("<h4 style='color: #ef4444; font-family: monospace; margin-top:15px;'>☣️ BIOSPHERE HAZARD READOUT MATRIX</h4>", unsafe_allow_html=True)
            with st.container(border=True):
                hz1, hz2, hz3, hz4 = st.columns(4)
                hz1.metric("Core Equilibrium Heat", f"{int(pl_eqt)} K" if pl_eqt else "UNKNOWN")
                hz2.metric("Insolation Load (vs Earth)", f"{pl_insol:.2f}x" if pl_insol else "UNKNOWN")
                hz3.metric("Calculated Structural Mass", f"{pl_bmasse:.1f} M⊕" if pl_bmasse else "UNKNOWN")
                hz4.metric("Star Core Metallicity", f"{st_met:.2f} Fe/H" if st_met else "UNKNOWN")
                
                st.markdown(f"""
                    <div style='padding: 15px; background-color: #1e293b; border-left: 6px solid {hab_color}; margin-top: 20px; font-family: monospace; border-radius: 4px;'>
                        <span style='color: #8a99ad;'>COMPUTER HABITABILITY VECTOR PROTOCOL:</span><br>
                        <strong style='color: {hab_color}; font-size: 16px;'>{hab_status.upper()}</strong>
                    </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<h4 style='color: #00e6ff; font-family: monospace; margin-top:25px;'>📡 RECONNAISSANCE HISTORICAL PROTOCOLS</h4>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown(f"""
                * **Initial Sensor Method of Identification:** `{disc_method}`
                * **Earth Log Year Added to Archive:** `{disc_year}`
                * **Terrestrial Sensor Facility Location:** `{disc_fac}`
                """)

        with tab4:
            st.markdown("<h4 style='color: #00e6ff; font-family: monospace; margin-top:15px;'>📊 RAW BEAM OSCILLOSCOPE SIGNALS</h4>", unsafe_allow_html=True)
            if enable_lightkurve:
                if lc_found and periodogram is not None and folded_lc is not None:
                    plt.style.use('dark_background')
                    col_plot1, col_plot2 = st.columns(2)
                    with col_plot1:
                        with st.container(border=True):
                            fig1, ax1 = plt.subplots(figsize=(6, 3.5))
                            fig1.patch.set_facecolor('#0f172a')
                            ax1.set_facecolor('#0f172a')
                            periodogram.plot(ax=ax1, color='#00ffff', lw=1.5)
                            ax1.set_title("BLS Periodogram Spectrum Frequency Scan", color='#00e6ff', fontfamily='monospace', fontsize=11)
                            st.pyplot(fig1)
                    with col_plot2:
                        with st.container(border=True):
                            fig2, ax2 = plt.subplots(figsize=(6, 3.5))
                            fig2.patch.set_facecolor('#0f172a')
                            ax2.set_facecolor('#0f172a')
                            folded_lc.scatter(ax=ax2, color='#ff4500', alpha=0.4, s=3)
                            ax2.set_title("Folded Proximity Light Signal Curvature", color='#00e6ff', fontfamily='monospace', fontsize=11)
                            st.pyplot(fig2)
                else:
                    st.warning("📡 Solar light curve blocks are currently outside sensor link boundaries for this quadrant configuration.")
            else:
                st.info("💡 SHIP DATA LINK DEACTIVATED. Flip the 'DEPLOY DEEP SPACE LIGHT SIGNAL LINK' toggle switch on the left navigation panel to open high-frequency telescope streams.")

# --- 3. DYNAMIC HUD WARNING STATUS (STANDBY PULSE) ---
elif target:
    st.markdown(
        """
        <style>
        @keyframes pulse-warn {
            0% { opacity: 0.6; box-shadow: 0 0 5px rgba(56, 189, 248, 0.1); }
            50% { opacity: 1; box-shadow: 0 0 15px rgba(56, 189, 248, 0.3); }
            100% { opacity: 0.6; box-shadow: 0 0 5px rgba(56, 189, 248, 0.1); }
        }
        .hud-warning {
            padding: 20px;
            background: rgba(30, 41, 59, 0.4);
            border: 1px solid rgba(56, 189, 248, 0.4);
            border-left: 5px solid #38bdf8;
            font-family: monospace;
            border-radius: 6px;
            animation: pulse-warn 3s infinite ease-in-out;
            color: #38bdf8;
            text-align: center;
            letter-spacing: 1px;
            font-size: 14px;
        }
        </style>
        <div class="hud-warning">
            🛰️ BRIDGE SENSORS AT STANDBY // ENTER SYSTEM TARGET VECTOR CORRELATION & ENGAGE SWEEP
        </div>
        """,
        unsafe_allow_html=True
    )
