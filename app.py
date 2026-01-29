import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import hashlib
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from streamlit.connections import ExperimentalBaseConnection
from streamlit.runtime.caching import cache_data

# ============================================
# CONFIGURACIÓN
# ============================================

# Configuración de la página
st.set_page_config(
    page_title="Inventario Ropa Caballero",
    page_icon="👔",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Inicializar estado de sesión
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

# Clase para conexión a Google Sheets
class GSheetsConnection(ExperimentalBaseConnection):
    def _connect(self, **kwargs):
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds_dict = st.secrets["gcp_service_account"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            client = gspread.authorize(creds)
            return client
        except Exception as e:
            st.error(f"Error de conexión Google Sheets: {str(e)}")
            return None
    
    def get_data(self, spreadsheet_url, worksheet_name="Inventario", **kwargs):
        @cache_data(ttl=300)
        def _get_data(spreadsheet_url, worksheet_name):
            try:
                client = self._connect()
                if client is None:
                    return pd.DataFrame(columns=[
                        'ID', 'Categoria', 'Producto', 'Talla', 
                        'Color', 'Entrada', 'Ventas', 'Stock', 'Precio'
                    ])
                
                spreadsheet = client.open_by_url(spreadsheet_url)
                worksheet = spreadsheet.worksheet(worksheet_name)
                data = worksheet.get_all_records()
                
                if not data:
                    return pd.DataFrame(columns=[
                        'ID', 'Categoria', 'Producto', 'Talla', 
                        'Color', 'Entrada', 'Ventas', 'Stock', 'Precio'
                    ])
                
                df = pd.DataFrame(data)
                
                # Convertir columnas numéricas
                numeric_columns = ['Entrada', 'Ventas', 'Stock', 'Precio']
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
                return df
            except Exception as e:
                st.error(f"Error al obtener datos: {str(e)}")
                return pd.DataFrame(columns=[
                    'ID', 'Categoria', 'Producto', 'Talla', 
                    'Color', 'Entrada', 'Ventas', 'Stock', 'Precio'
                ])
        
        return _get_data(spreadsheet_url, worksheet_name)
    
    def update_data(self, spreadsheet_url, data, worksheet_name="Inventario"):
        try:
            client = self._connect()
            if client is None:
                return False
                
            spreadsheet = client.open_by_url(spreadsheet_url)
            worksheet = spreadsheet.worksheet(worksheet_name)
            
            if isinstance(data, pd.DataFrame):
                values = [data.columns.tolist()] + data.fillna('').values.tolist()
            else:
                values = data
            
            worksheet.clear()
            worksheet.update(values, value_input_option='USER_ENTERED')
            return True
        except Exception as e:
            st.error(f"Error al actualizar: {str(e)}")
            return False

# Inicializar conexión
@st.cache_resource
def init_connection():
    return GSheetsConnection("gsheets")

# Funciones de autenticación SIMPLIFICADAS
def check_password():
    return st.session_state.admin_logged_in

def login_section():
    """Sección de login SIMPLIFICADA"""
    st.markdown("### 🔒 Acceso Administrador")
    
    # Usar un contenedor simple
    with st.container():
        password = st.text_input("Contraseña:", type="password", key="password_input")
        
        if st.button("Ingresar", key="login_button", type="primary"):
            # COMPARACIÓN DIRECTA - SIN HASH POR AHORA
            if password == "michiotaku":
                st.session_state.admin_logged_in = True
                st.success("✅ Acceso concedido")
                st.rerun()
            else:
                st.error(f"❌ Contraseña incorrecta. Ingresaste: '{password}'")
    
    return False

# Función principal
def main():
    st.title("👔 Inventario Ropa de Caballero")
    st.markdown("---")
    
    # Inicializar conexión
    conn = init_connection()
    
    # Obtener URL desde secrets
    try:
        SPREADSHEET_URL = st.secrets["spreadsheet_url"]
        WORKSHEET_NAME = "Inventario"
    except KeyError as e:
        st.error(f"❌ Error: No se encontró {e} en los Secrets")
        st.stop()
    
    # Cargar datos
    try:
        df = conn.get_data(SPREADSHEET_URL, WORKSHEET_NAME)
        
        if df.empty:
            st.info("📭 La base de datos está vacía. Comienza cargando productos.")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        df = pd.DataFrame(columns=[
            'ID', 'Categoria', 'Producto', 'Talla', 
            'Color', 'Entrada', 'Ventas', 'Stock', 'Precio'
        ])
    
    # Pestañas
    tab1, tab2, tab3 = st.tabs(["🛍️ Registrar Ventas", "📊 Reporte y Caja", "📦 Cargar Mercancía"])
    
    # TAB 1: REGISTRAR VENTAS
    with tab1:
        st.header("Registrar Ventas")
        
        if df.empty:
            st.info("No hay productos en el inventario.")
        else:
            search_term = st.text_input("🔍 Buscar producto:", "")
            
            if search_term:
                filtered_df = df[df['Producto'].str.contains(search_term, case=False, na=False)]
            else:
                filtered_df = df
            
            if filtered_df.empty:
                st.info("No se encontraron productos.")
            else:
                st.write(f"**{len(filtered_df)} productos**")
                
                for _, row in filtered_df.iterrows():
                    with st.expander(f"{row['Producto']} - Talla: {row['Talla']} - Color: {row['Color']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Categoría:** {row['Categoria']}")
                            st.write(f"**Precio:** ${row['Precio']:,.2f}")
                            st.write(f"**Stock:** {int(row['Stock'])}")
                        
                        with col2:
                            st.write(f"**Ventas:** {int(row['Ventas'])}")
                            st.write(f"**Entrada:** {int(row['Entrada'])}")
                        
                        if st.button("✅ Vender", key=f"v_{row['ID']}"):
                            if row['Stock'] > 0:
                                try:
                                    idx = df[df['ID'] == row['ID']].index[0]
                                    df.at[idx, 'Ventas'] += 1
                                    df.at[idx, 'Stock'] -= 1
                                    conn.update_data(SPREADSHEET_URL, df, WORKSHEET_NAME)
                                    st.success("✅ Venta registrada")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                            else:
                                st.error("❌ Sin stock")
    
    # TAB 2: REPORTE Y CAJA
    with tab2:
        st.header("Reporte y Caja")
        
        col1, col2 = st.columns([3,1])
        with col2:
            if st.button("🔄 Actualizar"):
                cache_data.clear()
                st.rerun()
        
        if not df.empty:
            # Métricas
            col1, col2, col3 = st.columns(3)
            with col1:
                try:
                    dinero = (df['Ventas'] * df['Precio']).sum()
                    st.metric("💰 Caja", f"${dinero:,.2f}")
                except:
                    st.metric("💰 Caja", "$0.00")
            with col2:
                try:
                    stock = df['Stock'].sum()
                    st.metric("📦 Stock", f"{int(stock)}")
                except:
                    st.metric("📦 Stock", "0")
            with col3:
                try:
                    productos = df['Producto'].nunique()
                    st.metric("👔 Productos", productos)
                except:
                    st.metric("👔 Productos", "0")
            
            # Gráficos
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                try:
                    ventas_cat = df.groupby('Categoria')['Ventas'].sum().reset_index()
                    if not ventas_cat.empty:
                        fig = px.pie(ventas_cat, values='Ventas', names='Categoria', title="Ventas por Categoría")
                        st.plotly_chart(fig, use_container_width=True)
                except:
                    pass
            
            with col2:
                try:
                    stock_cat = df.groupby('Categoria')['Stock'].sum().reset_index()
                    if not stock_cat.empty:
                        fig = px.bar(stock_cat, x='Categoria', y='Stock', title="Stock por Categoría", color='Categoria')
                        st.plotly_chart(fig, use_container_width=True)
                except:
                    pass
            
            # Tabla
            st.markdown("### 📋 Datos Completos")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Exportar
            if st.button("📥 Exportar CSV"):
                try:
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Descargar",
                        csv,
                        f"inventario_{datetime.now().strftime('%Y%m%d')}.csv",
                        "text/csv"
                    )
                except:
                    st.error("Error al exportar")
        else:
            st.info("No hay datos")
    
    # TAB 3: CARGAR MERCANCÍA
    with tab3:
        st.header("Cargar Mercancía")
        
        if not check_password():
            login_section()
        else:
            st.success("✅ Modo administrador")
            
            if st.button("🚪 Cerrar Sesión"):
                st.session_state.admin_logged_in = False
                st.rerun()
            
            st.markdown("---")
            
            with st.form("nuevo_producto"):
                st.subheader("📝 Nuevo Producto")
                new_id = f"PROD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                col1, col2 = st.columns(2)
                with col1:
                    # Categoría
                    cats = sorted(df['Categoria'].unique().tolist()) if not df.empty else []
                    cats.append('+ Nueva Categoría')
                    cat_sel = st.selectbox("Categoría:", cats, key="cat_sel")
                    
                    if cat_sel == '+ Nueva Categoría':
                        categoria = st.text_input("Nueva categoría:", key="new_cat")
                    else:
                        categoria = cat_sel
                    
                    producto = st.text_input("Producto:", key="prod")
                    color = st.text_input("Color:", key="color")
                
                with col2:
                    # Tallas dinámicas
                    if categoria and ('pantalón' in str(categoria).lower() or 'short' in str(categoria).lower()):
                        tallas = ['28', '30', '32', '34', '36', '38', '40', '42']
                    else:
                        tallas = ['XCH', 'CH', 'M', 'G', 'XG', 'XXG']
                    
                    talla = st.selectbox("Talla:", tallas, key="talla")
                    entrada = st.number_input("Cantidad:", min_value=1, value=1, key="ent")
                    precio = st.number_input("Precio $:", min_value=0.0, value=0.0, step=0.01, key="precio")
                
                submit = st.form_submit_button("➕ Agregar Producto")
                
                if submit:
                    if not categoria or not producto or not color:
                        st.error("❌ Faltan datos")
                    else:
                        nuevo = {
                            'ID': new_id,
                            'Categoria': categoria,
                            'Producto': producto,
                            'Talla': talla,
                            'Color': color,
                            'Entrada': int(entrada),
                            'Ventas': 0,
                            'Stock': int(entrada),
                            'Precio': float(precio)
                        }
                        
                        try:
                            nuevo_df = pd.DataFrame([nuevo])
                            df = pd.concat([df, nuevo_df], ignore_index=True)
                            conn.update_data(SPREADSHEET_URL, df, WORKSHEET_NAME)
                            st.success(f"✅ {producto} agregado")
                            cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()