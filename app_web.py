import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# 🎨 Configuración de la página en modo oscuro nativo
st.set_page_config(page_title="Panel de Control - Barbería", page_icon="✂️", layout="centered")

# 🔐 Conexión a tu Supabase actual
URL_SUPABASE = "TU_URL_DE_SUPABASE"
KEY_SUPABASE = "TU_KEY_DE_SUPABASE"

@st.cache_resource
def conectar_supabase():
    return create_client(URL_SUPABASE, KEY_SUPABASE)

supabase = conectar_supabase()

st.title("✂️ Panel Administrativo Remoto")

# Creación de pestañas para mantener la interfaz limpia
tab_registro, tab_historial = st.tabs(["📝 Registrar Servicio", "📊 Historial y Reportes"])

# ==========================================
# PESTAÑA 1: REGISTRO DE SERVICIOS
# ==========================================
with tab_registro:
    st.subheader("Registrar nuevo servicio desde cámaras")
    
    with st.form("registro_servicio", clear_on_submit=True):
        servicio = st.selectbox("Servicio realizado:", ["Corte Sencillo", "Corte + Barba", "Cigarro/Bebida", "Combo Completo"])
        valor = st.number_input("Valor del servicio ($):", min_value=0, value=15000, step=1000)
        pago = st.selectbox("Método de Pago:", ["Efectivo", "Transferencia"])
        
        submit = st.form_submit_button("Guardar Registro")

    if submit:
        ahora = datetime.now()
        nueva_venta = {
            "fecha": ahora.strftime("%Y-%m-%d"),
            "hora": ahora.strftime("%I:%M %p"),
            "servicio": servicio,
            "valor": valor,
            "pago": pago,
            "origen": "WEB"  # El .exe buscará este tag para descargarlo localmente
        }
        
        try:
            supabase.table("ventas").insert(nueva_venta).execute()
            st.success(f"✅ ¡{servicio} por ${valor:,} registrado! La caja local lo descargará automáticamente.")
        except Exception as e:
            st.error(f"Error al guardar en la nube: {e}")

# ==========================================
# PESTAÑA 2: HISTORIAL TAL COMO EN EL .EXE
# ==========================================
with tab_historial:
    st.subheader("Filtro de Historial")
    
    # Selector de fechas (Por defecto muestra el día de hoy)
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("Desde:", datetime.now())
    with col2:
        fecha_fin = st.date_input("Hasta:", datetime.now())
        
    if st.button("Buscar Historial", type="primary"):
        # Formateamos las fechas para la consulta en Supabase
        f_inicio_str = fecha_inicio.strftime("%Y-%m-%d")
        f_fin_str = fecha_fin.strftime("%Y-%m-%d")
        
        try:
            # Consulta con filtros de rango de fecha a Supabase
            respuesta = supabase.table("ventas")\
                .select("*")\
                .gte("fecha", f_inicio_str)\
                .lte("fecha", f_fin_str)\
                .order("fecha", ascending=False)\
                .execute()
                
            datos = respuesta.data
            
            if datos:
                # Convertimos a un DataFrame de Pandas para manejarlo como tabla fácilmente
                df = pd.DataFrame(datos)
                
                # Renombramos las columnas para que se vea estético
                df_visual = df[["fecha", "hora", "servicio", "valor", "pago"]].copy()
                df_visual.columns = ["Fecha", "Hora", "Servicio", "Valor ($)", "Método de Pago"]
                
                # 💰 Cálculos de totales en tiempo real
                total_general = df["valor"].sum()
                total_efectivo = df[df["pago"] == "Efectivo"]["valor"].sum() if "Efectivo" in df["pago"].values else 0
                total_transferencia = df[df["pago"] == "Transferencia"]["valor"].sum() if "Transferencia" in df["pago"].values else 0
                
                # Cuadros de resumen (Métricas llamativas arriba)
                st.write("---")
                c_tot, c_efe, c_tra = st.columns(3)
                c_tot.metric("Total Recaudado", f"${total_general:,.0f}")
                c_efe.metric("Efectivo 💵", f"${total_efectivo:,.0f}")
                c_tra.metric("Transferencias 📱", f"${total_transferencia:,.0f}")
                st.write("---")
                
                # Mostramos la tabla interactiva donde el jefe puede ordenar por columnas o buscar
                st.dataframe(df_visual, use_container_width=True, hide_index=True)
                
            else:
                st.info("📅 No se encontraron registros de servicios en el rango de fechas seleccionado.")
                
        except Exception as e:
            st.error(f"Error al consultar el historial: {e}")