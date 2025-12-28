import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- KONFIGURACE STRÁNKY ---
st.set_page_config(page_title="EDM Genius Calculator Pro", page_icon="⚡", layout="wide")

# --- STYLOVÁNÍ ---
st.markdown("""
<style>
    .metric-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; }
    h1, h2, h3 { color: #0e1117; }
</style>
""", unsafe_allow_html=True)

# --- 1. BACKEND LOGIKA (Stejná jako minule) ---
VDI_DB = {
    "VDI 33 (Ra 4.5)": {"time_factor": 1.0, "gap": 0.12, "orbit": 0.25},
    "VDI 30 (Ra 3.2)": {"time_factor": 1.8, "gap": 0.09, "orbit": 0.20},
    "VDI 27 (Ra 2.2)": {"time_factor": 3.2, "gap": 0.07, "orbit": 0.15},
    "VDI 24 (Ra 1.6)": {"time_factor": 5.5, "gap": 0.05, "orbit": 0.12}, 
    "VDI 20 (Ra 1.0)": {"time_factor": 12.0, "gap": 0.03, "orbit": 0.08}
}

def calculate_edm(vol, area, vdi_target, difficulty, num_electrodes):
    mrr_base = 200 
    if difficulty > 1.3: mrr_base *= 0.7 
    t_rough = vol / mrr_base
    factor = VDI_DB[vdi_target]["time_factor"]
    t_finish = area * factor * difficulty
    t_aux = num_electrodes * 8 
    return t_rough, t_finish, t_aux

def calculate_electrode_cost(dim_x, dim_y, dim_z, graphite_price_dm3, cnc_rate, cnc_time_min, num_el):
    vol_dm3 = (dim_x * dim_y * dim_z) / 1_000_000
    material_cost_per_piece = vol_dm3 * graphite_price_dm3
    cnc_cost_per_piece = (cnc_time_min / 60) * cnc_rate
    total_cost = (material_cost_per_piece + cnc_cost_per_piece) * num_el
    return total_cost, material_cost_per_piece, cnc_cost_per_piece

# --- 2. UI - SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Konfigurace Sazeb")
    st.markdown("**EDM Stroj**")
    edm_rate = st.number_input("Sazba EDM (Kč/h)", value=1200)
    st.markdown("---")
    st.markdown("**Elektrody**")
    graphite_price = st.number_input("Cena Grafitu (Kč/dm³)", value=4500)
    cnc_rate = st.number_input("Sazba CNC (Kč/h)", value=1500)

# --- 3. UI - HLAVNÍ PANEL ---
st.title("⚡ EDM Time & Cost Calculator")
st.caption("Powered by Plotly™ Graphics")

# Vstupy
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("1️⃣ Geometrie")
    volume = st.number_input("Objem odebrání (mm³)", value=1000)
    area = st.number_input("Aktivní plocha (cm²)", value=10.0)
    depth = st.number_input("Hloubka (mm)", value=25.0)

with col2:
    st.subheader("2️⃣ Kvalita")
    target_vdi = st.selectbox("Drsnost", list(VDI_DB.keys()), index=3)
    num_el = st.radio("Elektrody", [1, 2, 3], index=1, horizontal=True)

with col3:
    st.subheader("3️⃣ Podmínky")
    difficulty = st.slider("Obtížnost výplachu", 1.0, 2.0, 1.2, 0.1)

st.markdown("---")

# Výpočet
t_rough, t_finish, t_aux = calculate_edm(volume, area, target_vdi, difficulty, num_el)
total_time_min = t_rough + t_finish + t_aux
total_time_hours = total_time_min / 60
edm_cost = total_time_hours * edm_rate

# --- ZÁLOŽKY ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard & Grafy", "💰 Náklady na elektrody", "🛠️ Technologie"])

# --- TAB 1: GRAFICKÝ DASHBOARD (PLOTLY) ---
with tab1:
    # Hlavní metriky
    m1, m2, m3 = st.columns(3)
    m1.metric("⏱️ Celkový čas", f"{total_time_hours:.1f} hod")
    m2.metric("💳 Cena EDM", f"{int(edm_cost)} Kč")
    m3.metric("🎯 Finiš fáze", f"{int(t_finish)} min")

    st.markdown("---")
    
    # Rozdělení na dva sloupce pro grafy
    g_col1, g_col2 = st.columns(2)
    
    with g_col1:
        st.markdown("#### ⏳ Rozpad času (Proces)")
        # Vytvoření dat pro Donut Chart
        labels = ['Hrubování', 'Dokončování (Finiš)', 'Vedlejší časy']
        values = [t_rough, t_finish, t_aux]
        colors = ['#636EFA', '#EF553B', '#00CC96'] # Moderní paleta Plotly
        
        fig_time = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4)])
        fig_time.update_traces(textinfo='percent+label', marker=dict(colors=colors))
        fig_time.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=300)
        st.plotly_chart(fig_time, use_container_width=True)
        
        st.caption(f"Dokončování zabírá {int(t_finish/total_time_min*100)}% celkového času.")

    with g_col2:
        st.markdown("#### 📉 Efektivita úběru")
        # Waterfall graf (nebo jednoduchý bar) pro ukázku vlivu obtížnosti
        fig_eff = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = difficulty,
            title = {'text': "Faktor náročnosti"},
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [1, 2], 'tickwidth': 1},
                'bar': {'color': "darkred"},
                'steps': [
                    {'range': [1, 1.3], 'color': "lightgreen"},
                    {'range': [1.3, 1.7], 'color': "yellow"},
                    {'range': [1.7, 2.0], 'color': "orange"}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': difficulty}}))
        fig_eff.update_layout(height=300, margin=dict(t=40, b=0))
        st.plotly_chart(fig_eff, use_container_width=True)

# --- TAB 2: NÁKLADY ELEKTROD ---
with tab2:
    ce1, ce2 = st.columns([1, 2])
    with ce1:
        st.markdown("**Rozměry polotovaru (mm)**")
        el_x = st.number_input("Šířka (X)", value=50)
        el_y = st.number_input("Délka (Y)", value=50)
        el_z = st.number_input("Výška (Z)", value=80)
        cnc_time = st.number_input("CNC čas (min/ks)", value=45)
        
    total_el_cost, mat_cost, cnc_cost = calculate_electrode_cost(
        el_x, el_y, el_z, graphite_price, cnc_rate, cnc_time, num_el
    )
    project_total = edm_cost + total_el_cost
    
    with ce2:
        st.markdown("#### 💰 Struktura nákladů zakázky")
        # Stacked Bar Chart pro náklady
        df_cost = pd.DataFrame({
            "Kategorie": ["EDM Stroj", "CNC Práce", "Materiál Grafit"],
            "Cena": [edm_cost, cnc_cost * num_el, mat_cost * num_el],
            "Barva": ["Strojní čas", "Příprava", "Příprava"]
        })
        
        fig_cost = px.bar(
            df_cost, 
            x="Cena", 
            y="Kategorie", 
            orientation='h', 
            text="Cena",
            color="Kategorie",
            title=f"Celkem: {int(project_total)} Kč"
        )
        fig_cost.update_traces(texttemplate='%{text:.0f} Kč', textposition='inside')
        fig_cost.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig_cost, use_container_width=True)

# --- TAB 3: TECHNOLOGIE ---
with tab3:
    st.markdown("#### Parametry pro Zimmer & Kreim Genius")
    tech_data = VDI_DB[target_vdi]
    undersize_finish = tech_data["gap"] + tech_data["orbit"]
    
    # Vytvoření pěkné HTML tabulky místo standardní
    st.markdown(f"""
    <table style="width:100%; text-align: left; border-collapse: collapse;">
      <tr style="background-color: #f2f2f2; border-bottom: 2px solid #ddd;">
        <th style="padding: 10px;">Parametr</th>
        <th style="padding: 10px;">Hrubování (E1)</th>
        <th style="padding: 10px; color: #d63031;">Dokončování (E{num_el})</th>
      </tr>
      <tr style="border-bottom: 1px solid #ddd;">
        <td style="padding: 10px;"><b>Jiskrová mezera</b></td>
        <td style="padding: 10px;">~ 0.15 mm</td>
        <td style="padding: 10px;">{tech_data['gap']} mm</td>
      </tr>
      <tr style="border-bottom: 1px solid #ddd;">
        <td style="padding: 10px;"><b>Orbita (R)</b></td>
        <td style="padding: 10px;">0.0 - 0.2 mm</td>
        <td style="padding: 10px;">{tech_data['orbit']} mm</td>
      </tr>
      <tr style="background-color: #e8fdf5; border-bottom: 2px solid #00cc66;">
        <td style="padding: 10px;"><b>PODBROUŠENÍ</b></td>
        <td style="padding: 10px;"><b>{(undersize_finish + 0.3):.2f} mm</b></td>
        <td style="padding: 10px; color: #d63031;"><b>{undersize_finish:.2f} mm</b></td>
      </tr>
    </table>

    """, unsafe_allow_html=True)
