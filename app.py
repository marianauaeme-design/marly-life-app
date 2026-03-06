import streamlit as st
import pandas as pd
from datetime import datetime
import time
import plotly.graph_objects as go
import random
import string
import gspread
from google.oauth2.service_account import Credentials

# --- FUNCIÓN DE CONEXIÓN (Añádela aquí) ---
def conectar_google():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        # Usamos st.secrets para mayor seguridad
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        # Asegúrate de que el nombre coincida con tu Excel
        return client.open("MiExcelPlanSemanal").sheet1
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# --- 0. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Plan Semanal", layout="wide")

# --- PALETA DE COLORES PERSONALIZADA ---
SKY_BLUE = "#8ecae6"
BLUE_GREEN = "#219ebc"
DEEP_SPACE = "#023047"
AMBER = "#ffb703"
ORANGE = "#fb8500"

# --- ESTILOS MEJORADOS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #fcfcfc; }}
    
    /* --- AJUSTES "FAT-FINGER" (BOTONES Y CHECKBOXES MÁS GRANDES) --- */
    .stCheckbox {{
        padding: 12px 5px !important;
        background-color: #f9f9f9;
        border-radius: 8px;
        margin-bottom: 5px;
    }}
    .stButton>button {{ 
        height: 48px !important;
        font-size: 1rem !important;
        border-radius: 10px !important;
    }}

    /* --- CARPETAS NARANJA (FORZADO) --- */
    div[data-testid="stExpander"] {{
        border: 2px solid {ORANGE} !important;
        border-radius: 12px !important;
        background-color: white !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
        margin-bottom: 12px !important;
    }}

    div[data-testid="stExpander"] summary p {{
        color: {DEEP_SPACE} !important;
        font-weight: bold !important;
        font-size: 1rem !important;
    }}

    div[data-testid="stExpander"] svg {{
        fill: {ORANGE} !important;
    }}

    /* --- ESTILO WRAPPED MEJORADO (NARANJA) --- */
    .wrapped-card {{
        background-color: {ORANGE} !important;
        padding: 20px;
        border-radius: 15px;
        color: white !important;
        margin: 10px 0;
        text-align: center;
    }}
    .wrapped-card h2 {{ color: white !important; }}
    .stat-highlight {{ font-size: 2.5rem !important; font-weight: 800; color: {DEEP_SPACE}; }}

    /* --- OBJETIVO O META EN ROJO --- */
    .area-goal {{
        color: #FF0000 !important;
        font-size: 0.85rem !important;
        font-weight: 800 !important;
        font-style: italic !important;
        display: block !important;
        margin: 5px 0 10px 0 !important;
    }}

    /* --- NUEVO: ETIQUETA DE TAREA --- */
    .task-label {{
        color: {DEEP_SPACE} !important;
        font-size: 1.0rem !important;
        font-weight: 800 !important;
        font-style: italic !important;
        display: block !important; /* IMPORTANTE */
        margin-top: 10px !important;
        margin-bottom: 2px !important;
    }}

    .area-separator-line {{
        height: 3px;
        background-color: #219ebc;
        border-radius: 4px;
        margin: 6px 0 8px 0;
    }}

    /* --- OPTIMIZACIÓN MÓVIL (COLUMNAS INTELIGENTES Y SCROLL) --- */
    h1 {{ font-size: 1.6rem !important; }}
    h3 {{ font-size: 1.1rem !important; }}
    h4 {{ font-size: 0.9rem !important; }}
    
    @media (max-width: 640px) {{
        [data-testid="column"] {{
            width: 100% !important;
            flex: 1 1 100% !important;
            margin-bottom: 1.5rem !important;
        }}
        .stButton>button {{
            padding: 10px 5px !important;
            font-size: 0.9rem !important;
        }}
        .area-header {{
            font-size: 0.65rem !important;
        }}
        h3 {{
            font-size: 1.2rem !important;
            margin-top: 20px !important;
        }}
        div[data-testid="stExpander"] {{
            margin-left: 5px !important;
            margin-right: 5px !important;
        }}
        .wrapped-card h2 {{ font-size: 1.3rem !important; }}
        input {{ font-size: 16px !important; }} 
    }}

    /* SCROLL LATERAL PARA CONTENEDORES ANCHOS EN PC */
    .stHorizontalBlock {{
        overflow-x: auto !important;
        display: flex;
    }}

    .stTextInput>div>div>input, .stSelectbox>div>div>div {{
        border: 2px solid {ORANGE} !important;
        border-radius: 8px !important;
    }}
    .stButton>button {{ 
        background-color: {ORANGE} !important; 
        color: white !important; 
        font-weight: bold !important;
    }}
    
    .marly-puntos-badge {{
        background-color: {DEEP_SPACE};
        color: {AMBER};
        padding: 8px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE AUTENTICACIÓN (LECTURA AUTOMÁTICA DE EXCEL) ---
if 'db_usuarios' not in st.session_state:
    # 1. Primero agregamos tus accesos fijos (los que no están en el Excel)
    st.session_state.db_usuarios = {
        "ADMIN123": ["Marianita", "2026"]
    }
    
    # 2. Ahora leemos a todos los clientes que están guardados en el Excel
    hoja = conectar_google()
    if hoja:
        try:
            # Traemos todas las filas del Excel
            lista_usuarios = hoja.get_all_records() 
            for fila in lista_usuarios:
                t = str(fila['Token'])
                n = str(fila['Nombre'])
                # Si en el Excel ya hay un PIN, lo trae; si no, pone None
                p = str(fila['PIN']) if fila.get('PIN') else None
                
                # Los agregamos a la memoria de la app
                st.session_state.db_usuarios[t] = [n, p]
        except Exception as e:
            st.error(f"Error al sincronizar con la nube: {e}")

if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'user_key' not in st.session_state: st.session_state.user_key = None

# --- PANTALLA DE ACCESO (ESTILO TARJETA DIFERENCIADA) ---
if not st.session_state.autenticado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col_center, _ = st.columns([0.1, 1, 0.1]) 
    
    with col_center:
        # Título con el Azul Espacial que usamos para los días
        st.markdown(f"""
            <div style="padding: 10px; background-color: #f1f1f1; border-radius: 15px 15px 0 0; border: 2px solid {ORANGE}; border-bottom: none; text-align: center;">
                <span style="color: {DEEP_SPACE}; font-size: 1.8rem; font-weight: 800; font-style: italic; text-transform: uppercase;">
                    Bienvenida
                </span>
            </div>
            <div style="background-color: white; padding: 25px; border-radius: 0 0 15px 15px; border: 2px solid {ORANGE}; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                <p style='color: #FF0000; font-weight: 800; font-style: italic; margin-bottom: 20px;'>
                    Introduce tu Token o PIN para gestionar tu éxito
                </p>
        """, unsafe_allow_html=True)
        
      # El input y el botón
        entrada = st.text_input("Acceso:", type="password", placeholder="Llave de acceso...", label_visibility="collapsed")
        
        st.markdown('<div style="margin-top: 15px;">', unsafe_allow_html=True)
        if st.button("INGRESAR SISTEMA", width="stretch"):
            for token, datos in st.session_state.db_usuarios.items():
                if entrada == token or (datos[1] and entrada == datos[1]):
                    st.session_state.autenticado = True
                    st.session_state.user_key = token
                    st.session_state.nombre_usuario = datos[0]
                    st.rerun()
            st.error("Llave incorrecta")
        st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop()

col_vacia, col_pin, col_vacia2 = st.columns([1, 2, 1])


# --- CONFIGURACIÓN DE PIN INICIAL (DISEÑO PREMIUM + GUARDADO EN EXCEL) ---
if st.session_state.autenticado:
    user_info = st.session_state.db_usuarios.get(st.session_state.user_key)
    
    # Verificamos si no tiene PIN configurado
    if user_info and (len(user_info) < 2 or user_info[1] is None):
        st.markdown("<br>", unsafe_allow_html=True)
        _, col_pin, _ = st.columns([1, 1.5, 1]) 
        
        with col_pin:
            # Tu diseño elegante de la tarjeta blanca
            st.markdown(f"""
                <div style="background-color: white; padding: 25px; border-radius: 15px; 
                            box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-left: 5px solid {ORANGE};">
                    <h3 style='margin-top:0;'>Configura tu PIN</h3>
                    <p style='color:gray; font-size:0.9rem;'>Hola <b>{st.session_state.nombre_usuario}</b>, crea un código de 4 números para entrar más rápido.</p>
                </div>
            """, unsafe_allow_html=True)
            
            with st.container():
                st.markdown('<div style="margin-top: 10px;">', unsafe_allow_html=True)
                # Importante: añadimos 'key' para evitar conflictos de Streamlit
                nuevo_pin = st.text_input("PIN de 4 dígitos:", max_chars=4, type="password", key="setup_pin_final")
                
                st.markdown('<div class="btn-naranja">', unsafe_allow_html=True)
                if st.button("GUARDAR PIN Y ACTIVAR", width="stretch"):
                    if len(nuevo_pin) == 4 and nuevo_pin.isdigit():
                        # --- PROCESO DE GUARDADO EN GOOGLE SHEETS ---
                        hoja = conectar_google()
                        if hoja:
                            try:
                                # Busca la fila del usuario por su Token
                                celda = hoja.find(st.session_state.user_key)
                                # Actualiza la columna 3 (C) con el nuevo PIN
                                hoja.update_cell(celda.row, 3, nuevo_pin)
                                
                                # También actualizamos la memoria local para esta sesión
                                st.session_state.db_usuarios[st.session_state.user_key][1] = nuevo_pin
                                
                                st.success("¡PIN guardado en la nube correctamente!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al conectar con el Excel: {e}")
                        else:
                            st.error("Error: No se pudo conectar con Google Sheets.")
                    else:
                        st.warning("El PIN debe ser de exactamente 4 números.")
                st.markdown('</div></div>', unsafe_allow_html=True)
        st.stop()

# --- INICIALIZACION DE DATOS ---
dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

if 'puntos' not in st.session_state: st.session_state.puntos = 0
if 'nombre_usuario' not in st.session_state: 
    st.session_state.nombre_usuario = st.session_state.db_usuarios[st.session_state.user_key][0]
if 'historial' not in st.session_state: 
    st.session_state.historial = pd.DataFrame(columns=["Fecha", "Día", "Área", "Tarea", "Logro"])
if 'tienda' not in st.session_state: st.session_state.tienda = {"Café Especial": 200, "SkinCare Nuevo": 500}
if 'recordatorios' not in st.session_state: st.session_state.recordatorios = ["Beber 2L de agua", "Postura recta al trabajar"]
if 'areas' not in st.session_state:
    st.session_state.areas = {
        "Espiritu": [[{"nombre": "Lectura Biblia", "dias": dias_semana}], "Crecer en fe"],
        "Mente": [[{"nombre": "Inglés", "dias": dias_semana}, {"nombre": "Italiano", "dias": dias_semana}], "Fluidez 2026"],
        "Cuerpo": [[{"nombre": "Ejercicio", "dias": ["Lunes", "Miércoles", "Viernes"]}, {"nombre": "SkinCare", "dias": dias_semana}], "Salud óptima"]
    }
if 'version_tablero' not in st.session_state: st.session_state.version_tablero = 0

# --- SIDEBAR ---
with st.sidebar:
    st.header("Perfil")
    nuevo_nom = st.text_input("Tu Nombre", value=st.session_state.nombre_usuario)
    if nuevo_nom != st.session_state.nombre_usuario:
        st.session_state.nombre_usuario = nuevo_nom
        st.session_state.db_usuarios[st.session_state.user_key][0] = nuevo_nom
    
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()
    
    with st.expander("Seguridad: Cambiar mi PIN"):
        pin_upd = st.text_input("PIN Nuevo (4 dígitos)", max_chars=4, type="password", key="ch_pin")
        if st.button("Actualizar PIN"):
            if len(pin_upd) == 4 and pin_upd.isdigit():
                st.session_state.db_usuarios[st.session_state.user_key][1] = pin_upd
                st.success("PIN actualizado")
                time.sleep(1); st.rerun()
            else: st.error("Usa 4 números.")
        
    st.divider()

   # --- PANEL DE ADMINISTRACIÓN (DENTRO DEL SIDEBAR) ---
    if st.session_state.user_key == "ADMIN123":
        # Usamos el ícono de carpeta 📁 como pediste
        with st.expander("📁 PANEL DE VENTAS"):
            st.write("Generar acceso para nuevos clientes:")
            nom_cli = st.text_input("Nombre del Cliente", placeholder="Ej: Juan Pérez", key="nom_admin_key")
            
            # El botón que genera el token y lo guarda
            if st.button("GENERAR Y GUARDAR TOKEN", width="stretch"):
                if nom_cli:
                    # Generación del token con el prefijo MAR-
                    nuevo_tok = "MAR-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                    
                    # 1. Guardar en memoria local (Streamlit)
                    st.session_state.db_usuarios[nuevo_tok] = [nom_cli, None]
                    
                    # 2. Guardar en Google Sheets (La nube)
                    hoja = conectar_google()
                    if hoja:
                        try:
                            # Se agrega una fila con: Nombre, Token y espacio para el PIN
                            hoja.append_row([nom_cli, nuevo_tok, ""]) 
                            st.success(f"¡Éxito! Token para {nom_cli} guardado.")
                            st.code(nuevo_tok, language="text")
                        except Exception as e:
                            st.error(f"Error al subir a la nube: {e}")
                else:
                    st.warning("Por favor, escribe el nombre del cliente.")
        
        st.divider() # Línea divisoria después del panel

    st.header("Recompensas")
    st.markdown(f'<div class="marly-puntos-badge"> {st.session_state.puntos} pts</div>', unsafe_allow_html=True)
    
    for item, costo in list(st.session_state.tienda.items()):
        st.write(f"**{item}** ({costo} pts)")
        c_c, c_b = st.columns(2)
        with c_c:
            st.markdown('<div class="btn-naranja">', unsafe_allow_html=True)
            if st.button("Canjear", key=f"buy_{item}"):
                if st.session_state.puntos >= costo:
                    st.session_state.puntos -= costo
                    st.success("¡Disfrutalo!"); time.sleep(1); st.rerun()
                else: st.error("¡Faltan puntos!")
            st.markdown('</div>', unsafe_allow_html=True)
        with c_b:
            st.markdown('<div class="btn-oscuro">', unsafe_allow_html=True)
            if st.button("Eliminar", key=f"del_item_{item}"):
                del st.session_state.tienda[item]; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    with st.expander("Añadir Recompensa"):
        n_item = st.text_input("Premio")
        n_costo = st.number_input("Puntos", min_value=10, step=10)
        if st.button("Guardar Premio"):
            st.session_state.tienda[n_item] = n_costo; st.rerun()

    st.divider()
    st.header("Recordatorios")
    for idx, rec in enumerate(st.session_state.recordatorios):
        col_rec, col_del_rec = st.columns([0.8, 0.2])
        with col_rec:
            st.markdown(f'<div class="reminder-card">{rec}</div>', unsafe_allow_html=True)
        with col_del_rec:
            if st.button("🗑️", key=f"rec_del_{idx}"):
                st.session_state.recordatorios.pop(idx); st.rerun()
    
    with st.expander("Nuevo Recordatorio"):
        nuevo_rec = st.text_input("Nota:")
        if st.button("Añadir"):
            if nuevo_rec: st.session_state.recordatorios.append(nuevo_rec); st.rerun()

# --- HEADER PRINCIPAL (FECHA DINÁMICA) ---
from datetime import datetime

# Diccionario para traducir el mes a español manualmente si no quieres configurar el locale
meses_es = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

ahora = datetime.now()
dia_hoy = ahora.day
mes_hoy = meses_es[ahora.month]

st.markdown(f"""
<div style="padding: 15px; background-color: #f1f1f1; border-radius: 15px 15px 0 0; border: 2px solid {ORANGE}; border-bottom: none; text-align: center; margin-top: 10px;">
    <span style="color: {DEEP_SPACE}; font-size: 1.8rem; font-weight: 800; font-style: italic; text-transform: uppercase;">
        {st.session_state.nombre_usuario}: Plan Semanal
    </span>
</div>
<div style="background-color: white; padding: 10px; border-radius: 0 0 15px 15px; border: 2px solid {ORANGE}; text-align: center; margin-bottom: 20px;">
    <p style='color: #FF0000; font-weight: 800; font-style: italic; margin: 0;'>
        Hoy es {dia_hoy} de {mes_hoy}
    </p>
</div>
""", unsafe_allow_html=True)

# --- LOGICA DEL FEEDBACK (PARA QUE NO SE BORRE) ---
if 'mostrar_wrapped' not in st.session_state:
    st.session_state.mostrar_wrapped = False

if st.button("SOLICITAR FEEDBACK", width="stretch"):
    frases_motivadoras = [
        "No te detengas cuando estés cansada, detente cuando hayas terminado.",
        "La disciplina es el puente entre las metas y los logros.",
        "Tu futuro se crea por lo que haces hoy, no mañana.",
        "La excelencia es tu estándar.",
        "No cuentes los días, haz que los días cuenten."
    ]
    st.session_state.frase_del_dia = random.choice(frases_motivadoras)
    st.session_state.mostrar_wrapped = True
    st.rerun() # Forzamos el refresco para mostrar la tarjeta

# --- TARJETA DE FEEDBACK (DISEÑO LIMPIO) ---
if st.session_state.mostrar_wrapped:
    victorias = len(st.session_state.historial)
    frase_actual = st.session_state.get('frase_del_dia', "¡Sigue adelante!")
    
    st.markdown(f"""
<div style="background-color: {DEEP_SPACE}; padding: 30px; border-radius: 15px; border: 2px solid {AMBER}; text-align: center; margin-bottom: 20px;">
    <h2 style="color: {AMBER}; font-style: italic; margin-bottom: 15px;">Feedback de Alto Nivel</h2>
    <p style="color: white; font-size: 1.3rem; font-weight: 800; font-style: italic; line-height: 1.5; margin-bottom: 20px;">
        "{frase_actual}"
    </p>
    <div style="border-top: 2px solid {ORANGE}; margin-bottom: 20px;"></div>
    <p style="color: {SKY_BLUE}; font-size: 1.1rem; margin: 0;">
        Has alcanzado <b>{victorias}</b> victorias estratégicas.
    </p>
</div>
""", unsafe_allow_html=True)
    
    if st.button("VOLVER AL PLAN", width="stretch"):
        st.session_state.mostrar_wrapped = False
        st.rerun()

# --- SECCIÓN DE GESTIÓN (CARPETA CON ESTILO TARJETA) ---
with st.expander("📁 GESTIÓN DE ÁREAS Y TAREAS", expanded=False):
    
    # --- BLOQUE 1: NUEVA ÁREA ---
    st.markdown(f"""
        <div style="padding: 8px; background-color: #f1f1f1; border-radius: 10px 10px 0 0; border: 1px solid {ORANGE}; border-bottom: none;">
            <span style="color: {DEEP_SPACE}; font-weight: 800; font-style: italic; text-transform: uppercase;">Nueva Área</span>
        </div>
    """, unsafe_allow_html=True)
    with st.container():
        st.markdown(f'<div style="background-color: white; padding: 15px; border: 1px solid {ORANGE}; border-radius: 0 0 10px 10px; margin-bottom: 20px;">', unsafe_allow_html=True)
        na = st.text_input("Nombre de la nueva área:", placeholder="Ej: Salud, Finanzas...", key="na_input")
        st.markdown(f'<span class="area-goal">Objetivo / Meta</span>', unsafe_allow_html=True)
        ng = st.text_input("Define el objetivo:", placeholder="Ej: Estar en forma...", key="ng_input", label_visibility="collapsed")
        if st.button("AÑADIR ÁREA", width="stretch"):
            if na and na not in st.session_state.areas:
                st.session_state.areas[na] = [[], ng]
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- BLOQUE 2: NUEVA TAREA ---
    st.markdown(f"""
        <div style="padding: 8px; background-color: #f1f1f1; border-radius: 10px 10px 0 0; border: 1px solid {ORANGE}; border-bottom: none;">
            <span style="color: {DEEP_SPACE}; font-weight: 800; font-style: italic; text-transform: uppercase;">Nueva Tarea</span>
        </div>
    """, unsafe_allow_html=True)
    with st.container():
        st.markdown(f'<div style="background-color: white; padding: 15px; border: 1px solid {ORANGE}; border-radius: 0 0 10px 10px; margin-bottom: 20px;">', unsafe_allow_html=True)
        ad = st.selectbox("Área destino:", list(st.session_state.areas.keys()), key="ad_selector")
        st.markdown(f'<span class="area-goal">Tarea</span>', unsafe_allow_html=True)
        nt = st.text_input("¿Qué vas a hacer?", placeholder="Ej: Correr 5km...", key="nt_input", label_visibility="collapsed")
        
        st.markdown(f'<span class="area-goal">Días activos</span>', unsafe_allow_html=True)
        dias_tarea = st.multiselect("Selecciona los días:", dias_semana, default=dias_semana, key="dias_multi")
        
        if st.button("GUARDAR TAREA", width="stretch"):
            if nt and dias_tarea:
                st.session_state.areas[ad][0].append({"nombre": nt, "dias": dias_tarea})
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- BLOQUE 3: ELIMINAR ELEMENTOS ---
    st.markdown(f"""
        <div style="padding: 8px; background-color: #f1f1f1; border-radius: 10px 10px 0 0; border: 1px solid #ff4b4b; border-bottom: none;">
            <span style="color: {DEEP_SPACE}; font-weight: 800; font-style: italic; text-transform: uppercase;">Eliminar Elementos</span>
        </div>
    """, unsafe_allow_html=True)
    with st.container():
        st.markdown(f'<div style="background-color: white; padding: 15px; border: 1px solid #ff4b4b; border-radius: 0 0 10px 10px; margin-bottom: 20px;">', unsafe_allow_html=True)
        area_sel_del = st.selectbox("Selecciona Área para modificar:", ["..."] + list(st.session_state.areas.keys()), key="area_del_main")
        
        if area_sel_del != "...":
            tareas_en_area = [t["nombre"] for t in st.session_state.areas[area_sel_del][0]]
            if tareas_en_area:
                tarea_a_borrar = st.selectbox("Selecciona Tarea a eliminar:", ["..."] + tareas_en_area)
                if st.button("BORRAR TAREA SELECCIONADA", width="stretch"):
                    if tarea_a_borrar != "...":
                        st.session_state.areas[area_sel_del][0] = [t for t in st.session_state.areas[area_sel_del][0] if t["nombre"] != tarea_a_borrar]
                        st.rerun()
            
            st.divider()
            if st.button("ELIMINAR ÁREA COMPLETA", width="stretch", type="secondary"):
                del st.session_state.areas[area_sel_del]
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
            
# --- VISTA SEMANAL CORREGIDA (DÍAS APILADOS Y DIFERENCIADOS) ---
dict_checks = {}

for nombre_dia in dias_semana:
    with st.container():
        # Título del día en AZUL ESPACIAL para diferenciarlo de la meta roja
        st.markdown(f"""
            <div style="margin-top: 30px; padding: 10px; background-color: #f1f1f1; border-radius: 10px 10px 0 0;">
                <span style="color: {DEEP_SPACE}; font-size: 1.6rem; font-weight: 800; font-style: italic; text-transform: uppercase;">
                    {nombre_dia}
                </span>
                <div style="border-top: 3px solid {ORANGE}; margin-top: 5px; width: 100%;"></div>
            </div>
        """, unsafe_allow_html=True)
        
        v = st.session_state.version_tablero
        tareas_dia = []
        
        # Envolvemos el contenido en un div blanco para que parezca una tarjeta
        st.markdown('<div style="background-color: white; padding: 15px; border: 1px solid #ddd; border-radius: 0 0 10px 10px; margin-bottom: 20px;">', unsafe_allow_html=True)
        
        for area, datos in st.session_state.areas.items():
            tareas_filtradas = [t for t in datos[0] if nombre_dia in t["dias"]]
            
            if tareas_filtradas:
                st.markdown(f'<div class="area-header" style="font-weight:bold; color:{BLUE_GREEN}; margin-top:10px;">{area}</div>', unsafe_allow_html=True)
                
                # Meta en ROJO (como ya la tenías)
                meta = datos[1]
                st.markdown(f'<span class="area-goal">{meta}</span>', unsafe_allow_html=True)
                
                for idx, tarea_obj in enumerate(tareas_filtradas):
                    tarea_nombre = tarea_obj["nombre"]
                    k_chk, k_log = f"chk_{nombre_dia}_{tarea_nombre}_v{v}", f"log_{nombre_dia}_{tarea_nombre}_v{v}"
                    
                  # --- DISEÑO MEJORADO PARA MÓVIL (Tarea arriba, inputs abajo) ---
                    
                    # 1. Nombre de la tarea con estilo (Azul Oscuro, Negrita, Itálica)
                    st.markdown(f'<span class="task-label">{tarea_nombre}</span>', unsafe_allow_html=True)
                    
                    # 2. Fila de controles (Checkbox y Logro)
                    c_c, c_l = st.columns([0.2, 0.8]) # El checkbox ocupa poco, el logro más
                    
                    with c_c:
                        # Checkbox sin texto (label="") para que no estorbe
                        check = st.checkbox("Seleccionar ítem", key=k_chk, label_visibility="collapsed")
                        
                    with c_l:
                        logro = st.text_input("Logro:", key=k_log, placeholder="¿Qué lograste?", label_visibility="collapsed")
                    
                    # 3. Guardar estado (esto es vital para que sume puntos)
                    if check: 
                        tareas_dia.append({"Área": area, "Tarea": tarea_nombre, "Logro": logro})
                        dict_checks[k_chk] = True

     # Botón de Registrar específico para el día
        st.markdown('<div class="btn-naranja" style="margin-top:15px;">', unsafe_allow_html=True)
        if st.button(f"GUARDAR {nombre_dia.upper()}", key=f"s_{nombre_dia}_{v}", width="stretch"):
            if tareas_dia:
                puntos_ganados = len(tareas_dia) * 15
                st.session_state.puntos += puntos_ganados
                df_hoy = pd.DataFrame(tareas_dia)
                df_hoy["Fecha"] = datetime.now().strftime("%d/%m/%Y")
                df_hoy["Día"] = nombre_dia
                st.session_state.historial = pd.concat([st.session_state.historial, df_hoy], ignore_index=True)
                st.success(f"¡{nombre_dia} guardado! +{puntos_ganados} pts")
                time.sleep(0.5)
                st.rerun()
        st.markdown('</div></div>', unsafe_allow_html=True)

# --- ANALÍTICA ---
st.write("---")
c_g, c_b = st.columns([1, 1])

with c_g:
    # Título con estilo de Meta
    st.markdown('<span class="area-goal" style="font-size: 1.3rem;">Rueda de la Vida</span>', unsafe_allow_html=True)
    
    areas_lista = list(st.session_state.areas.keys())
    secuencia_colores = [ORANGE, BLUE_GREEN, SKY_BLUE, AMBER, "#ef5350", "#7e57c2", "#66bb6a"]
    progreso_real = [min(len(st.session_state.historial[st.session_state.historial["Área"] == a]) * 10, 100) for a in areas_lista]
    fig = go.Figure(go.Barpolar(
        r=progreso_real, theta=areas_lista, 
        marker_color=secuencia_colores[:len(areas_lista)], opacity=0.8
    ))
    fig.update_layout(height=380, margin=dict(t=30, b=30, l=30, r=30),
                      polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
    st.plotly_chart(fig, width="stretch")

with c_b:
    # Título con estilo de Meta
    st.markdown('<span class="area-goal" style="font-size: 1.3rem;">Bitácora</span>', unsafe_allow_html=True)
    
    # --- SCROLL LATERAL Y CONFIGURACIÓN DE TABLA ---
    st.markdown('<div style="overflow-x: auto;">', unsafe_allow_html=True)
    st.dataframe(
        st.session_state.historial, 
        width="stretch", 
        hide_index=True,
        column_config={
            "Logro": st.column_config.TextColumn("Logro", width="large"),
            "Tarea": st.column_config.TextColumn("Tarea", width="medium"),
            "Fecha": st.column_config.TextColumn("Fecha", width="small")
        }
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # --- BOTONES DE ACCIÓN (TODOS CON EL MISMO TAMAÑO) ---
    c_cob, c_lim, c_met = st.columns(3)

    with c_cob:
        if st.button("AGREGAR PTS", width="stretch"):
            st.session_state.puntos += len(dict_checks) * 15
            st.balloons()
            st.rerun()

    with c_lim:
        if st.button("LIMPIAR", width="stretch"):
            st.session_state.version_tablero += 1
            st.session_state.historial = pd.DataFrame(columns=["Fecha", "Día", "Área", "Tarea", "Logro"])
            st.rerun()

    # --- MÉTODO 5-4-3-2-1 (DISEÑO ENFOCADO EN MÓVIL) ---
    with c_met:
        if st.button("MÉTODO 5-4-3-2-1", width="stretch"):
            placeholder = st.empty()
            frases = [
                "5... ¡Visualiza tu éxito!", 
                "4... ¡Siente tu fuerza!", 
                "3... ¡Respira profundo!", 
                "2... ¡Ya casi estás ahí!", 
                "1... ¡AHORA ES EL MOMENTO!"
            ]
            
            for frase in frases:
                placeholder.markdown(f"""
                    <div style="
                        background-color: #f1f1f1; 
                        padding: 40px 20px; 
                        border-radius: 15px; 
                        border: 3px solid {ORANGE}; 
                        text-align: center; 
                        margin-top: 20px;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                        <span style="
                            color: #FF0000; 
                            font-size: 1.8rem; 
                            font-weight: 800; 
                            font-style: italic;">
                            {frase}
                        </span>
                    </div>
                """, unsafe_allow_html=True)
                time.sleep(1.0)
                
            placeholder.empty()
            st.balloons()
            
            st.markdown(f"""
                <div style="background-color: {DEEP_SPACE}; padding: 20px; border-radius: 15px; text-align: center;">
                    <p style="color: {AMBER}; font-weight: bold; margin: 0;">
                        ¡El mundo es de quienes se atreven a construirlo paso a paso! 🚀
                    </p>
                </div>
            """, unsafe_allow_html=True)
