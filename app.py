import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import hashlib
from streamlit.connections import ExperimentalBaseConnection
from streamlit.runtime.caching import cache_data

# Configuración de la página
st.set_page_config(
    page_title="Inventario Ropa Caballero",
    page_icon="👔",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Clase personalizada para conexión a Google Sheets
class GSheetsConnection(ExperimentalBaseConnection):
    def _connect(self, **kwargs):
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        
        # Configurar scope
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        
        # Cargar credenciales
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        
        client = gspread.authorize(creds)
        return client
    
    def get_data(self, spreadsheet_url, worksheet_name="Inventario", **kwargs):
        @cache_data(ttl=300)
        def _get_data(spreadsheet_url, worksheet_name):
            client = self._connect()
            spreadsheet = client.open_by_url(spreadsheet_url)
            worksheet = spreadsheet.worksheet(worksheet_name)
            
            # Obtener todos los registros
            data = worksheet.get_all_records()
            
            if not data:
                return pd.DataFrame(columns=['ID', 'Categoria', 'Producto', 'Talla', 
                                           'Color', 'Entrada', 'Ventas', 'Stock', 'Precio'])
            
            df = pd.DataFrame(data)
            
            # Asegurar tipos de datos correctos
            numeric_columns = ['Entrada', 'Ventas', 'Stock', 'Precio']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            return df
        
        return _get_data(spreadsheet_url, worksheet_name)
    
    def update_data(self, spreadsheet_url, data, worksheet_name="Inventario"):
        client = self._connect()
        spreadsheet = client.open_by_url(spreadsheet_url)
        worksheet = spreadsheet.worksheet(worksheet_name)
        
        # Convertir DataFrame a lista de listas
        if isinstance(data, pd.DataFrame):
            # Incluir headers
            values = [data.columns.tolist()] + data.fillna('').values.tolist()  
        else:
            values = data
        
        # Actualizar toda la hoja
        worksheet.clear()
        worksheet.update(values, value_input_option='USER_ENTERED')  
        
        return True

# Inicializar conexión
@st.cache_resource
def init_connection():
    return GSheetsConnection("gsheets")

conn = init_connection()

# URL de la hoja de Google Sheets (configurar en secrets)
SPREADSHEET_URL = st.secrets["spreadsheet_url"]

# Función para autenticación
def check_password():
    """Verificar contraseña del administrador"""
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False
    
    if st.session_state.admin_logged_in:
        return True
    
    return False

# Función para login
def login_section():
    """Sección de login para administrador"""
    st.markdown("### 🔒 Acceso Administrador")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        password = st.text_input("Contraseña:", type="password", key="michiotaku")
        login_button = st.button("Ingresar")
        
        if login_button:
            # Hash de la contraseña (en producción usaría algo más seguro como bcrypt)
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            stored_hash = st.secrets.get("admin_password_hash", "")
            
            if hashed_password == stored_hash:
                st.session_state.admin_logged_in = True
                st.success("✅ Acceso concedido")
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")
    
    return False

# Función principal de la aplicación
def main():
    st.title("👔 Inventario Ropa de Caballero")
    st.markdown("---")
    
    try:
        # Cargar datos
        df = conn.get_data(SPREADSHEET_URL)
        
        if df.empty:
            st.warning("⚠️ La base de datos está vacía. Comienza cargando productos en la pestaña de administración.")
            # Crear DataFrame vacío con las columnas correctas
            df = pd.DataFrame(columns=['ID', 'Categoria', 'Producto', 'Talla', 
                                     'Color', 'Entrada', 'Ventas', 'Stock', 'Precio'])
        
    except Exception as e:
        st.error(f"❌ Error al cargar datos: {str(e)}")
        df = pd.DataFrame(columns=['ID', 'Categoria', 'Producto', 'Talla', 
                                 'Color', 'Entrada', 'Ventas', 'Stock', 'Precio'])
    
    # Crear pestañas
    tab1, tab2, tab3 = st.tabs(["🛍️ Registrar Ventas", "📊 Reporte y Caja", "📦 Cargar Mercancía"])
    
    # TAB 1: REGISTRAR VENTAS
    with tab1:
        st.header("Registrar Ventas")
        
        # Buscador
        search_term = st.text_input("🔍 Buscar producto por nombre o modelo:", "")
        
        if search_term:
            filtered_df = df[df['Producto'].str.contains(search_term, case=False, na=False)]
        else:
            filtered_df = df
        
        if filtered_df.empty:
            st.info("No se encontraron productos. Intenta con otro término de búsqueda.")
        else:
            st.write(f"**{len(filtered_df)} productos encontrados**")
            
            for _, row in filtered_df.iterrows():
                with st.expander(f"{row['Producto']} - Talla: {row['Talla']} - Color: {row['Color']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Categoría:** {row['Categoria']}")
                        st.write(f"**Precio:** ${row['Precio']:,.2f}")
                        st.write(f"**Stock disponible:** {int(row['Stock'])}")
                    
                    with col2:
                        st.write(f"**Ventas totales:** {int(row['Ventas'])}")
                        st.write(f"**Última entrada:** {int(row['Entrada'])}")
                    
                    # Botón para registrar venta
                    if st.button("✅ Confirmar Venta", key=f"venta_{row['ID']}"):
                        if row['Stock'] > 0:
                            try:
                                # Actualizar DataFrame
                                idx = df[df['ID'] == row['ID']].index[0]
                                df.at[idx, 'Ventas'] = int(df.at[idx, 'Ventas']) + 1
                                df.at[idx, 'Stock'] = int(df.at[idx, 'Stock']) - 1
                                
                                # Guardar en Google Sheets
                                conn.update_data(SPREADSHEET_URL, df)
                                
                                st.success(f"✅ Venta registrada: {row['Producto']}")
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"❌ Error al registrar venta: {str(e)}")
                        else:
                            st.error("❌ Stock insuficiente")
    
    # TAB 2: REPORTE Y CAJA
    with tab2:
        st.header("Reporte y Caja")
        
        # Botón para forzar actualización
        col1, col2 = st.columns([3,1])
        with col2:
            if st.button("🔄 Actualizar Datos", use_container_width=True):
                cache_data.clear()
                st.rerun()
        
        if not df.empty:
            # Métricas principales
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_ventas = df['Ventas'].sum()
                dinero_caja = (df['Ventas'] * df['Precio']).sum()
                st.metric("💰 Dinero en Caja", f"${dinero_caja:,.2f}")
            
            with col2:
                stock_total = df['Stock'].sum()
                st.metric("📦 Stock Total", f"{int(stock_total)} unidades")
            
            with col3:
                productos_unicos = df['Producto'].nunique()
                st.metric("👔 Productos Únicos", productos_unicos)
            
            # Gráficos
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Ventas por categoría
                ventas_categoria = df.groupby('Categoria')['Ventas'].sum().reset_index()
                if not ventas_categoria.empty:
                    fig1 = px.pie(ventas_categoria, values='Ventas', names='Categoria',
                                title="Ventas por Categoría")
                    st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # Stock por categoría
                stock_categoria = df.groupby('Categoria')['Stock'].sum().reset_index()
                if not stock_categoria.empty:
                    fig2 = px.bar(stock_categoria, x='Categoria', y='Stock',
                                title="Stock por Categoría", color='Categoria')
                    st.plotly_chart(fig2, use_container_width=True)
            
            # DataFrame completo
            st.markdown("### 📋 Base de Datos Completa")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Botón para exportar
            if st.button("📥 Exportar a CSV"):
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Descargar CSV",
                    data=csv,
                    file_name=f"inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No hay datos para mostrar")
    
    # TAB 3: CARGAR MERCANCÍA
    with tab3:
        st.header("Cargar Mercancía")
        
        if not check_password():
            login_section()
        else:
            st.success("✅ Modo administrador activo")
            
            if st.button("🚪 Cerrar Sesión"):
                st.session_state.admin_logged_in = False
                st.rerun()
            
            st.markdown("---")
            
            # Formulario de carga
            with st.form("form_carga"):
                st.subheader("📝 Nuevo Producto")
                
                # Generar ID único
                new_id = f"PROD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Categoría con opción de nueva
                    categorias_existentes = sorted(df['Categoria'].unique().tolist()) if not df.empty else []
                    opciones_categoria = categorias_existentes + ['+ Nueva Categoría']
                    
                    categoria_seleccionada = st.selectbox(
                        "Categoría:",
                        options=opciones_categoria,
                        key="categoria_select"
                    )
                    
                    if categoria_seleccionada == '+ Nueva Categoría':
                        categoria = st.text_input("Nombre de nueva categoría:", key="nueva_categoria")
                    else:
                        categoria = categoria_seleccionada
                    
                    producto = st.text_input("Nombre del Producto:", key="producto")
                    color = st.text_input("Color:", key="color")
                
                with col2:
                    # Tallas dinámicas según categoría
                    if categoria and ('pantalón' in categoria.lower() or 'short' in categoria.lower()):
                        tallas_opciones = ['28', '30', '32', '34', '36', '38', '40', '42']
                    else:
                        tallas_opciones = ['XCH', 'CH', 'M', 'G', 'XG', 'XXG']
                    
                    talla = st.selectbox("Talla:", options=tallas_opciones, key="talla")
                    
                    entrada = st.number_input("Cantidad de Entrada:", min_value=1, value=1, step=1, key="entrada")
                    precio = st.number_input("Precio Unitario ($):", min_value=0.0, value=0.0, step=0.01, key="precio")
                
                # Botón de enviar
                submitted = st.form_submit_button("➕ Agregar al Inventario", use_container_width=True)
                
                if submitted:
                    if not categoria or not producto or not color:
                        st.error("❌ Por favor completa todos los campos obligatorios")
                    else:
                        try:
                            # Crear nuevo registro
                            nuevo_registro = {
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
                            
                            # Agregar al DataFrame
                            nuevo_df = pd.DataFrame([nuevo_registro])
                            df = pd.concat([df, nuevo_df], ignore_index=True)
                            
                            # Guardar en Google Sheets
                            conn.update_data(SPREADSHEET_URL, df)
                            
                            st.success(f"✅ Producto '{producto}' agregado exitosamente!")
                            st.balloons()
                            
                            # Limpiar caché para actualizar datos
                            cache_data.clear()
                            
                        except Exception as e:
                            st.error(f"❌ Error al guardar: {str(e)}")

if __name__ == "__main__":
    main()