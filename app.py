import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os
from streamlit.components.v1 import html

# ============================================
# CONFIGURACIÓN
# ============================================
st.set_page_config(
    page_title="Inventario Ropa Caballero",
    page_icon="👔",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Contraseña
CONTRASENA = "michiotaku"

# Inicializar estados
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False
if 'inventario' not in st.session_state:
    st.session_state.inventario = []
if 'ventas_diarias' not in st.session_state:
    st.session_state.ventas_diarias = []
if 'caja' not in st.session_state:
    st.session_state.caja = 0.0

# Archivo para guardar datos
INVENTARIO_FILE = "inventario_data.json"

# ============================================
# FUNCIONES DE DATOS
# ============================================
def cargar_inventario():
    """Cargar inventario desde archivo"""
    try:
        if os.path.exists(INVENTARIO_FILE):
            with open(INVENTARIO_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                st.session_state.inventario = data.get('inventario', [])
                st.session_state.ventas_diarias = data.get('ventas_diarias', [])
                st.session_state.caja = data.get('caja', 0.0)
    except:
        # Datos de ejemplo iniciales
        st.session_state.inventario = [
            {
                'ID': 'PROD_001',
                'Categoria': 'Camisas',
                'Producto': 'Camisa Casual',
                'Talla': 'M',
                'Color': 'Azul',
                'Entrada': 10,
                'Ventas': 3,
                'Stock': 7,
                'Precio': 25.99
            },
            {
                'ID': 'PROD_002',
                'Categoria': 'Pantalones',
                'Producto': 'Jeans Clásicos',
                'Talla': '32',
                'Color': 'Negro',
                'Entrada': 15,
                'Ventas': 5,
                'Stock': 10,
                'Precio': 34.99
            },
            {
                'ID': 'PROD_003',
                'Categoria': 'Playeras',
                'Producto': 'Polo Sport',
                'Talla': 'G',
                'Color': 'Blanco',
                'Entrada': 20,
                'Ventas': 8,
                'Stock': 12,
                'Precio': 19.99
            }
        ]

def guardar_inventario():
    """Guardar inventario en archivo"""
    try:
        data = {
            'inventario': st.session_state.inventario,
            'ventas_diarias': st.session_state.ventas_diarias,
            'caja': st.session_state.caja,
            'ultima_actualizacion': datetime.now().isoformat()
        }
        with open(INVENTARIO_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

def registrar_venta(producto_id):
    """Registrar una venta"""
    for item in st.session_state.inventario:
        if item['ID'] == producto_id and item['Stock'] > 0:
            item['Ventas'] += 1
            item['Stock'] -= 1
            
            # Registrar venta diaria
            venta = {
                'fecha': datetime.now().isoformat(),
                'producto': item['Producto'],
                'talla': item['Talla'],
                'precio': item['Precio']
            }
            st.session_state.ventas_diarias.append(venta)
            
            # Actualizar caja
            st.session_state.caja += item['Precio']
            
            guardar_inventario()
            return True
    return False

def agregar_producto(nuevo_producto):
    """Agregar nuevo producto al inventario"""
    st.session_state.inventario.append(nuevo_producto)
    guardar_inventario()

# ============================================
# INTERFAZ PRINCIPAL
# ============================================
def main():
    st.title("👔 Inventario Ropa de Caballero")
    st.markdown("---")
    
    # Cargar datos al inicio
    cargar_inventario()
    
    # Convertir a DataFrame
    df = pd.DataFrame(st.session_state.inventario)
    
    # Pestañas
    tab1, tab2, tab3 = st.tabs(["🛍️ Registrar Ventas", "📊 Reporte y Caja", "📦 Cargar Mercancía"])
    
    # TAB 1: REGISTRAR VENTAS
    with tab1:
        st.header("Registrar Ventas")
        
        if df.empty:
            st.info("📭 No hay productos en el inventario. Ve a 'Cargar Mercancía' para agregar productos.")
        else:
            # Buscador
            col1, col2 = st.columns([3, 1])
            with col1:
                search_term = st.text_input("🔍 Buscar producto:", "")
            
            # Filtrar productos
            if search_term:
                filtered_df = df[
                    df['Producto'].str.contains(search_term, case=False, na=False) |
                    df['Categoria'].str.contains(search_term, case=False, na=False) |
                    df['Color'].str.contains(search_term, case=False, na=False)
                ]
            else:
                filtered_df = df
            
            if filtered_df.empty:
                st.info("No se encontraron productos con ese criterio.")
            else:
                st.write(f"**📊 {len(filtered_df)} productos encontrados**")
                
                # Mostrar productos en tarjetas
                cols = st.columns(3)
                for idx, row in filtered_df.iterrows():
                    with cols[idx % 3]:
                        with st.container(border=True):
                            st.markdown(f"### {row['Producto']}")
                            st.markdown(f"**Categoría:** {row['Categoria']}")
                            st.markdown(f"**Talla:** {row['Talla']} | **Color:** {row['Color']}")
                            st.markdown(f"**Precio:** ${row['Precio']:,.2f}")
                            st.markdown(f"**Stock disponible:** {int(row['Stock'])}")
                            
                            if row['Stock'] > 0:
                                if st.button("✅ Vender", key=f"vender_{row['ID']}", use_container_width=True):
                                    if registrar_venta(row['ID']):
                                        st.success(f"✅ Vendido: {row['Producto']}")
                                        st.rerun()
                                    else:
                                        st.error("Error al registrar venta")
                            else:
                                st.error("❌ Sin stock", icon="⚠️")
    
    # TAB 2: REPORTE Y CAJA
    with tab2:
        st.header("📊 Reporte y Caja")
        
        if df.empty:
            st.info("No hay datos para mostrar. Agrega productos primero.")
        else:
            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_ventas = df['Ventas'].sum()
                st.metric("📈 Ventas Totales", f"{int(total_ventas)}")
            
            with col2:
                dinero_caja = st.session_state.caja
                st.metric("💰 Caja Total", f"${dinero_caja:,.2f}")
            
            with col3:
                stock_total = df['Stock'].sum()
                st.metric("📦 Stock Total", f"{int(stock_total)}")
            
            with col4:
                productos_unicos = df['Producto'].nunique()
                st.metric("👔 Productos", f"{productos_unicos}")
            
            st.markdown("---")
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                if not df.empty and 'Categoria' in df.columns:
                    ventas_por_categoria = df.groupby('Categoria')['Ventas'].sum().reset_index()
                    if not ventas_por_categoria.empty:
                        fig = px.pie(
                            ventas_por_categoria, 
                            values='Ventas', 
                            names='Categoria',
                            title="📊 Ventas por Categoría",
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if not df.empty and 'Categoria' in df.columns:
                    stock_por_categoria = df.groupby('Categoria')['Stock'].sum().reset_index()
                    if not stock_por_categoria.empty:
                        fig = px.bar(
                            stock_por_categoria,
                            x='Categoria',
                            y='Stock',
                            title="📦 Stock por Categoría",
                            color='Categoria',
                            text='Stock'
                        )
                        fig.update_traces(textposition='outside')
                        st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Tabla completa
            st.subheader("📋 Inventario Completo")
            
            # Opciones de visualización
            view_col1, view_col2 = st.columns([1, 3])
            with view_col1:
                mostrar_todo = st.checkbox("Mostrar todo el inventario", value=True)
            
            if mostrar_todo:
                # Formatear DataFrame para mostrar
                display_df = df.copy()
                display_df['Precio'] = display_df['Precio'].apply(lambda x: f"${x:,.2f}")
                display_df = display_df[['Categoria', 'Producto', 'Talla', 'Color', 'Stock', 'Ventas', 'Precio']]
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'Categoria': st.column_config.TextColumn("Categoría"),
                        'Producto': st.column_config.TextColumn("Producto"),
                        'Talla': st.column_config.TextColumn("Talla"),
                        'Color': st.column_config.TextColumn("Color"),
                        'Stock': st.column_config.NumberColumn("Stock", format="%d"),
                        'Ventas': st.column_config.NumberColumn("Ventas", format="%d"),
                        'Precio': st.column_config.TextColumn("Precio")
                    }
                )
            
            # Botones de exportación
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                if st.button("📥 Exportar a CSV", use_container_width=True):
                    csv = df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="Descargar CSV",
                        data=csv,
                        file_name=f"inventario_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            with col_exp2:
                if st.button("🔄 Reiniciar Caja", use_container_width=True):
                    st.session_state.caja = 0.0
                    guardar_inventario()
                    st.success("Caja reiniciada")
                    st.rerun()
    
    # TAB 3: CARGAR MERCANCÍA
    with tab3:
        st.header("📦 Cargar Mercancía")
        
        # Verificar login
        if not st.session_state.admin_logged_in:
            st.markdown("### 🔒 Acceso Administrador")
            
            with st.container(border=True):
                password = st.text_input("Contraseña:", type="password", key="password_input")
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("🔑 Ingresar", type="primary", use_container_width=True):
                        if password == CONTRASENA:
                            st.session_state.admin_logged_in = True
                            st.success("✅ Acceso concedido")
                            st.rerun()
                        else:
                            st.error("❌ Contraseña incorrecta")
            
            # Información
            with st.expander("ℹ️ Información"):
                st.info("""
                **Para acceder al modo administrador:**
                - Usa la contraseña establecida
                - Podrás agregar nuevos productos al inventario
                - Solo personal autorizado
                """)
            
        else:
            # Mostrar controles de administrador
            st.success("✅ **Modo administrador activado**")
            
            if st.button("🚪 Cerrar Sesión", use_container_width=True):
                st.session_state.admin_logged_in = False
                st.rerun()
            
            st.markdown("---")
            
            # Formulario para agregar producto
            with st.form("form_nuevo_producto", clear_on_submit=True):
                st.subheader("📝 Agregar Nuevo Producto")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    categoria = st.selectbox(
                        "Categoría:",
                        ['Camisas', 'Pantalones', 'Playeras', 'Shorts', 'Suéteres', 'Chaquetas', 'Accesorios']
                    )
                    
                    producto = st.text_input("Nombre del Producto:")
                    
                    color = st.text_input("Color:")
                
                with col2:
                    # Tallas según categoría
                    if categoria in ['Pantalones', 'Shorts']:
                        tallas = ['28', '30', '32', '34', '36', '38', '40']
                    else:
                        tallas = ['XCH', 'CH', 'M', 'G', 'XG', 'XXG']
                    
                    talla = st.selectbox("Talla:", tallas)
                    
                    cantidad = st.number_input("Cantidad:", min_value=1, value=1, step=1)
                    
                    precio = st.number_input("Precio ($):", min_value=0.0, value=0.0, step=0.01, format="%.2f")
                
                # Botón de envío
                submitted = st.form_submit_button("➕ Agregar al Inventario", type="primary", use_container_width=True)
                
                if submitted:
                    if not producto or not color:
                        st.error("❌ Por favor, completa todos los campos obligatorios")
                    else:
                        # Crear nuevo producto
                        nuevo_id = f"PROD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        
                        nuevo_producto = {
                            'ID': nuevo_id,
                            'Categoria': categoria,
                            'Producto': producto,
                            'Talla': talla,
                            'Color': color,
                            'Entrada': cantidad,
                            'Ventas': 0,
                            'Stock': cantidad,
                            'Precio': float(precio)
                        }
                        
                        # Agregar al inventario
                        agregar_producto(nuevo_producto)
                        
                        st.success(f"✅ **{producto}** agregado al inventario exitosamente!")
                        st.balloons()
            
            # Vista rápida del inventario actual
            st.markdown("---")
            st.subheader("📋 Inventario Actual")
            
            if df.empty:
                st.info("No hay productos en el inventario.")
            else:
                # Mostrar resumen
                resumen_df = df[['Categoria', 'Producto', 'Talla', 'Stock']].head(10)
                st.dataframe(resumen_df, use_container_width=True, hide_index=True)
                
                if len(df) > 10:
                    st.caption(f"Mostrando 10 de {len(df)} productos. Ve a 'Reporte y Caja' para ver todo.")

# ============================================
# EJECUCIÓN
# ============================================
if __name__ == "__main__":
    main()