import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
import os
import google.generativeai as genai

# 1. Inicializar Firebase una sola vez por proceso (evita doble init en reruns)
@st.cache_resource
def inicializar_firebase():
    if not firebase_admin._apps:
        # MODO NUBE: Si encuentra los secrets de Streamlit Cloud
        if "firebase_creds" in st.secrets:
            firebase_creds = dict(st.secrets["firebase_creds"])
            if "private_key" in firebase_creds:
                firebase_creds["private_key"] = firebase_creds["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(firebase_creds)

        # MODO LOCAL: Si estás en tu PC, usa el archivo JSON físico
        elif os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")

        else:
            st.error("No se encontraron credenciales de Firebase (ni en Secrets ni el archivo JSON local).")
            st.stop()

        try:
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://estacion-metereologica-d7c0d-default-rtdb.firebaseio.com'
            })
        except ValueError:
            # Ya existe (carrera entre reruns) — no es un error real, continuamos
            pass
    return True

inicializar_firebase()


st.set_page_config(
    page_title="BIU Monitoreo - ESP32 | BMP280",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600;700&display=swap');

    .stApp {
        background-image: url('https://images.unsplash.com/photo-1501630834273-4b5604d2ee31?w=1920&q=80');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    .stApp::before {
        content: '';
        position: fixed;
        inset: 0;
        background: rgba(240, 247, 255, 0.82);
        z-index: 0;
    }
    .stApp > * { position: relative; z-index: 1; }

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        color: #1a2b4a;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.88);
        border: 1px solid rgba(100, 160, 230, 0.35);
        border-radius: 14px;
        padding: 20px 16px;
        text-align: center;
        backdrop-filter: blur(8px);
        box-shadow: 0 2px 12px rgba(30, 90, 180, 0.10);
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    .metric-card:hover {
        border-color: #3a8fd8;
        box-shadow: 0 4px 20px rgba(30, 90, 180, 0.18);
    }
    .metric-value {
        font-family: 'Space Mono', monospace;
        font-size: 2rem;
        font-weight: 700;
        color: #1455a4;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 0.75rem;
        color: #5a7a9e;
        letter-spacing: 0.10em;
        text-transform: uppercase;
        margin-top: 5px;
        font-weight: 600;
    }
    .metric-unit {
        font-size: 0.88rem;
        color: #5a7a9e;
        font-family: 'Space Mono', monospace;
    }
    .section-title {
        font-family: 'Space Mono', monospace;
        font-size: 0.82rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #1455a4;
        border-left: 4px solid #3a8fd8;
        padding-left: 12px;
        margin: 28px 0 16px 0;
        font-weight: 700;
    }
    .header-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 24px;
        border-radius: 16px;
        background: linear-gradient(135deg, #0d2b5e 0%, #1455a4 60%, #1a6bbf 100%);
        border: 1px solid rgba(255,255,255,0.15);
        box-shadow: 0 4px 20px rgba(13,43,94,0.45);
        margin-bottom: 24px;
    }
    .header-title {
        font-family: 'Space Mono', monospace;
        font-size: 1.35rem;
        font-weight: 700;
        color: #ffffff;
        text-shadow: 0 1px 4px rgba(0,0,0,0.3);
    }
    .header-sub {
        font-size: 0.80rem;
        color: #a8c8f0;
        margin-top: 3px;
        font-weight: 400;
    }
    .last-update {
        font-family: 'Space Mono', monospace;
        font-size: 0.70rem;
        color: #a8c8f0;
        text-align: right;
        line-height: 1.6;
    }
    .status-dot {
        display: inline-block;
        width: 8px; height: 8px;
        background: #22c55e;
        border-radius: 50%;
        margin-right: 5px;
        animation: pulse 2s infinite;
    }
    @keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.35;} }
    .chart-container {
        background: rgba(255,255,255,0.88);
        border-radius: 14px;
        border: 1px solid rgba(100,160,230,0.25);
        padding: 8px;
        backdrop-filter: blur(8px);
        box-shadow: 0 2px 12px rgba(30,90,180,0.08);
    }
    div[data-testid="stSelectbox"] label,
    div[data-testid="stSlider"] label {
        color: #1a2b4a !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
    }
    div[data-testid="stSelectbox"] > div > div {
        background-color: rgba(255,255,255,0.95) !important;
        border-color: #a8c8e8 !important;
        color: #1a2b4a !important;
        border-radius: 8px !important;
    }
    div[data-testid="stMultiSelect"] > div > div {
        background-color: rgba(255,255,255,0.95) !important;
        border-color: #a8c8e8 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stTextInput"] > div > div > input {
        background-color: rgba(255,255,255,0.95) !important;
        border-color: #a8c8e8 !important;
        color: #1a2b4a !important;
        border-radius: 8px !important;
    }
    .stButton > button {
        background: #1455a4 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover { background: #0e3d7a !important; }
    details { background: rgba(255,255,255,0.88) !important; border-radius: 12px !important; border: 1px solid rgba(100,160,230,0.25) !important; }
    summary { color: #1455a4 !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)


# ── Firebase ──────────────────────────────────────────────────────────────────
@st.cache_resource
def init_firebase_ref():
    # La app ya fue inicializada arriba, solo retornamos la referencia
    return db.reference("lecturas")

def cargar_datos():
    ref = init_firebase_ref()
    data = ref.order_by_key().limit_to_last(35000).get()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(list(data.values()))

    # Excluir registros sin campo 'fecha' (ej. pruebas iniciales del ESP32)
    df = df[df["fecha"].notna()].copy()

    df["fecha"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    df = df[df["fecha"].notna()]  # también descarta fechas con formato inválido
    df = df.sort_values("fecha").reset_index(drop=True)
    df["fecha_label"] = df["fecha"].dt.strftime("%d/%m %H:%M")
    for col in ["temperatura", "presion", "altitud", "wifi"]:
        if col not in df.columns:
            df[col] = None
    return df


# ── Paleta ────────────────────────────────────────────────────────────────────
# Histórico: solo temperatura y presión (altitud excluida por ser valor calculado)
COLORES  = {"temperatura": "#e05a2b", "presion": "#1455a4"}
UNIDADES = {"temperatura": "°C",      "presion": "hPa",    "altitud": "m.s.n.m."}
ICONOS   = {"temperatura": "🌡️",      "presion": "🔵",     "altitud": "⛰️"}

PLOT_BG  = "rgba(250,253,255,0.95)"
GRID_COL = "#d0e4f4"
TICK_COL = "#a0b8d0"
FONT_COL = "#1a2b4a"


# ── IA — Gemini con contexto de datos reales ─────────────────────────────────
@st.cache_resource
def init_gemini():
    genai.configure(api_key=st.secrets["gemini"]["api_key"])
    return genai.GenerativeModel("gemini-2.5-flash-lite")


def construir_contexto(df, n=100):
    """Construye un resumen compacto: estadísticas diarias de TODO el historial
    + detalle de los últimos N registros para preguntas de corto plazo."""

    # ── Rango completo disponible en Firebase ──
    fecha_inicio = df['fecha'].min()
    fecha_fin    = df['fecha'].max()
    total_dias   = (fecha_fin - fecha_inicio).days

    # ── Estadísticas agregadas POR DÍA (todo el historial, sin gastar tokens en cada registro) ──
    df_diario = df.copy()
    df_diario["dia"] = df_diario["fecha"].dt.strftime("%Y-%m-%d (%A)")
    resumen_diario = df_diario.groupby("dia").agg(
        temp_min=("temperatura", "min"),
        temp_max=("temperatura", "max"),
        temp_prom=("temperatura", "mean"),
        presion_min=("presion", "min"),
        presion_max=("presion", "max"),
        presion_prom=("presion", "mean"),
        registros=("temperatura", "count"),
    ).round(2)

    tabla_diaria = "\n".join(
        f"  {dia}: Temp [{r.temp_min}–{r.temp_max}, prom {r.temp_prom}°C] · "
        f"Presión [{r.presion_min}–{r.presion_max}, prom {r.presion_prom} hPa] · "
        f"({int(r.registros)} lecturas)"
        for dia, r in resumen_diario.iterrows()
    )

    # ── Detalle de los últimos N registros (para preguntas de "ahora" o "reciente") ──
    df_ctx = df.tail(n).copy()

    resumen = f"""
Datos de la estación meteorológica BIU (Bogotá, Colombia).

RANGO TOTAL DISPONIBLE: desde {fecha_inicio} hasta {fecha_fin} ({total_dias} días, {len(df)} registros totales).

RESUMEN POR DÍA (todo el historial):
{tabla_diaria}

LECTURA MÁS RECIENTE (últimos {len(df_ctx)} registros, {df_ctx['fecha'].min()} a {df_ctx['fecha'].max()}):
  Temperatura actual: {df_ctx['temperatura'].iloc[-1]:.2f} °C (mín {df_ctx['temperatura'].min():.2f}, máx {df_ctx['temperatura'].max():.2f}, prom {df_ctx['temperatura'].mean():.2f})
  Presión actual: {df_ctx['presion'].iloc[-1]:.2f} hPa (mín {df_ctx['presion'].min():.2f}, máx {df_ctx['presion'].max():.2f}, prom {df_ctx['presion'].mean():.2f})
  Altitud actual: {df_ctx['altitud'].iloc[-1]:.1f} m (prom {df_ctx['altitud'].mean():.1f})
  WiFi RSSI actual: {df_ctx['wifi'].iloc[-1]} dBm (mín {df_ctx['wifi'].min()}, máx {df_ctx['wifi'].max()})
"""
    return resumen


def preguntar_ia(pregunta, contexto):
    """Envía la pregunta + contexto a Gemini y retorna la respuesta."""
    model = init_gemini()
    prompt = f"""Eres un asistente experto en meteorología y análisis de datos IoT.
Responde la pregunta del usuario basándote ÚNICAMENTE en los datos proporcionados.
Sé breve, concreto y usa unidades correctas. Si la pregunta no se puede responder
con estos datos, dilo claramente.

DATOS DISPONIBLES:
{contexto}

PREGUNTA DEL USUARIO: {pregunta}

RESPUESTA:"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Error al consultar la IA: {e}"


def main():
    try:
        df = cargar_datos()
    except Exception as e:
        st.error(f"⚠️ Error conectando a Firebase: {e}")
        st.stop()

    if df.empty:
        st.warning("No hay datos en Firebase todavía.")
        st.stop()

    ultima = df.iloc[-1]
    ahora  = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="header-bar">
        <div>
            <div class="header-title">📡 BIU · ESP32 BMP280 Monitor</div>
            <div class="header-sub">Estación meteorológica · Bogotá, Colombia</div>
        </div>
        <div class="last-update">
            <span class="status-dot"></span><b style="color:#86efac;">En línea</b><br>
            Actualizado: {ahora}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tarjetas — lectura más reciente (incluye altitud) ─────────────────────
    st.markdown('<div class="section-title">⚡ Lectura más reciente</div>', unsafe_allow_html=True)

    temp_val       = ultima["temperatura"] if pd.notnull(ultima["temperatura"]) else 0
    pres_val       = ultima["presion"]     if pd.notnull(ultima["presion"])     else 0
    alt_val        = ultima["altitud"]     if pd.notnull(ultima["altitud"])     else 0
    wifi_val       = int(ultima["wifi"])   if pd.notnull(ultima["wifi"])        else 0
    fecha_firebase = ultima["fecha"].strftime("%d/%m/%Y %H:%M:%S") if pd.notnull(ultima["fecha"]) else "—"

    c1, c2, c3, c4, c5 = st.columns(5)
    tarjetas = [
        (c1, "🌡️ Temperatura",    f"{temp_val:.2f}",  "°C",      "2rem"),
        (c2, "🔵 Presión",        f"{pres_val:.2f}",  "hPa",     "2rem"),
        (c3, "⛰️ Altitud",        f"{alt_val:.1f}",   "m",       "2rem"),
        (c4, "📶 WiFi RSSI",      f"{wifi_val}",       "dBm",     "2rem"),
        (c5, "📅 Última lectura", fecha_firebase,      "",        "1.05rem"),
    ]
    for col, nombre, valor, unidad, size in tarjetas:
        col.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="font-size:{size};">{valor}
                <span class="metric-unit">{unidad}</span>
            </div>
            <div class="metric-label">{nombre}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Gráfico histórico — solo temperatura y presión ────────────────────────
    st.markdown('<div class="section-title">📈 Histórico de variables</div>', unsafe_allow_html=True)

    col_sel, col_rango = st.columns([2, 3])
    with col_sel:
        variables_sel = st.multiselect(
            "Variables a mostrar",
            options=["temperatura", "presion"],
            default=["temperatura", "presion"],
        )
    with col_rango:
        n_registros = st.slider("Últimos N registros", 10, len(df), min(200, len(df)), step=10)

    df_filtrado = df.tail(n_registros).dropna(subset=["fecha"])

    if variables_sel:
        fig_hist = go.Figure()
        for var in variables_sel:
            fig_hist.add_trace(go.Scatter(
                x=df_filtrado["fecha_label"], y=df_filtrado[var], mode="lines",
                name=f"{ICONOS[var]} {var.capitalize()} ({UNIDADES[var]})",
                line=dict(color=COLORES[var], width=2.5),
                hovertemplate=f"<b>{var}</b>: %{{y:.2f}} {UNIDADES[var]}<br>%{{x}}<extra></extra>"
            ))
        fig_hist.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=PLOT_BG,
            font=dict(color=FONT_COL, family="DM Sans"),
            legend=dict(bgcolor="rgba(255,255,255,0.8)", font=dict(color=FONT_COL),
                        bordercolor="#d0e4f4", borderwidth=1),
            xaxis=dict(gridcolor=GRID_COL, tickcolor=TICK_COL, linecolor=TICK_COL,
                       tickfont=dict(color=FONT_COL, size=11)),
            yaxis=dict(gridcolor=GRID_COL, tickcolor=TICK_COL, linecolor=TICK_COL,
                       tickfont=dict(color=FONT_COL, size=11)),
            margin=dict(l=10, r=10, t=16, b=10), height=380, hovermode="x unified",
        )
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(fig_hist, width='stretch')
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Selecciona al menos una variable.")

    # ── WiFi Gauge ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">📶 Señal WiFi (RSSI)</div>', unsafe_allow_html=True)

    col_gauge, col_wifi_info = st.columns([1, 2])
    with col_gauge:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=wifi_val,
            number={"suffix": " dBm", "font": {"color": "#1455a4", "family": "Space Mono", "size": 32}},
            gauge={
                "axis": {"range": [-100, 0], "tickcolor": TICK_COL,
                         "tickvals": [-100, -80, -70, -60, -50, -30, 0],
                         "tickfont": {"color": FONT_COL, "size": 10}},
                "bar": {"color": "#1455a4", "thickness": 0.25},
                "bgcolor": "rgba(240,247,255,0.9)",
                "borderwidth": 1, "bordercolor": "#d0e4f4",
                "steps": [
                    {"range": [-100, -80], "color": "#fde8e8"},
                    {"range": [-80,  -70], "color": "#fef3cd"},
                    {"range": [-70,  -60], "color": "#d4edda"},
                    {"range": [-60,    0], "color": "#cce5ff"},
                ],
            },
            title={"text": "Intensidad de señal", "font": {"color": FONT_COL, "size": 13}}
        ))
        fig_gauge.update_layout(
            paper_bgcolor="rgba(255,255,255,0.88)",
            height=260, margin=dict(l=20, r=20, t=40, b=10)
        )
        st.plotly_chart(fig_gauge, width='stretch')

    with col_wifi_info:
        if wifi_val >= -60:
            nivel, color, desc = "Excelente 🟢", "#166534", "Señal óptima, sin pérdida de paquetes"
        elif wifi_val >= -70:
            nivel, color, desc = "Buena 🟡",     "#854d0e", "Señal aceptable para IoT"
        elif wifi_val >= -80:
            nivel, color, desc = "Regular 🟠",   "#9a3412", "Puede haber intermitencias"
        else:
            nivel, color, desc = "Débil 🔴",     "#7f1d1d", "Riesgo de desconexión"
        st.markdown(f"""
        <div class="metric-card" style="margin-top:30px; text-align:left; padding:24px 28px;">
            <div style="font-family:'Space Mono',monospace; font-size:1.4rem; font-weight:700; color:{color};">{nivel}</div>
            <div style="font-size:0.85rem; color:#5a7a9e; margin-top:10px;">{desc}</div>
            <div style="font-size:0.82rem; color:#1a2b4a; margin-top:14px; font-weight:600;">
                Valor actual: <b>{wifi_val} dBm</b>
            </div>
            <div style="font-size:0.78rem; color:#5a7a9e; margin-top:4px;">
                Rango ideal ESP32: -30 a -60 dBm
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Tabla de datos ────────────────────────────────────────────────────────
    with st.expander("🗃️ Ver tabla de datos completa"):
        df_show = df[["fecha", "temperatura", "presion", "altitud", "wifi"]].tail(100).copy()
        df_show["fecha"] = df_show["fecha"].dt.strftime("%d/%m/%Y %H:%M:%S")
        st.dataframe(df_show, width='stretch', height=300)
        st.caption(f"Mostrando últimos 100 de {len(df)} registros totales.")

    # ── Chat con IA — Gemini con contexto de datos reales ─────────────────────
    st.markdown('<div class="section-title">🤖 Pregúntale a la IA sobre tus datos</div>', unsafe_allow_html=True)

    if "historial_chat" not in st.session_state:
        st.session_state.historial_chat = []

    col_chat, col_ejemplos = st.columns([3, 1])

    with col_ejemplos:
        st.caption("💡 Ejemplos de preguntas:")
        st.caption("• ¿Cuál fue la temperatura máxima?")
        st.caption("• ¿La presión está subiendo o bajando?")
        st.caption("• ¿La señal WiFi es estable?")

    with col_chat:
        pregunta_usuario = st.text_input(
            "Escribe tu pregunta sobre los datos meteorológicos:",
            placeholder="Ej: ¿Cuál ha sido la tendencia de temperatura?",
            key="input_pregunta"
        )

        if st.button("Preguntar 🔍") and pregunta_usuario:
            contexto = construir_contexto(df, n=100)
            with st.spinner("Consultando IA..."):
                respuesta = preguntar_ia(pregunta_usuario, contexto)
            st.session_state.historial_chat.append((pregunta_usuario, respuesta))

        # Mostrar historial de la sesión actual (más reciente primero)
        for pregunta, respuesta in reversed(st.session_state.historial_chat):
            st.markdown(f"""
            <div class="metric-card" style="text-align:left; margin-top:12px; padding:16px 20px;">
                <div style="font-weight:700; color:#1455a4; margin-bottom:6px;">🙋 {pregunta}</div>
                <div style="color:#1a2b4a; font-size:0.92rem; line-height:1.5;">🤖 {respuesta}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Auto-refresh ──────────────────────────────────────────────────────────
    st.markdown("---")
    col_r1, col_r2 = st.columns([3, 1])
    with col_r1:
        st.caption("🔄 La página se actualiza automáticamente cada 30 segundos.")
    with col_r2:
        if st.button("🔄 Actualizar ahora"):
            st.rerun()

    time.sleep(30)
    st.rerun()


if __name__ == "__main__":
    main()