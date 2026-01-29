import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os

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

# Configuración inicial de categorías y tallas
if 'categorias_personalizadas' not in st.session_state:
    st.session_state.categorias_personalizadas = []

if 'config_tallas' not in st.session_state:
    st.session_state.config_tallas = {
        'superior': ['Unitalla', 'XCH', 'CH', 'M', 'G', 'XG', 'XXG'],
        'inferior': ['Unitalla', '28', '30', '32', '34', '36', '38', '40', '42'],
        'accesorios': ['Unitalla'],
        'personalizado': ['Unitalla']
    }

# Categorías base (no editables)
CATEGORIAS_BASE = {
    'superior': ['Camisas', 'Playeras', 'Suéteres', 'Chaquetas', 'Camisetas', 'Polos'],
    'inferior': ['Pantalones', 'Shorts', 'Jeans', 'Bermudas'],
    'accesorios': ['Cinturones', 'Gorras', 'Medias', 'Bufandas']
}

# Obtener todas las categorías disponibles
def obtener_todas_categorias():
    todas = []
    for tipo in CATEGORIAS_BASE:
        todas.extend(CATEGORIAS_BASE[tipo])
    todas.extend(st.session_state.categorias_personalizadas)
    return sorted(list(set(todas)))

# Determinar tipo de categoría
def obtener_tipo_categoria(categoria):
    """Determina si la categoría es superior, inferior, accesorio o personalizado"""
    for tipo, categorias in CATEGORIAS_BASE.items():
        if categoria in categorias:
            return tipo
    return 'personalizado'

# Obtener tallas disponibles para una categoría
def obtener_tallas_disponibles(categoria):
    """Obtiene las tallas disponibles para una categoría"""
    tipo = obtener_tipo_categoria(categoria)
    return st.session_state.config_tallas.get(tipo, ['Unitalla'])

# Inicializar estados
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False
if 'inventario' not in st.session_state:
    st.session_state.inventario = []
if 'ventas_diarias' not in st.session_state:
    st.session_state.ventas_diarias = []
if 'caja' not in st.session_state:
    st.session_state.caja = 0.0
if 'modo_edicion' not in st.session_state:
    st.session_state.modo_edicion = None
if 'producto_editar' not in st.session_state:
    st.session_state.producto_editar = None
if 'mostrar_gestion_categorias' not in st.session_state:
    st.session_state.mostrar_gestion_categorias = False

# Archivo para guardar datos
INVENTARIO_FILE = "inventario_data.json"
CATEGORIAS_FILE = "categorias_data.json"

# ============================================
# FUNCIONES DE DATOS
# ============================================
def cargar_datos():
    """Cargar todos los datos desde archivos"""
    # Cargar inventario
    try:
        if os.path.exists(INVENTARIO_FILE):
            with open(INVENTARIO_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                st.session_state.inventario = data.get('inventario', [])
                st.session_state.ventas_diarias = data.get('ventas_diarias', [])
                st.session_state.caja = data.get('caja', 0.0)
    except:
        st.session_state.inventario = []
        st.session_state.ventas_diarias = []
        st.session_state.caja = 0.0
    
    # Cargar categorías personalizadas
    try:
        if os.path.exists(CATEGORIAS_FILE):
            with open(CATEGORIAS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                st.session_state.categorias_personalizadas = data.get('categorias_personalizadas', [])
    except:
        st.session_state.categorias_personalizadas = []

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
    except Exception as e:
        st.error(f"Error al guardar inventario: {str(e)}")

def guardar_categorias():
    """Guardar categorías personalizadas en archivo"""
    try:
        data = {
            'categorias_personalizadas': st.session_state.categorias_personalizadas,
            'ultima_actualizacion': datetime.now().isoformat()
        }
        with open(CATEGORIAS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Error al guardar categorías: {str(e)}")

def agregar_categoria_personalizada(nueva_categoria):
    """Agregar una nueva categoría personalizada"""
    if nueva_categoria and nueva_categoria not in obtener_todas_categorias():
        st.session_state.categorias_personalizadas.append(nueva_categoria)
        guardar_categorias()
        return True
    return False

def eliminar_categoria_personalizada(categoria):
    """Eliminar una categoría personalizada"""
    if categoria in st.session_state.categorias_personalizadas:
        # Verificar que no haya productos usando esta categoría
        productos_en_categoria = [p for p in st.session_state.inventario if p['Categoria'] == categoria]
        
        if productos_en_categoria:
            return False, f"No se puede eliminar. Hay {len(productos_en_categoria)} productos usando esta categoría."
        
        st.session_state.categorias_personalizadas.remove(categoria)
        guardar_categorias()
        return True, f"Categoría '{categoria}' eliminada correctamente"
    
    return False, "Categoría no encontrada"

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
                'precio': item['Precio'],
                'categoria': item['Categoria']
            }
            st.session_state.ventas_diarias.append(venta)
            
            # Actualizar caja
            st.session_state.caja += item['Precio']
            
            guardar_inventario()
            return True
    return False

def agregar_producto(nuevo_producto):
    """Agregar nuevo producto al inventario"""
    # Agregar tipo de categoría
    nuevo_producto['Tipo'] = obtener_tipo_categoria(nuevo_producto['Categoria'])
    st.session_state.inventario.append(nuevo_producto)
    guardar_inventario()
    return True

def editar_producto(producto_id, datos_actualizados):
    """Editar un producto existente"""
    for i, item in enumerate(st.session_state.inventario):
        if item['ID'] == producto_id:
            # Preservar ventas y calcular nuevo stock
            ventas_actuales = item['Ventas']
            nuevo_stock = datos_actualizados['Entrada'] - ventas_actuales
            
            if nuevo_stock < 0:
                return False, "No puedes reducir la cantidad por debajo de las ventas realizadas"
            
            datos_actualizados['Ventas'] = ventas_actuales
            datos_actualizados['Stock'] = nuevo_stock
            datos_actualizados['ID'] = producto_id
            datos_actualizados['Tipo'] = obtener_tipo_categoria(datos_actualizados['Categoria'])
            
            st.session_state.inventario[i] = datos_actualizados
            guardar_inventario()
            return True, "Producto actualizado correctamente"
    
    return False, "Producto no encontrado"

def eliminar_producto(producto_id):
    """Eliminar un producto del inventario"""
    for i, item in enumerate(st.session_state.inventario):
        if item['ID'] == producto_id:
            # Verificar si tiene ventas
            if item['Ventas'] > 0:
                return False, "No se puede eliminar un producto con ventas registradas"
            
            # Eliminar producto
            producto_eliminado = st.session_state.inventario.pop(i)
            guardar_inventario()
            return True, f"Producto '{producto_eliminado['Producto']}' eliminado correctamente"
    
    return False, "Producto no encontrado"

def ajustar_stock(producto_id, nueva_cantidad):
    """Ajustar el stock de un producto"""
    for item in st.session_state.inventario:
        if item['ID'] == producto_id:
            if nueva_cantidad < item['Ventas']:
                return False, f"El stock no puede ser menor a las ventas ({item['Ventas']})"
            
            item['Entrada'] = nueva_cantidad
            item['Stock'] = nueva_cantidad - item['Ventas']
            guardar_inventario()
            return True, f"Stock ajustado a {nueva_cantidad} unidades"
    return False, "Producto no encontrado"

# ============================================
# INTERFAZ PRINCIPAL - CORREGIDA
# ============================================
def main():
    st.title("👔 Inventario Ropa de Caballero")
    
    # Cargar todos los datos
    cargar_datos()
    
    # Información de tallas
    with st.expander("ℹ️ Guía de Tallas y Categorías", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 🔝 Parte Superior")
            st.write("**Categorías base:** Camisas, Playeras, Suéteres, Chaquetas")
            st.write("**Tallas disponibles:** Unitalla, XCH, CH, M, G, XG, XXG")
        with col2:
            st.markdown("### 👖 Parte Inferior")
            st.write("**Categorías base:** Pantalones, Shorts, Jeans, Bermudas")
            st.write("**Tallas disponibles:** Unitalla, 28, 30, 32, 34, 36, 38, 40, 42")
        with col3:
            st.markdown("### 🎽 Accesorios y Personalizadas")
            st.write("**Categorías base:** Cinturones, Gorras, Medias, Bufandas")
            st.write("**Talla:** Unitalla (puedes agregar más categorías)")
    
    st.markdown("---")
    
    # Convertir a DataFrame y asegurar columna 'Tipo'
    inventario_con_tipo = []
    for item in st.session_state.inventario:
        if 'Tipo' not in item:
            item['Tipo'] = obtener_tipo_categoria(item.get('Categoria', ''))
        inventario_con_tipo.append(item)
    
    st.session_state.inventario = inventario_con_tipo
    df = pd.DataFrame(st.session_state.inventario)
    
    # Pestañas
    tab1, tab2, tab3 = st.tabs(["🛍️ Registrar Ventas", "📊 Reporte y Caja", "⚙️ Gestión Inventario"])
    
    # TAB 1: REGISTRAR VENTAS - CORREGIDA
    with tab1:
        st.header("Registrar Ventas")
        
        if df.empty:
            st.info("📭 No hay productos en el inventario. Ve a 'Gestión Inventario' para agregar productos.")
        else:
            # Filtros por tipo
            col_filt1, col_filt2, col_filt3 = st.columns(3)
            with col_filt1:
                todas_categorias = obtener_todas_categorias()
                categoria_filtro = st.selectbox("Filtrar por categoría:", 
                                              ['Todas'] + sorted(todas_categorias))
            with col_filt2:
                filtrar_tipo = st.selectbox("Filtrar por tipo:", 
                                          ['Todos', 'Parte Superior', 'Parte Inferior', 'Accesorios', 'Personalizado'])
            with col_filt3:
                search_term = st.text_input("🔍 Buscar producto:", "", key="search_ventas")
            
            # Aplicar filtros - CORRECCIÓN: Manejar DataFrame vacío
            filtered_df = df.copy()
            
            if not df.empty:
                if categoria_filtro != 'Todas':
                    filtered_df = filtered_df[filtered_df['Categoria'] == categoria_filtro]
                
                if filtrar_tipo != 'Todos':
                    tipo_map = {
                        'Parte Superior': 'superior',
                        'Parte Inferior': 'inferior', 
                        'Accesorios': 'accesorios',
                        'Personalizado': 'personalizado'
                    }
                    if filtrar_tipo in tipo_map:
                        filtered_df = filtered_df[filtered_df['Tipo'] == tipo_map[filtrar_tipo]]
                
                if search_term:
                    filtered_df = filtered_df[
                        filtered_df['Producto'].str.contains(search_term, case=False, na=False) |
                        filtered_df['Categoria'].str.contains(search_term, case=False, na=False) |
                        filtered_df['Color'].str.contains(search_term, case=False, na=False) |
                        filtered_df['Talla'].str.contains(search_term, case=False, na=False)
                    ]
            
            if filtered_df.empty:
                st.info("No se encontraron productos con ese criterio.")
            else:
                st.write(f"**📊 {len(filtered_df)} productos encontrados**")
                
                # Verificar si tiene columna 'Tipo' - CORRECCIÓN
                if 'Tipo' in filtered_df.columns:
                    tipos = filtered_df['Tipo'].unique()
                else:
                    # Si no tiene columna Tipo, agrupar por categoría
                    tipos = filtered_df['Categoria'].unique()
                
                for tipo in tipos:
                    if 'Tipo' in filtered_df.columns:
                        productos_tipo = filtered_df[filtered_df['Tipo'] == tipo]
                    else:
                        productos_tipo = filtered_df[filtered_df['Categoria'] == tipo]
                    
                    # Título según tipo
                    titulo_map = {
                        'superior': '🔝 Parte Superior',
                        'inferior': '👖 Parte Inferior',
                        'accesorios': '🎽 Accesorios',
                        'personalizado': '📌 Categorías Personalizadas'
                    }
                    
                    if tipo in titulo_map:
                        st.markdown(f"### {titulo_map[tipo]}")
                    else:
                        st.markdown(f"### 📦 {tipo}")
                    
                    # Mostrar en columnas - máximo 3 columnas
                    num_productos = len(productos_tipo)
                    if num_productos == 0:
                        continue
                    
                    # Crear columnas dinámicamente
                    num_cols = min(3, num_productos)
                    cols = st.columns(num_cols)
                    
                    for idx, (_, row) in enumerate(productos_tipo.iterrows()):
                        with cols[idx % num_cols]:
                            with st.container(border=True):
                                # Icono según tipo
                                if 'Tipo' in row:
                                    icono_map = {
                                        'superior': '👕',
                                        'inferior': '👖',
                                        'accesorios': '🧦',
                                        'personalizado': '📌'
                                    }
                                    icono = icono_map.get(row['Tipo'], '📦')
                                else:
                                    icono = '📦'
                                
                                st.markdown(f"### {icono} {row['Producto']}")
                                st.markdown(f"**Categoría:** {row['Categoria']}")
                                st.markdown(f"**Talla:** {row['Talla']} | **Color:** {row['Color']}")
                                st.markdown(f"**Precio:** ${row['Precio']:,.2f}")
                                
                                # Barra de stock con manejo de división por cero
                                entrada = row['Entrada'] if 'Entrada' in row else 1
                                stock = row['Stock'] if 'Stock' in row else 0
                                
                                if entrada > 0:
                                    porcentaje_stock = (stock / entrada) * 100
                                    color_barra = "green" if porcentaje_stock > 50 else "orange" if porcentaje_stock > 20 else "red"
                                    st.progress(int(porcentaje_stock), 
                                              text=f"Stock: {int(stock)}/{int(entrada)}")
                                else:
                                    st.progress(0, text=f"Stock: {int(stock)}/0")
                                
                                if stock > 0:
                                    if st.button("✅ Vender", key=f"vender_{row['ID']}", use_container_width=True):
                                        if registrar_venta(row['ID']):
                                            st.success(f"✅ Vendido: {row['Producto']}")
                                            st.rerun()
                                        else:
                                            st.error("Error al registrar venta")
                                else:
                                    st.error("❌ Sin stock", icon="⚠️")
    
    # TAB 2: REPORTE Y CAJA - CORREGIDA
    with tab2:
        st.header("📊 Reporte y Caja")
        
        if df.empty:
            st.info("No hay datos para mostrar. Agrega productos primero.")
        else:
            # Asegurar que el DataFrame tenga las columnas necesarias
            if 'Ventas' not in df.columns:
                df['Ventas'] = 0
            if 'Stock' not in df.columns:
                df['Stock'] = 0
            if 'Precio' not in df.columns:
                df['Precio'] = 0.0
            if 'Tipo' not in df.columns:
                df['Tipo'] = df['Categoria'].apply(obtener_tipo_categoria)
            
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
            
            # Estadísticas por tipo - Solo si hay columna 'Tipo'
            if 'Tipo' in df.columns:
                st.subheader("📈 Estadísticas por Tipo de Prenda")
                
                tipo_map_display = {
                    'superior': '🔝 Parte Superior',
                    'inferior': '👖 Parte Inferior',
                    'accesorios': '🎽 Accesorios',
                    'personalizado': '📌 Personalizado'
                }
                
                tipos_presentes = df['Tipo'].unique()
                if len(tipos_presentes) > 0:
                    cols_tipos = st.columns(len(tipos_presentes))
                    
                    for idx, tipo in enumerate(tipos_presentes):
                        with cols_tipos[idx]:
                            ventas_tipo = df[df['Tipo'] == tipo]['Ventas'].sum()
                            display_name = tipo_map_display.get(tipo, tipo)
                            st.metric(display_name, f"{int(ventas_tipo)} ventas")
            
            st.markdown("---")
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                if not df.empty and 'Tipo' in df.columns:
                    ventas_por_tipo = df.groupby('Tipo')['Ventas'].sum().reset_index()
                    if not ventas_por_tipo.empty and len(ventas_por_tipo) > 0:
                        # Traducir tipos para el gráfico
                        ventas_por_tipo['Tipo'] = ventas_por_tipo['Tipo'].map(tipo_map_display)
                        ventas_por_tipo = ventas_por_tipo.dropna()  # Eliminar NaN
                        
                        if not ventas_por_tipo.empty:
                            fig = px.pie(
                                ventas_por_tipo, 
                                values='Ventas', 
                                names='Tipo',
                                title="📊 Ventas por Tipo de Prenda",
                                color_discrete_sequence=px.colors.qualitative.Set3
                            )
                            fig.update_traces(textposition='inside', textinfo='percent+label')
                            st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if not df.empty and 'Categoria' in df.columns:
                    ventas_por_categoria = df.groupby('Categoria')['Ventas'].sum().reset_index()
                    if not ventas_por_categoria.empty:
                        # Tomar solo las top 10 categorías para el gráfico
                        ventas_por_categoria = ventas_por_categoria.sort_values('Ventas', ascending=False).head(10)
                        
                        if not ventas_por_categoria.empty:
                            fig = px.bar(
                                ventas_por_categoria,
                                x='Categoria',
                                y='Ventas',
                                title="🏆 Top 10 Categorías por Ventas",
                                color='Ventas',
                                text='Ventas'
                            )
                            fig.update_traces(textposition='outside')
                            fig.update_layout(xaxis_tickangle=-45)
                            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Tabla completa con filtros
            st.subheader("📋 Inventario Completo")
            
            # Filtros para la tabla
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                # Opciones de filtro de tipo
                opciones_tipo = ['Todos']
                if 'Tipo' in df.columns:
                    tipos_unicos = sorted(df['Tipo'].unique())
                    for t in tipos_unicos:
                        display_name = tipo_map_display.get(t, t)
                        opciones_tipo.append(display_name)
                
                filtro_tipo_tabla = st.selectbox("Tipo:", opciones_tipo, key="filtro_tipo_tabla")
            
            with col_f2:
                todas_categorias_tabla = ['Todas'] + sorted(df['Categoria'].unique().tolist())
                filtro_categoria = st.selectbox("Categoría:", todas_categorias_tabla, key="filtro_categoria")
            
            with col_f3:
                ordenar_por = st.selectbox("Ordenar por:", ['Producto', 'Stock', 'Ventas', 'Precio'], key="ordenar_por")
            
            # Aplicar filtros a la tabla
            display_df = df.copy()
            
            if filtro_tipo_tabla != 'Todos' and 'Tipo' in display_df.columns:
                # Convertir display name back to tipo
                tipo_reverse_map = {v: k for k, v in tipo_map_display.items()}
                tipo_filtro = tipo_reverse_map.get(filtro_tipo_tabla, filtro_tipo_tabla)
                display_df = display_df[display_df['Tipo'] == tipo_filtro]
            
            if filtro_categoria != 'Todas':
                display_df = display_df[display_df['Categoria'] == filtro_categoria]
            
            # Ordenar
            if ordenar_por == 'Stock':
                display_df = display_df.sort_values('Stock', ascending=False)
            elif ordenar_por == 'Ventas':
                display_df = display_df.sort_values('Ventas', ascending=False)
            elif ordenar_por == 'Precio':
                display_df = display_df.sort_values('Precio', ascending=False)
            else:
                display_df = display_df.sort_values('Producto')
            
            # Mostrar tabla formateada
            if not display_df.empty:
                display_df_formatted = display_df.copy()
                display_df_formatted['Precio'] = display_df_formatted['Precio'].apply(lambda x: f"${x:,.2f}")
                
                if 'Tipo' in display_df_formatted.columns:
                    display_df_formatted['Tipo'] = display_df_formatted['Tipo'].map(tipo_map_display)
                
                columnas_disponibles = []
                columnas_posibles = ['Tipo', 'Categoria', 'Producto', 'Talla', 'Color', 'Stock', 'Ventas', 'Precio']
                
                for col in columnas_posibles:
                    if col in display_df_formatted.columns:
                        columnas_disponibles.append(col)
                
                st.dataframe(
                    display_df_formatted[columnas_disponibles],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'Tipo': st.column_config.TextColumn("Tipo"),
                        'Categoria': st.column_config.TextColumn("Categoría"),
                        'Producto': st.column_config.TextColumn("Producto"),
                        'Talla': st.column_config.TextColumn("Talla"),
                        'Color': st.column_config.TextColumn("Color"),
                        'Stock': st.column_config.NumberColumn("Stock", format="%d"),
                        'Ventas': st.column_config.NumberColumn("Ventas", format="%d"),
                        'Precio': st.column_config.TextColumn("Precio")
                    }
                )
            else:
                st.info("No hay productos que coincidan con los filtros seleccionados.")
            
            # Botones de exportación
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                if st.button("📥 Exportar a CSV", use_container_width=True, key="export_csv"):
                    csv = df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="Descargar CSV",
                        data=csv,
                        file_name=f"inventario_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="download_csv"
                    )
            
            with col_exp2:
                if st.button("🔄 Reiniciar Caja", use_container_width=True, key="reset_caja"):
                    st.session_state.caja = 0.0
                    guardar_inventario()
                    st.success("Caja reiniciada")
                    st.rerun()
    
    # TAB 3: GESTIÓN INVENTARIO - CORREGIDA
    with tab3:
        st.header("⚙️ Gestión de Inventario")
        
        # Verificar login
        if not st.session_state.admin_logged_in:
            st.markdown("### 🔒 Acceso Administrador")
            
            with st.container(border=True):
                password = st.text_input("Contraseña:", type="password", key="password_input_admin")
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("🔑 Ingresar", type="primary", use_container_width=True, key="login_admin"):
                        if password == CONTRASENA:
                            st.session_state.admin_logged_in = True
                            st.success("✅ Acceso concedido")
                            st.rerun()
                        else:
                            st.error("❌ Contraseña incorrecta")
        else:
            # Mostrar controles de administrador
            st.success("✅ **Modo administrador activado**")
            
            # Botón para gestionar categorías
            col_logout, col_cats, col_space = st.columns([1, 1, 2])
            with col_logout:
                if st.button("🚪 Cerrar Sesión", use_container_width=True, key="logout_admin"):
                    st.session_state.admin_logged_in = False
                    st.session_state.modo_edicion = None
                    st.session_state.producto_editar = None
                    st.session_state.mostrar_gestion_categorias = False
                    st.rerun()
            
            with col_cats:
                if st.button("🏷️ Gestionar Categorías", use_container_width=True, 
                           type="primary" if st.session_state.mostrar_gestion_categorias else "secondary"):
                    st.session_state.mostrar_gestion_categorias = not st.session_state.mostrar_gestion_categorias
                    st.session_state.modo_edicion = None
                    st.rerun()
            
            st.markdown("---")
            
            # PANEL DE GESTIÓN DE CATEGORÍAS
            if st.session_state.mostrar_gestion_categorias:
                st.subheader("🏷️ Gestión de Categorías Personalizadas")
                
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    with st.container(border=True):
                        st.markdown("### 📋 Categorías Existentes")
                        todas_categorias = obtener_todas_categorias()
                        
                        st.write("**Categorías base (no editables):**")
                        for tipo in ['superior', 'inferior', 'accesorios']:
                            st.write(f"- **{tipo.title()}:** {', '.join(CATEGORIAS_BASE[tipo])}")
                        
                        if st.session_state.categorias_personalizadas:
                            st.write("\n**Categorías personalizadas:**")
                            for cat in st.session_state.categorias_personalizadas:
                                st.write(f"- 📌 {cat}")
                        else:
                            st.info("No hay categorías personalizadas aún.")
                
                with col_info2:
                    with st.container(border=True):
                        st.markdown("### ➕ Agregar Nueva Categoría")
                        
                        nueva_categoria = st.text_input("Nombre de la nueva categoría:", 
                                                      placeholder="Ej: Sudaderas, Trajes, Chalecos...")
                        
                        if st.button("➕ Agregar Categoría", use_container_width=True):
                            if nueva_categoria:
                                if agregar_categoria_personalizada(nueva_categoria):
                                    st.success(f"✅ Categoría '{nueva_categoria}' agregada exitosamente!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ La categoría '{nueva_categoria}' ya existe.")
                            else:
                                st.error("❌ Por favor ingresa un nombre para la categoría.")
                        
                        st.markdown("---")
                        
                        st.markdown("### 🗑️ Eliminar Categoría Personalizada")
                        
                        if st.session_state.categorias_personalizadas:
                            cat_a_eliminar = st.selectbox(
                                "Selecciona categoría a eliminar:",
                                st.session_state.categorias_personalizadas,
                                key="select_cat_eliminar"
                            )
                            
                            if st.button("🗑️ Eliminar Categoría", use_container_width=True, type="secondary"):
                                success, message = eliminar_categoria_personalizada(cat_a_eliminar)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                        else:
                            st.info("No hay categorías personalizadas para eliminar.")
                
                st.markdown("---")
                if st.button("⬅️ Volver a Gestión de Productos", use_container_width=True):
                    st.session_state.mostrar_gestion_categorias = False
                    st.rerun()
                
            else:
                # Selección de modo
                st.subheader("📋 Acciones Disponibles")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("➕ Agregar Producto", use_container_width=True, 
                               type="primary" if st.session_state.modo_edicion == 'agregar' else "secondary"):
                        st.session_state.modo_edicion = 'agregar'
                        st.session_state.producto_editar = None
                        st.rerun()
                
                with col2:
                    if st.button("✏️ Editar Producto", use_container_width=True,
                               type="primary" if st.session_state.modo_edicion == 'editar' else "secondary"):
                        st.session_state.modo_edicion = 'editar'
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ Eliminar Producto", use_container_width=True,
                               type="primary" if st.session_state.modo_edicion == 'eliminar' else "secondary"):
                        st.session_state.modo_edicion = 'eliminar'
                        st.rerun()
                
                with col4:
                    if st.button("📊 Ver Inventario", use_container_width=True,
                               type="primary" if st.session_state.modo_edicion is None else "secondary"):
                        st.session_state.modo_edicion = None
                        st.rerun()
                
                st.markdown("---")
                
                # MODO: AGREGAR PRODUCTO
                if st.session_state.modo_edicion == 'agregar':
                    st.subheader("📝 Agregar Nuevo Producto")
                    
                    with st.form("form_agregar_producto", clear_on_submit=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Obtener todas las categorías disponibles
                            todas_categorias = obtener_todas_categorias()
                            
                            categoria = st.selectbox(
                                "Categoría:",
                                todas_categorias,
                                key="cat_agregar"
                            )
                            
                            producto = st.text_input("Nombre del Producto:", key="prod_agregar")
                            
                            color = st.text_input("Color:", key="color_agregar")
                        
                        with col2:
                            # Obtener tallas según categoría seleccionada
                            tallas_disponibles = obtener_tallas_disponibles(categoria)
                            
                            talla = st.selectbox("Talla:", tallas_disponibles, key="talla_agregar")
                            
                            cantidad = st.number_input("Cantidad inicial:", min_value=1, value=1, step=1, key="cant_agregar")
                            
                            precio = st.number_input("Precio ($):", min_value=0.0, value=0.0, step=0.01, 
                                                   format="%.2f", key="precio_agregar")
                        
                        # Información de tipo de talla
                        tipo_cat = obtener_tipo_categoria(categoria)
                        if tipo_cat == 'superior':
                            st.info("🔝 **Parte Superior**: Unitalla, XCH, CH, M, G, XG, XXG")
                        elif tipo_cat == 'inferior':
                            st.info("👖 **Parte Inferior**: Unitalla, 28, 30, 32, 34, 36, 38, 40, 42")
                        elif tipo_cat == 'accesorios':
                            st.info("🎽 **Accesorio**: Unitalla")
                        else:
                            st.info("📌 **Categoría Personalizada**: Unitalla (talla única)")
                        
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
                                    'Precio': float(precio),
                                    'Tipo': tipo_cat
                                }
                                
                                # Agregar al inventario
                                if agregar_producto(nuevo_producto):
                                    st.success(f"✅ **{producto}** agregado al inventario exitosamente!")
                                    st.balloons()
                                    st.session_state.modo_edicion = None
                
                # MODO: EDITAR PRODUCTO
                elif st.session_state.modo_edicion == 'editar':
                    st.subheader("✏️ Editar Producto Existente")
                    
                    if df.empty:
                        st.info("No hay productos para editar.")
                    else:
                        # Lista de productos para seleccionar
                        productos_opciones = {f"{row['Producto']} ({row['Talla']}, {row['Color']})": row['ID'] 
                                            for _, row in df.iterrows()}
                        
                        producto_seleccionado = st.selectbox(
                            "Selecciona un producto para editar:",
                            list(productos_opciones.keys()),
                            key="select_editar"
                        )
                        
                        if producto_seleccionado:
                            producto_id = productos_opciones[producto_seleccionado]
                            producto_data = next((item for item in st.session_state.inventario 
                                                if item['ID'] == producto_id), None)
                            
                            if producto_data:
                                with st.form("form_editar_producto"):
                                    st.write(f"**Editando:** {producto_data['Producto']}")
                                    
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        todas_categorias = obtener_todas_categorias()
                                        
                                        nueva_categoria = st.selectbox(
                                            "Categoría:",
                                            todas_categorias,
                                            index=todas_categorias.index(producto_data['Categoria']) 
                                            if producto_data['Categoria'] in todas_categorias else 0,
                                            key="cat_editar"
                                        )
                                        
                                        nuevo_producto = st.text_input("Nombre del Producto:", 
                                                                      value=producto_data['Producto'],
                                                                      key="prod_editar")
                                        
                                        nuevo_color = st.text_input("Color:", 
                                                                  value=producto_data['Color'],
                                                                  key="color_editar")
                                    
                                    with col2:
                                        # Obtener tallas según nueva categoría
                                        tallas_disponibles = obtener_tallas_disponibles(nueva_categoria)
                                        
                                        # Encontrar índice de la talla actual
                                        try:
                                            idx_talla = tallas_disponibles.index(producto_data['Talla'])
                                        except ValueError:
                                            idx_talla = 0
                                        
                                        nueva_talla = st.selectbox("Talla:", tallas_disponibles, 
                                                                 index=idx_talla,
                                                                 key="talla_editar")
                                        
                                        nueva_cantidad = st.number_input("Cantidad total:", 
                                                                        min_value=1, 
                                                                        value=int(producto_data['Entrada']),
                                                                        step=1,
                                                                        key="cant_editar")
                                        
                                        nuevo_precio = st.number_input("Precio ($):", 
                                                                     min_value=0.0, 
                                                                     value=float(producto_data['Precio']),
                                                                     step=0.01,
                                                                     format="%.2f",
                                                                     key="precio_editar")
                                    
                                    # Mostrar información del tipo
                                    nuevo_tipo = obtener_tipo_categoria(nueva_categoria)
                                    tipo_info = {
                                        'superior': '🔝 Parte Superior',
                                        'inferior': '👖 Parte Inferior',
                                        'accesorios': '🎽 Accesorio',
                                        'personalizado': '📌 Personalizado'
                                    }
                                    st.info(f"{tipo_info.get(nuevo_tipo, '📦')}: {', '.join(obtener_tallas_disponibles(nueva_categoria))}")
                                    
                                    st.info(f"📝 Ventas actuales: {producto_data['Ventas']} | Stock actual: {producto_data['Stock']}")
                                    
                                    # Botones de acción
                                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                                    
                                    with col_btn1:
                                        guardar = st.form_submit_button("💾 Guardar Cambios", type="primary", use_container_width=True)
                                    
                                    with col_btn2:
                                        if st.form_submit_button("📦 Solo Ajustar Stock", use_container_width=True):
                                            success, message = ajustar_stock(producto_id, nueva_cantidad)
                                            if success:
                                                st.success(message)
                                                st.rerun()
                                            else:
                                                st.error(message)
                                    
                                    with col_btn3:
                                        if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                            st.session_state.modo_edicion = None
                                            st.rerun()
                                    
                                    if guardar:
                                        datos_actualizados = {
                                            'Categoria': nueva_categoria,
                                            'Producto': nuevo_producto,
                                            'Talla': nueva_talla,
                                            'Color': nuevo_color,
                                            'Entrada': nueva_cantidad,
                                            'Precio': float(nuevo_precio)
                                        }
                                        
                                        success, message = editar_producto(producto_id, datos_actualizados)
                                        if success:
                                            st.success(message)
                                            st.session_state.modo_edicion = None
                                            st.rerun()
                                        else:
                                            st.error(message)
                
                # MODO: ELIMINAR PRODUCTO
                elif st.session_state.modo_edicion == 'eliminar':
                    st.subheader("🗑️ Eliminar Producto")
                    
                    if df.empty:
                        st.info("No hay productos para eliminar.")
                    else:
                        # Filtrar productos que no tienen ventas
                        productos_sin_ventas = df[df['Ventas'] == 0]
                        
                        if productos_sin_ventas.empty:
                            st.warning("⚠️ No hay productos sin ventas. Solo se pueden eliminar productos que NO tienen ventas registradas.")
                            st.dataframe(df[['Producto', 'Talla', 'Color', 'Ventas']], use_container_width=True)
                        else:
                            # Lista de productos sin ventas
                            productos_eliminar = {f"{row['Producto']} ({row['Talla']}, {row['Color']})": row['ID'] 
                                                for _, row in productos_sin_ventas.iterrows()}
                            
                            producto_eliminar = st.selectbox(
                                "Selecciona un producto para eliminar (solo sin ventas):",
                                list(productos_eliminar.keys()),
                                key="select_eliminar"
                            )
                            
                            if producto_eliminar:
                                producto_id = productos_eliminar[producto_eliminar]
                                producto_data = next((item for item in st.session_state.inventario 
                                                    if item['ID'] == producto_id), None)
                                
                                if producto_data:
                                    st.warning(f"⚠️ ¿Estás seguro de eliminar **{producto_data['Producto']}**?")
                                    
                                    tipo_icono = {
                                        'superior': '🔝',
                                        'inferior': '👖',
                                        'accesorios': '🎽',
                                        'personalizado': '📌'
                                    }
                                    
                                    col_info1, col_info2 = st.columns(2)
                                    with col_info1:
                                        tipo = producto_data.get('Tipo', 'desconocido')
                                        st.write(f"**{tipo_icono.get(tipo, '📦')} Tipo:** {producto_data['Categoria']}")
                                        st.write(f"**Talla:** {producto_data['Talla']}")
                                    with col_info2:
                                        st.write(f"**Color:** {producto_data['Color']}")
                                        st.write(f"**Precio:** ${producto_data['Precio']:,.2f}")
                                    
                                    col_conf1, col_conf2, col_conf3 = st.columns([1, 1, 2])
                                    
                                    with col_conf1:
                                        if st.button("✅ Sí, Eliminar", type="primary", use_container_width=True):
                                            success, message = eliminar_producto(producto_id)
                                            if success:
                                                st.success(message)
                                                st.session_state.modo_edicion = None
                                                st.rerun()
                                            else:
                                                st.error(message)
                                    
                                    with col_conf2:
                                        if st.button("❌ Cancelar", use_container_width=True):
                                            st.session_state.modo_edicion = None
                                            st.rerun()
                
                # MODO: VER INVENTARIO (por defecto)
                else:
                    st.subheader("📋 Inventario Actual")
                    
                    if df.empty:
                        st.info("No hay productos en el inventario.")
                    else:
                        # Resumen del inventario
                        col_res1, col_res2, col_res3 = st.columns(3)
                        with col_res1:
                            st.metric("📦 Total Productos", len(df))
                        with col_res2:
                            valor_inventario = (df['Stock'] * df['Precio']).sum()
                            st.metric("💰 Valor Inventario", f"${valor_inventario:,.2f}")
                        with col_res3:
                            productos_con_stock = len(df[df['Stock'] > 0])
                            st.metric("📈 Productos con Stock", f"{productos_con_stock}")
                        
                        # Búsqueda en inventario
                        search_inv = st.text_input("🔍 Buscar en inventario:", key="search_inv")
                        
                        if search_inv:
                            filtered_inv = df[
                                df['Producto'].str.contains(search_inv, case=False, na=False) |
                                df['Categoria'].str.contains(search_inv, case=False, na=False) |
                                df['Color'].str.contains(search_inv, case=False, na=False) |
                                df['Talla'].str.contains(search_inv, case=False, na=False)
                            ]
                        else:
                            filtered_inv = df
                        
                        # Mostrar tabla
                        if not filtered_inv.empty:
                            tipo_map_display_inv = {
                                'superior': '🔝 Superior',
                                'inferior': '👖 Inferior', 
                                'accesorios': '🎽 Accesorio',
                                'personalizado': '📌 Personalizado'
                            }
                            
                            display_inv = filtered_inv.copy()
                            display_inv['Precio'] = display_inv['Precio'].apply(lambda x: f"${x:,.2f}")
                            
                            if 'Tipo' in display_inv.columns:
                                display_inv['Tipo'] = display_inv['Tipo'].map(tipo_map_display_inv)
                            
                            columnas_mostrar = []
                            for col in ['Tipo', 'Categoria', 'Producto', 'Talla', 'Color', 'Stock', 'Ventas', 'Precio']:
                                if col in display_inv.columns:
                                    columnas_mostrar.append(col)
                            
                            st.dataframe(
                                display_inv[columnas_mostrar],
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    'Tipo': st.column_config.TextColumn("Tipo"),
                                    'Categoria': st.column_config.TextColumn("Categoría"),
                                    'Producto': st.column_config.TextColumn("Producto"),
                                    'Talla': st.column_config.TextColumn("Talla"),
                                    'Color': st.column_config.TextColumn("Color"),
                                    'Stock': st.column_config.NumberColumn("Stock", format="%d"),
                                    'Ventas': st.column_config.NumberColumn("Ventas", format="%d"),
                                    'Precio': st.column_config.TextColumn("Precio")
                                }
                            )
                        else:
                            st.info("No hay productos que coincidan con la búsqueda.")

# ============================================
# EJECUCIÓN
# ============================================
if __name__ == "__main__":
    main()