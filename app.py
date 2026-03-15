import streamlit as st
import pandas as pd
from datetime import datetime
import time
import plotly.graph_objects as go
import random
import string
import gspread
from google.oauth2.service_account import Credentials

# --- REEMPLAZA TUS FUNCIONES DE LIMPIEZA POR ESTAS ---

def limpiar_historial_nube():
    """Limpia el historial en la nube SOLO para el usuario actual"""
    documento = conectar_google()
    if documento:
        try:
            try:
                pestana = documento.spreadsheet.worksheet("Historial")
            except:
                pestana = documento.worksheet("Historial")
            
            # 1. Obtenemos todos los datos actuales de la hoja
            filas = pestana.get_all_values()
            if len(filas) <= 1:
                return True # La hoja ya está vacía o solo tiene encabezados
            
            encabezados = filas[0]
            
            # 2. FILTRADO INTELIGENTE:
            # Creamos una lista nueva que incluya los encabezados y 
            # TODAS las filas que NO sean del usuario actual.
            # (Asumimos que el Token está en la primera columna, índice 0)
            nuevas_filas = [encabezados]
            for fila in filas[1:]:
                if fila[0] != st.session_state.user_key:
                    nuevas_filas.append(fila)
            
            # 3. Actualizamos la nube
            pestana.clear()
            pestana.update('A1', nuevas_filas)
            
            # 4. Avisamos a la app que debe refrescar la vista local
            st.session_state.actualizar_historial = True
            return True
        except Exception as e:
            st.error(f"Error al limpiar en la nube: {e}")
    return False

def limpiar_historial_local():
    """Limpia la vista inmediata en la pantalla"""
    # Reiniciamos el DataFrame a ceros
    st.session_state.historial = pd.DataFrame(columns=["Token", "Fecha", "Día", "Área", "Tarea", "Logro"])
    st.session_state.version_tablero += 1

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
                    Bienvenido/a
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

def guardar_en_historial_nube(fila_datos):
    """
    fila_datos debe ser una lista: [Token, Fecha, Día, Área, Tarea, Logro]
    """
    # Intentamos conectar
    documento = conectar_google() 
    
    if documento:
        try:
            # Si conectar_google() devuelve el libro completo, buscamos la pestaña
            # Si ya devuelve una pestaña, intentamos usar el Spreadsheet padre
            try:
                pestana_historial = documento.spreadsheet.worksheet("Historial")
            except:
                # Si lo anterior falla, es que 'documento' ya es el libro
                pestana_historial = documento.worksheet("Historial")
                
            pestana_historial.append_row(fila_datos)
            return True
        except Exception as e:
            st.error(f"Error al guardar en Historial: {e}")
    return False

# --- INICIALIZACION DE DATOS ---
dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

if 'puntos' not in st.session_state:
    st.session_state.puntos = 0  # Valor por defecto inicial
if 'version_tablero' not in st.session_state:
    st.session_state.version_tablero = 0
    try:
        hoja_p = conectar_google()
        try:
            p_puntos = hoja_p.spreadsheet.worksheet("Puntos")
        except:
            p_puntos = hoja_p.worksheet("Puntos")
            
        celda_token = p_puntos.find(st.session_state.user_key)
        if celda_token:
            valor_puntos = p_puntos.cell(celda_token.row, 2).value
            st.session_state.puntos = int(valor_puntos) if valor_puntos else 0
    except Exception as e:
        st.session_state.puntos = 0
if 'nombre_usuario' not in st.session_state:
    st.session_state.nombre_usuario = st.session_state.db_usuarios[st.session_state.user_key][0]
# --- INICIALIZACIÓN DEL HISTORIAL PERSISTENTE ---
if 'historial' not in st.session_state or st.session_state.get('actualizar_historial', False):
    hoja_h = conectar_google()
    if hoja_h:
        try:
            # Intentamos acceder a la pestaña Historial
            try:
                pestana_h = hoja_h.spreadsheet.worksheet("Historial")
            except:
                pestana_h = hoja_h.worksheet("Historial")
            
            # Traemos todos los datos
            todos_los_datos = pd.DataFrame(pestana_h.get_all_records())
            
            if not todos_los_datos.empty:
                # FILTRAR: Solo mostrar lo que pertenece al Token del usuario actual
                # Asegúrate de que tu columna en Excel se llame exactamente "Token"
                mi_historial = todos_los_datos[todos_los_datos['Token'] == st.session_state.user_key]
                st.session_state.historial = mi_historial
            else:
                st.session_state.historial = pd.DataFrame(columns=["Token", "Fecha", "Día", "Área", "Tarea", "Logro"])
            
            st.session_state.actualizar_historial = False
        except Exception as e:
            st.error(f"Error al cargar bitácora: {e}")
            st.session_state.historial = pd.DataFrame(columns=["Token", "Fecha", "Día", "Área", "Tarea", "Logro"])
if 'tienda' not in st.session_state: st.session_state.tienda = {"Café Especial": 200, "SkinCare Nuevo": 500}
# --- INICIALIZACIÓN DE ÁREAS (CÓDIGO FINAL SIN AVISOS) ---
if 'areas' not in st.session_state:
    hoja_conf = conectar_google()
    config_cargada = {}
    
    if hoja_conf:
        try:
            # Intentamos acceder de forma segura a la pestaña
            try:
                libro = hoja_conf.spreadsheet
                pestana = libro.worksheet("Configuracion")
            except:
                pestana = hoja_conf 
            
            datos = pestana.get_all_records()
            
            for fila in datos:
                # Usamos .get() para evitar errores si la columna no existe
                if str(fila.get('Token')) == st.session_state.user_key:
                    area = fila.get('Area', 'General')
                    objetivo = fila.get('Objetivo', '')
                    tarea = fila.get('Tarea', '')
                    # Si no hay días, ponemos todos por defecto
                    dias_val = fila.get('Dias', "")
                    dias = str(dias_val).split(",") if dias_val else dias_semana
                    
                    if area not in config_cargada:
                        config_cargada[area] = [[], objetivo]
                    
                    if tarea:
                        config_cargada[area][0].append({"nombre": tarea, "dias": dias})
        except Exception as e:
            # Al dejar esto solo con 'pass', el aviso amarillo desaparece
            pass

    # Si la nube falló o está vacía, cargamos los valores por defecto
    if not config_cargada:
        st.session_state.areas = {
            "Espiritu": [[{"nombre": "Lectura Biblia", "dias": dias_semana}], "Crecer en fe"],
            "Mente": [[{"nombre": "Inglés", "dias": dias_semana}], "Fluidez 2026"],
            "Cuerpo": [[{"nombre": "Ejercicio", "dias": ["Lunes", "Miércoles", "Viernes"]}], "Salud óptima"]
        }
    else:
        st.session_state.areas = config_cargada

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
        st.markdown('<span class="area-goal">PIN Nuevo (4 dígitos)</span>', unsafe_allow_html=True)
        pin_upd = st.text_input("PIN Nuevo (4 dígitos)", max_chars=4, type="password", key="ch_pin", label_visibility="collapsed")
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
            st.markdown('<span class="area-goal">Generar acceso para nuevos clientes:</span>', unsafe_allow_html=True)
            nom_cli = st.text_input("Nombre del Cliente", placeholder="Ej: Juan Pérez", key="nom_admin_key", label_visibility="collapsed")
            
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

        # --- SIDEBAR: GESTIÓN DE TIENDA ---
with st.sidebar:
    st.header("Tienda de Recompensas")
    st.markdown(f'<div class="marly-puntos-badge" style="text-align:center;"> {st.session_state.puntos} pts</div>', unsafe_allow_html=True)
    st.write("---")

    # 1. Lista de Recompensas existentes (Arriba)
    for item, costo in list(st.session_state.tienda.items()):
        st.markdown(f"**{item}** \n*{costo} pts*")
        c_c, c_b = st.columns(2)
        
        with c_c:
            st.markdown('<div class="btn-naranja">', unsafe_allow_html=True)
            if st.button("Canjear", key=f"side_buy_{item}"):
                if st.session_state.puntos >= costo:
                    st.session_state.puntos -= costo
                    st.success("¡Canjeado!")
                    time.sleep(1)
                    st.rerun()
                else: 
                    st.error("Puntos insuficientes")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c_b:
            st.markdown('<div class="btn-oscuro">', unsafe_allow_html=True)
            if st.button("Eliminar", key=f"side_del_{item}"):
                hoja_t = conectar_google()
                if hoja_t:
                    try:
                        try:
                            pestana_t = hoja_t.spreadsheet.worksheet("Tienda")
                        except:
                            pestana_t = hoja_t.worksheet("Tienda")
                        
                        filas = pestana_t.get_all_values()
                        for i, fila in enumerate(filas, 1):
                            if str(fila[0]) == st.session_state.user_key and str(fila[1]) == item:
                                pestana_t.delete_rows(i)
                                break
                        
                        del st.session_state.tienda[item]
                        st.rerun()
                    except:
                        st.error("Error en la nube")
            st.markdown('</div>', unsafe_allow_html=True)
        st.write("---")

    # 2. Formulario para Añadir Recompensa (Abajo)
    with st.expander("➕ Añadir Recompensa"):
        st.markdown('<span class="area-goal">Nombre del Premio</span>', unsafe_allow_html=True)
        n_item = st.text_input("Premio", label_visibility="collapsed", key="new_reward_name")
        
        st.markdown('<span class="area-goal">Costo en Puntos</span>', unsafe_allow_html=True)
        n_costo = st.number_input("Puntos", min_value=10, step=10, label_visibility="collapsed")
        
        if st.button("Guardar Premio", use_container_width=True):
            if n_item:
                hoja_t = conectar_google()
                if hoja_t:
                    try:
                        try:
                            pestana_t = hoja_t.spreadsheet.worksheet("Tienda")
                        except:
                            pestana_t = hoja_t.worksheet("Tienda")
                        
                        pestana_t.append_row([st.session_state.user_key, n_item, n_costo])
                        st.session_state.tienda[n_item] = n_costo 
                        st.success("¡Guardado!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

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
    
   # --- BLOQUE 1: NUEVA ÁREA (ACTUALIZADO PARA GUARDAR EN NUBE) ---
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
                # 1. Guardar en la nube (Excel)
                hoja_c = conectar_google()
                if hoja_c:
                    try:
                        # Buscamos la pestaña Configuracion
                        try:
                            p_conf = hoja_c.spreadsheet.worksheet("Configuracion")
                        except:
                            p_conf = hoja_c.worksheet("Configuracion")
                        
                        # Añadimos la fila: Token, Area, Objetivo, Tarea(vacia), Dias(vacia)
                        p_conf.append_row([st.session_state.user_key, na, ng, "", ""])
                        
                        # 2. Actualizar memoria local para que se vea el cambio
                        st.session_state.areas[na] = [[], ng]
                        st.success(f"Área '{na}' guardada permanentemente.")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar en la nube: {e}")
                else:
                    st.error("No hay conexión con el Excel.")
        st.markdown('</div>', unsafe_allow_html=True)
    # --- BLOQUE 2: NUEVA TAREA ---
    # --- BLOQUE 2: NUEVA TAREA (CONEXIÓN A NUBE) ---
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
                # 1. Guardar en la nube (Excel)
                hoja_c = conectar_google()
                if hoja_c:
                    try:
                        try:
                            p_conf = hoja_c.spreadsheet.worksheet("Configuracion")
                        except:
                            p_conf = hoja_c.worksheet("Configuracion")
                        
                        # Convertimos la lista de días ["Lunes", "Martes"] en un texto "Lunes,Martes"
                        dias_texto = ",".join(dias_tarea)
                        # Buscamos el objetivo actual de esa área para no dejarlo vacío
                        objetivo_actual = st.session_state.areas[ad][1]
                        
                        # Añadimos fila: Token, Area, Objetivo, Tarea, Dias
                        p_conf.append_row([st.session_state.user_key, ad, objetivo_actual, nt, dias_texto])
                        
                        # 2. Actualizar memoria local
                        st.session_state.areas[ad][0].append({"nombre": nt, "dias": dias_tarea})
                        st.success(f"Tarea '{nt}' añadida a {ad}")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar tarea: {e}")
                else:
                    st.error("Error de conexión.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- BLOQUE 3: ELIMINAR ELEMENTOS ---
    # --- BLOQUE 3: ELIMINAR ELEMENTOS (LIMPIEZA EN NUBE) ---
    RED_ALERT = "#FF4B4B" # El rojo estándar de Streamlit
    st.markdown(f"""
        <div style="padding: 8px; background-color: #f1f1f1; border-radius: 10px 10px 0 0; border: 1px solid {RED_ALERT}; border-bottom: none;">
            <span style="color: {DEEP_SPACE}; font-weight: 800; font-style: italic; text-transform: uppercase;">Eliminar Elementos</span>
        </div>
    """, unsafe_allow_html=True)
    with st.container():
        st.markdown(f'<div style="background-color: white; padding: 15px; border: 1px solid {RED_ALERT}; border-radius: 0 0 10px 10px;">', unsafe_allow_html=True)
        opcion_del = st.radio("¿Qué deseas eliminar?", ["Una Tarea", "Un Área completa"], horizontal=True)
        
        hoja_c = conectar_google()
        try:
            p_conf = hoja_c.spreadsheet.worksheet("Configuracion")
        except:
            p_conf = hoja_c.worksheet("Configuracion")

        if opcion_del == "Una Tarea":
            ae = st.selectbox("Área de la tarea:", list(st.session_state.areas.keys()), key="ae_selector")
            tareas_disp = [t["nombre"] for t in st.session_state.areas[ae][0]]
            te = st.selectbox("Selecciona la tarea a eliminar:", tareas_disp, key="te_selector")
            
            if st.button("ELIMINAR TAREA", width="stretch"):
                # 1. Borrar en Excel
                celda = p_conf.find(te) # Busca el nombre de la tarea
                if celda:
                    p_conf.delete_rows(celda.row)
                
                # 2. Borrar en memoria local
                st.session_state.areas[ae][0] = [t for t in st.session_state.areas[ae][0] if t["nombre"] != te]
                st.error(f"Tarea '{te}' eliminada.")
                time.sleep(1)
                st.rerun()

        else:
            area_e = st.selectbox("Área a eliminar:", list(st.session_state.areas.keys()), key="area_e_selector")
            if st.button("ELIMINAR ÁREA", width="stretch"):
                # 1. Borrar todas las filas de esa área en Excel
                filas = p_conf.get_all_values()
                for i, fila in enumerate(reversed(filas), 1):
                    # Si el Token coincide y el Area coincide
                    if fila[0] == st.session_state.user_key and fila[1] == area_e:
                        p_conf.delete_rows(len(filas) - i + 1)
                
                # 2. Borrar en memoria local
                del st.session_state.areas[area_e]
                st.error(f"Área '{area_e}' y sus tareas eliminadas.")
                time.sleep(1)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
            
# --- VISTA SEMANAL CON DESPLEGABLES Y METAS EN ROJO ---
dict_checks = {}

for i, nombre_dia in enumerate(dias_semana):
    # Creamos el expander para cada día
    with st.expander(f"📅 {nombre_dia.upper()}", expanded=False):
        
        # Título interno con tu estilo de Azul Espacial y Naranja
        st.markdown(f"""
            <div style="padding: 5px; border-bottom: 3px solid {ORANGE}; margin-bottom: 15px;">
                <span style="color: {DEEP_SPACE}; font-size: 1.4rem; font-weight: 800; font-style: italic;">
                    ÁREAS Y TAREAS
                </span>
            </div>
        """, unsafe_allow_html=True)
        
        v = st.session_state.version_tablero
        tareas_dia_recolectadas = [] 
        
        # --- BUCLE DE ÁREAS ---
        for nombre_area, info in st.session_state.areas.items():
            lista_tareas = info[0] 
            meta = info[1]        

            tareas_filtradas = [
                t for t in lista_tareas 
                if isinstance(t, dict) and nombre_dia.lower() in [d.strip().lower() for d in t.get("dias", [])]
            ]
             
            if tareas_filtradas:
                # Nombre del Área
                st.markdown(f'<div style="font-weight:bold; color:{BLUE_GREEN}; margin-top:15px; border-left: 4px solid {BLUE_GREEN}; padding-left: 10px;">{nombre_area.upper()}</div>', unsafe_allow_html=True)
                
                # --- META EN ROJO (Actualizado) ---
                st.markdown(f'<div style="color: #FF0000; font-weight: bold; font-size: 1.0rem; margin-bottom: 10px;">🎯 Meta: {meta}</div>', unsafe_allow_html=True)
                
                for idx, tarea_obj in enumerate(tareas_filtradas):
                    tarea_nombre = tarea_obj["nombre"]
                    k_chk = f"chk_{nombre_dia}_{nombre_area}_{idx}_v{v}"
                    k_log = f"log_{nombre_dia}_{nombre_area}_{idx}_v{v}"
                    
                    st.markdown(f'<div style="color: {DEEP_SPACE}; font-weight: 600; margin-top: 8px;">{tarea_nombre}</div>', unsafe_allow_html=True)
                    
                    c_c, c_l = st.columns([0.15, 0.85]) 
                    with c_c:
                        check = st.checkbox("Logrado", key=k_chk, label_visibility="collapsed")
                    with c_l:
                        logro = st.text_input("Logro:", key=k_log, placeholder="¿Qué lograste?", label_visibility="collapsed")
                    
                    if check: 
                        tareas_dia_recolectadas.append({
                            "Área": nombre_area, 
                            "Tarea": tarea_nombre, 
                            "Logro": logro if logro else "Tarea completada"
                        })

        # --- BOTÓN DE GUARDAR ---
        st.markdown('<div style="margin-top:20px;">', unsafe_allow_html=True)
        if st.button(f"FINALIZAR {nombre_dia.upper()}", key=f"btn_save_{nombre_dia}_{v}", use_container_width=True):
            if tareas_dia_recolectadas:
                df_hoy = pd.DataFrame(tareas_dia_recolectadas)
                df_hoy["Fecha"] = datetime.now().strftime("%d/%m/%Y")
                df_hoy["Día"] = nombre_dia
                
                st.session_state.historial = pd.concat([st.session_state.historial, df_hoy], ignore_index=True)
                
                st.success(f"¡{nombre_dia} guardado en la Bitácora!")
                time.sleep(1)
                st.rerun()
            else:
                st.warning("No hay tareas seleccionadas.")
        st.markdown('</div>', unsafe_allow_html=True)
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

    # ¡ESTO DEBE ESTAR AQUÍ ADENTRO! (Indentado)
    fig.update_layout(
        height=380,
        margin=dict(t=30, b=30, l=30, r=30),
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(
                    size=10, 
                    color="#ef5350", 
                    weight="bold"
                )
            )
        )
    )
    st.plotly_chart(fig, width="stretch")

# --- DENTRO DE TU COLUMNA DE BITÁCORA (with c_b:) ---
    with c_b:
        # 1. TÍTULO
        st.markdown('<span class="area-goal" style="font-size: 1.3rem;">Bitácora</span>', unsafe_allow_html=True)
        
        # 2. TABLA VISUAL
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

        # 3. ESPACIO Y COLUMNAS PARA BOTONES
        st.write("")
        c_cob, c_lim, c_met = st.columns(3)

       # --- BOTÓN 1: AGREGAR PUNTOS (CON SINCRONIZACIÓN DE SALDO TOTAL) ---
with c_cob:
    if st.button("AGREGAR PTS", key="btn_final_pts", width="stretch"):
        if not st.session_state.historial.empty:
            try:
                # 1. Guardar cada tarea en la pestaña de Historial
                for index, fila in st.session_state.historial.iterrows():
                    datos_excel = [
                        st.session_state.user_key, 
                        fila["Fecha"], 
                        fila["Día"], 
                        fila["Área"], 
                        fila["Tarea"], 
                        fila["Logro"]
                    ]
                    guardar_en_historial_nube(datos_excel)
                
                # 2. Calcular y actualizar puntos localmente
                puntos_ganados = len(st.session_state.historial) * 10
                st.session_state.puntos += puntos_ganados
                st.session_state.version_tablero += 1

                # 3. --- SINCRONIZAR SALDO TOTAL EN PESTAÑA "PUNTOS" ---
                hoja_p = conectar_google()
                try:
                    try:
                        p_puntos = hoja_p.spreadsheet.worksheet("Puntos")
                    except:
                        p_puntos = hoja_p.worksheet("Puntos")
                    
                    # Buscamos si el Token ya existe en la columna A
                    celda_token = p_puntos.find(st.session_state.user_key)
                    
                    if celda_token:
                        # Si existe, actualizamos la columna B (celda de al lado)
                        p_puntos.update_cell(celda_token.row, 2, st.session_state.puntos)
                    else:
                        # Si es la primera vez del usuario, creamos su registro
                        p_puntos.append_row([st.session_state.user_key, st.session_state.puntos])
                except Exception as e_pts:
                    st.warning(f"Historial guardado, pero no se pudo actualizar el saldo total: {e_pts}")

                # 4. Finalizar
                st.success(f"¡Sincronizado! +{puntos_ganados} pts.")
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"Error al sincronizar: {e}")
        else:
            st.warning("La bitácora está vacía.")

with c_lim:
    # Agregamos un checkbox o un mensaje de advertencia antes de limpiar
    if st.button("LIMPIAR TODO", key="btn_final_limpiar", use_container_width=True):
        with st.spinner("Limpiando registros..."):
            # Intentamos limpiar la nube primero (Google Sheets)
            if limpiar_historial_nube(): 
                # Si la nube se limpió, procedemos con lo local
                st.session_state.historial = pd.DataFrame(columns=["Fecha", "Día", "Área", "Tarea", "Logro"])
                st.session_state.version_tablero += 1
                
                st.success("¡Historial eliminado con éxito!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("No se pudo conectar con la nube. Intenta de nuevo.")

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


