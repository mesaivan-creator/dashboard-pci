import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración inicial de la página
st.set_page_config(
    page_title="Dashboard Proyectos PCI - SharePoint",
    page_icon="📈",
    layout="wide"
)

st.title("📊 Dashboard de Seguimiento de Proyectos - PCI (SharePoint)")

# ENLACE DE SHAREPOINT INSTITUCIONAL DE LA UNIVERSIDAD EL BOSQUE
# URL con parámetro de descarga directa habilitado (?download=1)
SHAREPOINT_URL = "https://unbosqueeduco-my.sharepoint.com/:x:/g/personal/investigaciones_unbosque_edu_co/IQCkCPRJP4-tSafuBd1A0TOTAVVR4XsxURv683539zcxxHg?download=1"

# 1. Carga Eficiente de Datos con Caché de 5 minutos
@st.cache_data(ttl=300)  # Se actualiza automáticamente cada 5 minutos
def load_data(url):
    # Carga directamente el Excel desde la URL de SharePoint
    df = pd.read_excel(url, engine="openpyxl")
    
    # Ajuste de fechas y valores numéricos
    if "Fecha de creación" in df.columns:
        df["Fecha de creación"] = pd.to_datetime(df["Fecha de creación"], errors="coerce")
    
    if "Costo real COP Aprox*" in df.columns:
        df["Costo real COP Aprox*"] = pd.to_numeric(df["Costo real COP Aprox*"], errors="coerce").fillna(0)
        
    return df

try:
    df = load_data(SHAREPOINT_URL)
except Exception as e:
    st.error(f"Error al conectar con SharePoint. Verifica que los permisos del enlace permitan acceso externo sin login: {e}")
    st.stop()

# Botón para recargar datos manualmente
if st.sidebar.button("🔄 Actualizar datos ahora"):
    st.cache_data.clear()
    st.rerun()

# 2. Barra Lateral - Filtros Dinámicos
st.sidebar.header("🔍 Filtros de Control")

# Filtro por Proyecto / Código PCI
pci_opts = sorted([str(x) for x in df["CÓDIGO PCI"].dropna().unique()]) if "CÓDIGO PCI" in df.columns else []
pci_sel = st.sidebar.multiselect("Código PCI:", options=pci_opts, default=[])

# Filtro por Rubro Presupuestal
rubro_opts = sorted([str(x) for x in df["Rubro Presupuestal"].dropna().unique()]) if "Rubro Presupuestal" in df.columns else []
rubro_sel = st.sidebar.multiselect("Rubro Presupuestal:", options=rubro_opts, default=[])

# Filtro por Solicitante
solic_opts = sorted([str(x) for x in df["Solicitante"].dropna().unique()]) if "Solicitante" in df.columns else []
solic_sel = st.sidebar.multiselect("Solicitante:", options=solic_opts, default=[])

# Aplicación de filtros
df_filtered = df.copy()

if pci_sel and "CÓDIGO PCI" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["CÓDIGO PCI"].astype(str).isin(pci_sel)]
if rubro_sel and "Rubro Presupuestal" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["Rubro Presupuestal"].astype(str).isin(rubro_sel)]
if solic_sel and "Solicitante" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["Solicitante"].astype(str).isin(solic_sel)]

# 3. Métricas Principales (KPIs)
st.subheader("📌 Resumen Ejecutivo")
m1, m2, m3, m4 = st.columns(4)

total_solicitudes = len(df_filtered)
total_monto = df_filtered["Costo real COP Aprox*"].sum() if "Costo real COP Aprox*" in df_filtered.columns else 0
total_pci = df_filtered["CÓDIGO PCI"].nunique() if "CÓDIGO PCI" in df_filtered.columns else 0
total_proveedores = df_filtered["Tercero / Proveedor"].nunique() if "Tercero / Proveedor" in df_filtered.columns else 0

m1.metric("Total Solicitudes", f"{total_solicitudes:,}")
m2.metric("Ejecución Total (COP)", f"${total_monto:,.0f}")
m3.metric("Proyectos Únicos", f"{total_pci}")
m4.metric("Proveedores Activos", f"{total_proveedores}")

st.markdown("---")

# 4. Visualizaciones Gráficas Agregadas
st.subheader("📈 Análisis Agregado")

col1, col2 = st.columns(2)

with col1:
    if "Rubro Presupuestal" in df_filtered.columns and "Costo real COP Aprox*" in df_filtered.columns:
        df_rubro = df_filtered.groupby("Rubro Presupuestal", as_index=False)["Costo real COP Aprox*"].sum()
        df_rubro = df_rubro.sort_values(by="Costo real COP Aprox*", ascending=False)
        
        fig_rubro = px.bar(
            df_rubro,
            x="Rubro Presupuestal",
            y="Costo real COP Aprox*",
            color="Rubro Presupuestal",
            title="Ejecución Presupuestal por Rubro (COP)",
            text_auto=",.0f"
        )
        fig_rubro.update_layout(showlegend=False, xaxis_title="", yaxis_title="COP")
        st.plotly_chart(fig_rubro, use_container_width=True)

with col2:
    if "CÓDIGO PCI" in df_filtered.columns and "Costo real COP Aprox*" in df_filtered.columns:
        df_pci = df_filtered.groupby("CÓDIGO PCI", as_index=False)["Costo real COP Aprox*"].sum()
        
        fig_pci = px.pie(
            df_pci,
            names="CÓDIGO PCI",
            values="Costo real COP Aprox*",
            title="Participación de Costo por Proyecto (PCI)",
            hole=0.4
        )
        st.plotly_chart(fig_pci, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    if "Tercero / Proveedor" in df_filtered.columns and "Costo real COP Aprox*" in df_filtered.columns:
        df_prov = df_filtered.groupby("Tercero / Proveedor", as_index=False)["Costo real COP Aprox*"].sum()
        df_prov = df_prov.sort_values(by="Costo real COP Aprox*", ascending=True).tail(10)
        
        fig_prov = px.bar(
            df_prov,
            x="Costo real COP Aprox*",
            y="Tercero / Proveedor",
            orientation="h",
            title="Top 10 Proveedores con Mayor Ejecución",
            text_auto=",.0f"
        )
        fig_prov.update_layout(xaxis_title="COP", yaxis_title="")
        st.plotly_chart(fig_prov, use_container_width=True)

with col4:
    if "Fecha de creación" in df_filtered.columns and not df_filtered["Fecha de creación"].isna().all():
        df_time = df_filtered.set_index("Fecha de creación").resample("ME")["Costo real COP Aprox*"].sum().reset_index()
        fig_time = px.line(
            df_time,
            x="Fecha de creación",
            y="Costo real COP Aprox*",
            title="Evolución de Ejecución Mensual",
            markers=True
        )
        fig_time.update_layout(xaxis_title="Fecha", yaxis_title="COP")
        st.plotly_chart(fig_time, use_container_width=True)

# 5. Vista de Datos Detallada
st.markdown("---")
st.subheader("📑 Registro de Solicitudes Filtradas")

cols_mostrar = [
    "N. Solicitud", "Fecha de creación", "CÓDIGO PCI", "Solicitante", 
    "Rubro Presupuestal", "Tercero / Proveedor", "Costo real COP Aprox*", 
    "Estado orden de compra", "Orden de compra"
]

cols_validas = [c for c in cols_mostrar if c in df_filtered.columns]

st.dataframe(
    df_filtered[cols_validas],
    use_container_width=True,
    hide_index=True
)
