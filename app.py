import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json
import os

# ============================================
# CONFIGURACIÓN
# ============================================
st.set_page_config(
    page_title="Inventario roPacheco",
    page_icon="👔",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Contraseña
CONTRASENA = "michiotaku"

# Configuración inicial
if 'categorias_personalizadas' not in st.session_state:
    st.session_state.categorias_personalizadas = []

if 'reset_graficas_fecha' not in st.session_state:
    st.session_state.reset_graficas_fecha = datetime.now().strftime('%Y-%m-%d')

# Categorías base
CATEGORIAS_BASE = [
    'Camisas', 'Playeras', 'Suéteres', 'Chamarras',
    'Pantalones', 'Shorts', 'Jeans', 'Niño'
]

# Obtener todas las categorías disponibles
def obtener_todas_categorias():
    todas = CATEGORIAS_BASE.copy()
    todas.extend(st.session_state.categorias_personalizadas)
    return sorted(list(set(todas)))

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
if 'modo_mover_stock' not in st.session_state:
    st.session_state.modo_mover_stock = None
if 'producto_mover' not in st.session_state:
    st.session_state.producto_mover = None

# Archivo para guardar datos
INVENTARIO_FILE = "inventario_data.json"
CATEGORIAS_FILE = "categorias_data.json"

# ============================================
# FUNCIONES DE DATOS - MODIFICADAS
# ============================================
def crear_nuevo_producto(producto, talla, color, categoria, entrada_total, precio_sugerido, precio_venta, ubicacion_inicial="Bodega"):
    """Crear un nuevo producto con la nueva estructura"""
    nuevo_id = f"PROD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Distribuir el stock inicial según ubicación
    if ubicacion_inicial == "Bodega":
        stock_bodega = entrada_total
        stock_exhibido = 0
    else:
        stock_bodega = 0
        stock_exhibido = entrada_total
    
    return {
        'ID': nuevo_id,
        'Categoria': categoria,
        'Producto': producto,
        'Talla': talla,
        'Color': color,
        'Ubicacion': ubicacion_inicial,
        'Entrada_Total': entrada_total,
        'Stock_Bodega': stock_bodega,
        'Stock_Exhibido': stock_exhibido,
        'Stock_Total': entrada_total,
        'Ventas_Total': 0,
        'Precio_Sugerido': float(precio_sugerido),
        'Precio_Venta': float(precio_venta) if precio_venta > 0 else float(precio_sugerido)
    }

def cargar_datos():
    """Cargar todos los datos desde archivos y migrar estructura si es necesario"""
    # Cargar inventario
    try:
        if os.path.exists(INVENTARIO_FILE):
            with open(INVENTARIO_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Verificar si necesitamos migrar la estructura
                inventario_old = data.get('inventario', [])
                inventario_new = []
                
                for item in inventario_old:
                    # Si es estructura vieja, migrar
                    if 'Stock_Bodega' not in item:
                        # Migrar de estructura vieja a nueva
                        item_migrado = {
                            'ID': item.get('ID', ''),
                            'Categoria': item.get('Categoria', ''),
                            'Producto': item.get('Producto', ''),
                            'Talla': item.get('Talla', ''),
                            'Color': item.get('Color', ''),
                            'Ubicacion': 'Exhibido',
                            'Entrada_Total': item.get('Entrada', 0),
                            'Stock_Bodega': 0,
                            'Stock_Exhibido': item.get('Stock', 0),
                            'Stock_Total': item.get('Stock', 0),
                            'Ventas_Total': item.get('Ventas', 0),
                            'Precio_Sugerido': item.get('Precio', 0.0),
                            'Precio_Venta': item.get('Precio', 0.0)
                        }
                        inventario_new.append(item_migrado)
                    else:
                        inventario_new.append(item)
                
                st.session_state.inventario = inventario_new
                st.session_state.ventas_diarias = data.get('ventas_diarias', [])
                st.session_state.caja = data.get('caja', 0.0)
    except Exception as e:
        st.error(f"Error al cargar inventario: {str(e)}")
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

def registrar_venta(producto_id, precio_venta_real=None):
    """Registrar una venta con precio de venta real"""
    for item in st.session_state.inventario:
        if item['ID'] == producto_id:
            # Verificar stock disponible según ubicación
            if item['Ubicacion'] == 'Exhibido':
                stock_disponible = item['Stock_Exhibido']
            else:
                stock_disponible = item['Stock_Bodega']
            
            if stock_disponible > 0:
                # Actualizar stock según ubicación
                if item['Ubicacion'] == 'Exhibido':
                    item['Stock_Exhibido'] -= 1
                else:
                    item['Stock_Bodega'] -= 1
                
                item['Ventas_Total'] += 1
                item['Stock_Total'] -= 1
                
                # Usar precio de venta real si se proporciona, sino el Precio_Venta guardado
                precio_final = float(precio_venta_real) if precio_venta_real else item['Precio_Venta']
                
                # Registrar venta diaria con precio real
                venta = {
                    'fecha': datetime.now().isoformat(),
                    'producto': item['Producto'],
                    'talla': item['Talla'],
                    'precio_sugerido': item['Precio_Sugerido'],
                    'precio_venta': precio_final,
                    'categoria': item['Categoria'],
                    'ubicacion': item['Ubicacion']
                }
                st.session_state.ventas_diarias.append(venta)
                
                # Actualizar caja con precio REAL
                st.session_state.caja += precio_final
                
                guardar_inventario()
                return True, precio_final
            else:
                return False, f"No hay stock disponible en {item['Ubicacion']}"
    
    return False, "Producto no encontrado"

def agregar_producto(nuevo_producto):
    """Agregar nuevo producto al inventario"""
    st.session_state.inventario.append(nuevo_producto)
    guardar_inventario()
    return True

def editar_producto(producto_id, datos_actualizados):
    """Editar un producto existente"""
    for i, item in enumerate(st.session_state.inventario):
        if item['ID'] == producto_id:
            # Preservar ventas y stocks por ubicación
            ventas_actuales = item['Ventas_Total']
            
            # Calcular nuevo stock total
            nueva_entrada_total = datos_actualizados['Entrada_Total']
            
            # Verificar que el nuevo stock no sea menor a las ventas
            if nueva_entrada_total < ventas_actuales:
                return False, f"No puedes reducir la cantidad por debajo de las ventas ({ventas_actuales})"
            
            # Calcular nuevo stock total
            nuevo_stock_total = nueva_entrada_total - ventas_actuales
            
            # Distribuir stock manteniendo proporciones actuales
            stock_bodega_actual = item['Stock_Bodega']
            stock_exhibido_actual = item['Stock_Exhibido']
            stock_total_actual = stock_bodega_actual + stock_exhibido_actual
            
            if stock_total_actual > 0:
                # Mantener las proporciones actuales
                proporcion_bodega = stock_bodega_actual / stock_total_actual
                proporcion_exhibido = stock_exhibido_actual / stock_total_actual
                
                nuevo_stock_bodega = int(nuevo_stock_total * proporcion_bodega)
                nuevo_stock_exhibido = nuevo_stock_total - nuevo_stock_bodega
            else:
                # Si no hay stock, mantener la ubicación actual
                if item['Ubicacion'] == 'Bodega':
                    nuevo_stock_bodega = nuevo_stock_total
                    nuevo_stock_exhibido = 0
                else:
                    nuevo_stock_bodega = 0
                    nuevo_stock_exhibido = nuevo_stock_total
            
            # Actualizar todos los datos
            datos_actualizados['Ventas_Total'] = ventas_actuales
            datos_actualizados['Stock_Total'] = nuevo_stock_total
            datos_actualizados['Stock_Bodega'] = nuevo_stock_bodega
            datos_actualizados['Stock_Exhibido'] = nuevo_stock_exhibido
            datos_actualizados['ID'] = producto_id
            datos_actualizados['Ubicacion'] = item['Ubicacion']  # Mantener ubicación
            datos_actualizados['Precio_Sugerido'] = item['Precio_Sugerido']  # Mantener precio sugerido
            datos_actualizados['Precio_Venta'] = item['Precio_Venta']  # Mantener precio venta
            
            st.session_state.inventario[i] = datos_actualizados
            guardar_inventario()
            return True, "Producto actualizado correctamente"
    
    return False, "Producto no encontrado"

def eliminar_producto(producto_id):
    """Eliminar un producto del inventario"""
    for i, item in enumerate(st.session_state.inventario):
        if item['ID'] == producto_id:
            # Guardamos información antes de eliminar
            producto_eliminado = st.session_state.inventario.pop(i)
            
            # Si tenía ventas, restamos de la caja
            if producto_eliminado['Ventas_Total'] > 0:
                # Necesitamos calcular cuánto se había sumado a la caja
                # Buscamos todas las ventas de este producto
                ventas_producto = [v for v in st.session_state.ventas_diarias 
                                  if v.get('producto') == producto_eliminado['Producto']]
                
                total_ventas_producto = sum(v.get('precio_venta', 0) for v in ventas_producto)
                st.session_state.caja -= total_ventas_producto
                
                if st.session_state.caja < 0:
                    st.session_state.caja = 0
            
            guardar_inventario()
            return True, f"Producto '{producto_eliminado['Producto']}' eliminado correctamente"
    
    return False, "Producto no encontrado"

def mover_stock(producto_id, cantidad, origen, destino):
    """Mover stock entre bodega y exhibido"""
    for item in st.session_state.inventario:
        if item['ID'] == producto_id:
            # Verificar stock disponible en origen
            stock_origen = item['Stock_Bodega'] if origen == 'Bodega' else item['Stock_Exhibido']
            
            if stock_origen < cantidad:
                return False, f"No hay suficiente stock en {origen} (solo hay {stock_origen})"
            
            # Actualizar stocks
            if origen == 'Bodega':
                item['Stock_Bodega'] -= cantidad
                item['Stock_Exhibido'] += cantidad
            else:
                item['Stock_Exhibido'] -= cantidad
                item['Stock_Bodega'] += cantidad
            
            # Actualizar ubicación principal basada en dónde hay más stock
            if item['Stock_Bodega'] > item['Stock_Exhibido']:
                item['Ubicacion'] = 'Bodega'
            elif item['Stock_Exhibido'] > item['Stock_Bodega']:
                item['Ubicacion'] = 'Exhibido'
            else:
                # Si hay igual cantidad, mantener ubicación actual
                pass
            
            guardar_inventario()
            return True, f"{cantidad} unidades movidas de {origen} a {destino}"
    
    return False, "Producto no encontrado"

def actualizar_precio_venta(producto_id, nuevo_precio_venta):
    """Actualizar el precio de venta de un producto"""
    for item in st.session_state.inventario:
        if item['ID'] == producto_id:
            item['Precio_Venta'] = float(nuevo_precio_venta)
            guardar_inventario()
            return True, "Precio de venta actualizado"
    return False, "Producto no encontrado"

def actualizar_precio_sugerido(producto_id, nuevo_precio_sugerido):
    """Actualizar el precio sugerido de un producto"""
    for item in st.session_state.inventario:
        if item['ID'] == producto_id:
            item['Precio_Sugerido'] = float(nuevo_precio_sugerido)
            guardar_inventario()
            return True, "Precio sugerido actualizado"
    return False, "Producto no encontrado"

def calcular_caja_total():
    """Calcular el total de caja desde las ventas diarias (con precios reales)"""
    total = 0.0
    for venta in st.session_state.ventas_diarias:
        total += venta.get('precio_venta', 0)
    return total

# ============================================
# INTERFAZ PRINCIPAL
# ============================================
def main():
    st.title("👔 Inventario Ropa de Caballero")
    
    # Cargar todos los datos
    cargar_datos()
    
    # Información del sistema
    with st.expander("ℹ️ Información del Sistema", expanded=False):
        st.write("""
        **✨ NUEVAS CARACTERÍSTICAS:**
        - **📦 Stock dividido**: Bodega vs Exhibido
        - **💰 Dos precios**: Precio sugerido y precio de venta real
        - **🔄 Mover stock**: Transfiere entre ubicaciones fácilmente
        - **🎯 Ventas flexibles**: Precio personalizable por venta
        
        **📌 Otras características:**
        - Tallas manuales (escribe cualquier talla)
        - Categorías personalizables
        - Eliminar productos con o sin ventas
        - Control de gráficas programado
        """)
    
    st.markdown("---")
    
    # Convertir a DataFrame
    df = pd.DataFrame(st.session_state.inventario)
    
    # Pestañas
    tab1, tab2, tab3 = st.tabs(["🛍️ Registrar Ventas", "📊 Reporte y Caja", "⚙️ Gestión Inventario"])
    
    # TAB 1: REGISTRAR VENTAS - MODIFICADA
    with tab1:
        st.header("Registrar Ventas")
        
        if df.empty:
            st.info("📭 No hay productos en el inventario.")
        else:
            # Filtros mejorados
            col_filt1, col_filt2, col_filt3 = st.columns(3)
            with col_filt1:
                todas_categorias = obtener_todas_categorias()
                categoria_filtro = st.selectbox("Categoría:", ['Todas'] + sorted(todas_categorias), key="cat_filtro_ventas")
            with col_filt2:
                ubicacion_filtro = st.selectbox("Ubicación:", ['Todas', 'Exhibido', 'Bodega'], key="ubic_filtro_ventas")
            with col_filt3:
                search_term = st.text_input("🔍 Buscar:", "", key="search_ventas")
            
            # Aplicar filtros
            filtered_df = df.copy()
            
            if not df.empty:
                if categoria_filtro != 'Todas':
                    filtered_df = filtered_df[filtered_df['Categoria'] == categoria_filtro]
                
                if ubicacion_filtro != 'Todas':
                    filtered_df = filtered_df[filtered_df['Ubicacion'] == ubicacion_filtro]
                
                if search_term:
                    filtered_df = filtered_df[
                        filtered_df['Producto'].str.contains(search_term, case=False, na=False) |
                        filtered_df['Categoria'].str.contains(search_term, case=False, na=False) |
                        filtered_df['Color'].str.contains(search_term, case=False, na=False) |
                        filtered_df['Talla'].str.contains(search_term, case=False, na=False)
                    ]
            
            if filtered_df.empty:
                st.info("No se encontraron productos.")
            else:
                st.write(f"**📊 {len(filtered_df)} productos encontrados**")
                
                # Mostrar productos
                for _, row in filtered_df.iterrows():
                    with st.expander(f"📦 {row['Producto']} | 👕 {row['Talla']} | 🎨 {row['Color']} | 💰${row['Precio_Venta']:,.2f}"):
                        col_info1, col_info2 = st.columns(2)
                        
                        with col_info1:
                            st.write(f"**📋 Categoría:** {row['Categoria']}")
                            st.write(f"**📍 Ubicación:** {row['Ubicacion']}")
                            st.write(f"**💰 Precio Sugerido:** ${row['Precio_Sugerido']:,.2f}")
                            st.write(f"**💵 Precio Venta:** ${row['Precio_Venta']:,.2f}")
                        
                        with col_info2:
                            st.write(f"**🛍️ Stock Exhibido:** {int(row['Stock_Exhibido'])}")
                            st.write(f"**📦 Stock Bodega:** {int(row['Stock_Bodega'])}")
                            st.write(f"**📊 Stock Total:** {int(row['Stock_Total'])}")
                            st.write(f"**📈 Ventas:** {int(row['Ventas_Total'])}")
                        
                        # Verificar stock disponible según ubicación
                        if row['Ubicacion'] == 'Exhibido':
                            stock_disponible = row['Stock_Exhibido']
                            ubicacion_texto = "exhibido"
                        else:
                            stock_disponible = row['Stock_Bodega']
                            ubicacion_texto = "bodega"
                        
                        if stock_disponible > 0:
                            # Botón para mover stock
                            if st.button("🔄 Mover Stock", key=f"btn_mover_{row['ID']}", use_container_width=True):
                                st.session_state.modo_mover_stock = 'mover'
                                st.session_state.producto_mover = row['ID']
                                st.rerun()
                            
                            # Formulario para vender con precio personalizado
                            with st.form(key=f"venta_form_{row['ID']}"):
                                col_precio1, col_precio2 = st.columns(2)
                                with col_precio1:
                                    precio_venta = st.number_input(
                                        f"Precio de venta ($):",
                                        min_value=0.0,
                                        value=float(row['Precio_Venta']),
                                        step=0.01,
                                        format="%.2f",
                                        key=f"precio_venta_{row['ID']}"
                                    )
                                
                                with col_precio2:
                                    if st.form_submit_button("✅ Vender 1 Unidad", use_container_width=True, type="primary"):
                                        success, resultado = registrar_venta(row['ID'], precio_venta)
                                        if success:
                                            st.success(f"✅ Vendido por ${resultado:,.2f}")
                                            st.rerun()
                                        else:
                                            st.error(f"❌ {resultado}")
                        else:
                            st.error(f"❌ Sin stock disponible en {ubicacion_texto}")
    
    # TAB 2: REPORTE Y CAJA - MODIFICADA
    with tab2:
        st.header("📊 Reporte y Caja")
        
        # Control de gráficas
        with st.expander("🔄 Control de Gráficas", expanded=False):
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                nueva_fecha_reset = st.date_input(
                    "Próximo reset de gráficas:",
                    value=datetime.strptime(st.session_state.reset_graficas_fecha, '%Y-%m-%d'),
                    key="fecha_reset"
                )
            
            with col_res2:
                if st.button("💾 Guardar Fecha", use_container_width=True):
                    st.session_state.reset_graficas_fecha = nueva_fecha_reset.strftime('%Y-%m-%d')
                    st.success(f"Fecha guardada: {nueva_fecha_reset.strftime('%Y-%m-%d')}")
                
                if st.button("🔄 Resetear Gráficas Ahora", use_container_width=True, type="secondary"):
                    st.session_state.ventas_diarias = []
                    guardar_inventario()
                    st.success("¡Gráficas reseteadas!")
                    st.rerun()
        
        if df.empty:
            st.info("No hay datos para mostrar.")
        else:
            # Asegurar columnas
            columnas_necesarias = ['Stock_Bodega', 'Stock_Exhibido', 'Stock_Total', 
                                 'Ventas_Total', 'Precio_Sugerido', 'Precio_Venta']
            
            for col in columnas_necesarias:
                if col not in df.columns:
                    if col == 'Stock_Bodega':
                        df['Stock_Bodega'] = 0
                    elif col == 'Stock_Exhibido':
                        df['Stock_Exhibido'] = df.get('Stock', 0)
                    elif col == 'Stock_Total':
                        df['Stock_Total'] = df.get('Stock', 0)
                    elif col == 'Ventas_Total':
                        df['Ventas_Total'] = df.get('Ventas', 0)
                    elif col == 'Precio_Sugerido':
                        df['Precio_Sugerido'] = df.get('Precio', 0.0)
                    elif col == 'Precio_Venta':
                        df['Precio_Venta'] = df.get('Precio', 0.0)
            
            # Calcular caja total
            caja_total = calcular_caja_total()
            st.session_state.caja = caja_total
            
            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_ventas = df['Ventas_Total'].sum()
                st.metric("📈 Ventas Totales", f"{int(total_ventas)}")
            
            with col2:
                st.metric("💰 Caja Total", f"${caja_total:,.2f}")
            
            with col3:
                stock_exhibido = df['Stock_Exhibido'].sum()
                st.metric("🛍️ Stock Exhibido", f"{int(stock_exhibido)}")
            
            with col4:
                stock_bodega = df['Stock_Bodega'].sum()
                st.metric("📦 Stock Bodega", f"{int(stock_bodega)}")
            
            st.markdown("---")
            
            # Gráficos mejorados
            col1, col2 = st.columns(2)
            
            with col1:
                if not df.empty:
                    # Ventas por categoría
                    ventas_por_categoria = df.groupby('Categoria')['Ventas_Total'].sum().reset_index()
                    if not ventas_por_categoria.empty:
                        fig = px.pie(
                            ventas_por_categoria, 
                            values='Ventas_Total', 
                            names='Categoria',
                            title="📊 Ventas por Categoría",
                            color_discrete_sequence=px.colors.qualitative.Set3,
                            hole=0.3
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if not df.empty:
                    # Stock por ubicación
                    stock_data = pd.DataFrame({
                        'Ubicacion': ['Exhibido', 'Bodega'],
                        'Stock': [int(df['Stock_Exhibido'].sum()), int(df['Stock_Bodega'].sum())]
                    })
                    
                    if not stock_data.empty:
                        fig = px.bar(
                            stock_data,
                            x='Ubicacion',
                            y='Stock',
                            title="📍 Distribución del Stock",
                            color='Ubicacion',
                            text='Stock',
                            color_discrete_map={'Exhibido': '#2E86AB', 'Bodega': '#A23B72'}
                        )
                        fig.update_traces(textposition='outside')
                        st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Tabla completa
            st.subheader("📋 Inventario Completo")
            
            # Filtros para la tabla
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                todas_categorias_tabla = ['Todas'] + sorted(df['Categoria'].unique().tolist())
                filtro_categoria = st.selectbox("Filtrar categoría:", todas_categorias_tabla, key="filtro_categoria_tabla")
            with col_f2:
                filtro_ubicacion = st.selectbox("Filtrar ubicación:", ['Todas', 'Exhibido', 'Bodega'], key="filtro_ubicacion_tabla")
            with col_f3:
                ordenar_por = st.selectbox("Ordenar por:", ['Producto', 'Stock_Total', 'Ventas_Total', 'Precio_Venta'], key="ordenar_por_tabla")
            
            # Aplicar filtros
            display_df = df.copy()
            
            if filtro_categoria != 'Todas':
                display_df = display_df[display_df['Categoria'] == filtro_categoria]
            
            if filtro_ubicacion != 'Todas':
                display_df = display_df[display_df['Ubicacion'] == filtro_ubicacion]
            
            # Ordenar
            if ordenar_por == 'Stock_Total':
                display_df = display_df.sort_values('Stock_Total', ascending=False)
            elif ordenar_por == 'Ventas_Total':
                display_df = display_df.sort_values('Ventas_Total', ascending=False)
            elif ordenar_por == 'Precio_Venta':
                display_df = display_df.sort_values('Precio_Venta', ascending=False)
            else:
                display_df = display_df.sort_values('Producto')
            
            # Mostrar tabla
            if not display_df.empty:
                display_df_formatted = display_df.copy()
                display_df_formatted['Precio_Sugerido'] = display_df_formatted['Precio_Sugerido'].apply(lambda x: f"${x:,.2f}")
                display_df_formatted['Precio_Venta'] = display_df_formatted['Precio_Venta'].apply(lambda x: f"${x:,.2f}")
                
                st.dataframe(
                    display_df_formatted[['Categoria', 'Producto', 'Talla', 'Color', 'Ubicacion', 
                                         'Stock_Bodega', 'Stock_Exhibido', 'Stock_Total', 
                                         'Ventas_Total', 'Precio_Sugerido', 'Precio_Venta']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'Categoria': st.column_config.TextColumn("Categoría"),
                        'Producto': st.column_config.TextColumn("Producto"),
                        'Talla': st.column_config.TextColumn("Talla"),
                        'Color': st.column_config.TextColumn("Color"),
                        'Ubicacion': st.column_config.TextColumn("📍 Ubicación"),
                        'Stock_Bodega': st.column_config.NumberColumn("📦 Bodega", format="%d"),
                        'Stock_Exhibido': st.column_config.NumberColumn("🛍️ Exhibido", format="%d"),
                        'Stock_Total': st.column_config.NumberColumn("📊 Total", format="%d"),
                        'Ventas_Total': st.column_config.NumberColumn("📈 Ventas", format="%d"),
                        'Precio_Sugerido': st.column_config.TextColumn("💰 Sugerido"),
                        'Precio_Venta': st.column_config.TextColumn("💵 Venta")
                    }
                )
            else:
                st.info("No hay productos que coincidan con los filtros.")
            
            # Botones de exportación
            col_exp1, col_exp2, col_exp3 = st.columns(3)
            with col_exp1:
                if st.button("📥 Exportar CSV", use_container_width=True, key="export_csv"):
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
                if st.button("🔄 Actualizar Precios", use_container_width=True, key="btn_actualizar_precios"):
                    st.session_state.modo_edicion = 'actualizar_precios'
                    st.rerun()
            
            with col_exp3:
                if st.button("🔄 Reiniciar Caja", use_container_width=True, key="reset_caja"):
                    st.session_state.caja = 0.0
                    st.session_state.ventas_diarias = []
                    for item in st.session_state.inventario:
                        item['Ventas_Total'] = 0
                        item['Stock_Total'] = item['Entrada_Total']
                        item['Stock_Bodega'] = item['Entrada_Total'] if item['Ubicacion'] == 'Bodega' else 0
                        item['Stock_Exhibido'] = 0 if item['Ubicacion'] == 'Bodega' else item['Entrada_Total']
                    guardar_inventario()
                    st.success("Caja y ventas reiniciadas")
                    st.rerun()
    
    # TAB 3: GESTIÓN INVENTARIO - MODIFICADA
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
            
            # Botones principales
            col_logout, col_cats, col_mover, col_space = st.columns([1, 1, 1, 1])
            with col_logout:
                if st.button("🚪 Cerrar Sesión", use_container_width=True, key="logout_admin"):
                    st.session_state.admin_logged_in = False
                    st.session_state.modo_edicion = None
                    st.session_state.producto_editar = None
                    st.session_state.mostrar_gestion_categorias = False
                    st.session_state.modo_mover_stock = None
                    st.rerun()
            
            with col_cats:
                if st.button("🏷️ Categorías", use_container_width=True, 
                           type="primary" if st.session_state.mostrar_gestion_categorias else "secondary"):
                    st.session_state.mostrar_gestion_categorias = not st.session_state.mostrar_gestion_categorias
                    st.session_state.modo_edicion = None
                    st.session_state.modo_mover_stock = None
                    st.rerun()
            
            with col_mover:
                if st.button("🔄 Mover Stock", use_container_width=True,
                           type="primary" if st.session_state.modo_mover_stock == 'seleccionar' else "secondary"):
                    st.session_state.modo_mover_stock = 'seleccionar'
                    st.session_state.mostrar_gestion_categorias = False
                    st.session_state.modo_edicion = None
                    st.rerun()
            
            st.markdown("---")
            
            # MODO: MOVER STOCK
            if st.session_state.modo_mover_stock == 'seleccionar':
                st.subheader("🔄 Mover Stock entre Ubicaciones")
                
                if df.empty:
                    st.info("No hay productos para mover.")
                else:
                    # Seleccionar producto
                    productos_opciones = {f"{row['Producto']} ({row['Talla']}, {row['Color']}) - Bodega:{row['Stock_Bodega']} | Exhibido:{row['Stock_Exhibido']}": row['ID'] 
                                        for _, row in df.iterrows()}
                    
                    producto_seleccionado = st.selectbox(
                        "Selecciona un producto para mover stock:",
                        list(productos_opciones.keys()),
                        key="select_mover"
                    )
                    
                    if producto_seleccionado:
                        producto_id = productos_opciones[producto_seleccionado]
                        producto_data = next((item for item in st.session_state.inventario 
                                            if item['ID'] == producto_id), None)
                        
                        if producto_data:
                            st.session_state.producto_mover = producto_id
                            st.session_state.modo_mover_stock = 'mover'
                            st.rerun()
            
            elif st.session_state.modo_mover_stock == 'mover' and st.session_state.producto_mover:
                # Formulario para mover stock
                producto_id = st.session_state.producto_mover
                producto_data = next((item for item in st.session_state.inventario 
                                    if item['ID'] == producto_id), None)
                
                if producto_data:
                    st.subheader(f"🔄 Mover Stock: {producto_data['Producto']}")
                    
                    with st.form("form_mover_stock"):
                        col_info1, col_info2 = st.columns(2)
                        with col_info1:
                            st.write(f"**📦 Stock Bodega:** {producto_data['Stock_Bodega']}")
                            st.write(f"**🛍️ Stock Exhibido:** {producto_data['Stock_Exhibido']}")
                            st.write(f"**📍 Ubicación actual:** {producto_data['Ubicacion']}")
                        
                        with col_info2:
                            # Seleccionar dirección del movimiento
                            direccion = st.selectbox(
                                "Dirección del movimiento:",
                                ["De Bodega a Exhibido", "De Exhibido a Bodega"],
                                key="direccion_mover"
                            )
                            
                            # Determinar origen y destino
                            if direccion == "De Bodega a Exhibido":
                                origen = "Bodega"
                                destino = "Exhibido"
                                max_cantidad = producto_data['Stock_Bodega']
                            else:
                                origen = "Exhibido"
                                destino = "Bodega"
                                max_cantidad = producto_data['Stock_Exhibido']
                            
                            cantidad = st.number_input(
                                f"Cantidad a mover (máx: {max_cantidad}):",
                                min_value=1,
                                max_value=max_cantidad,
                                value=1 if max_cantidad > 0 else 0,
                                step=1,
                                key="cantidad_mover"
                            )
                        
                        col_btn1, col_btn2, col_btn3 = st.columns(3)
                        with col_btn1:
                            mover = st.form_submit_button("🔄 Mover Stock", type="primary", use_container_width=True)
                        with col_btn2:
                            cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
                        
                        if cancelar:
                            st.session_state.modo_mover_stock = None
                            st.session_state.producto_mover = None
                            st.rerun()
                        
                        if mover and cantidad > 0:
                            success, mensaje = mover_stock(producto_id, cantidad, origen, destino)
                            if success:
                                st.success(f"✅ {mensaje}")
                                st.session_state.modo_mover_stock = None
                                st.session_state.producto_mover = None
                                st.rerun()
                            else:
                                st.error(f"❌ {mensaje}")
            
            # PANEL DE GESTIÓN DE CATEGORÍAS
            elif st.session_state.mostrar_gestion_categorias:
                st.subheader("🏷️ Gestión de Categorías")
                
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    with st.container(border=True):
                        st.markdown("### 📋 Categorías Existentes")
                        todas_categorias = obtener_todas_categorias()
                        
                        st.write("**Categorías base:**")
                        for cat in CATEGORIAS_BASE:
                            st.write(f"- {cat}")
                        
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
                                    st.success(f"✅ Categoría '{nueva_categoria}' agregada!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ La categoría '{nueva_categoria}' ya existe.")
                            else:
                                st.error("❌ Ingresa un nombre para la categoría.")
                        
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
                if st.button("⬅️ Volver a Gestión", use_container_width=True):
                    st.session_state.mostrar_gestion_categorias = False
                    st.rerun()
            
            # MODO: ACTUALIZAR PRECIOS
            elif st.session_state.modo_edicion == 'actualizar_precios':
                st.subheader("💰 Actualizar Precios")
                
                if df.empty:
                    st.info("No hay productos para actualizar.")
                else:
                    # Seleccionar producto
                    productos_opciones = {f"{row['Producto']} ({row['Talla']}) - Sug:${row['Precio_Sugerido']:.2f} | Ven:${row['Precio_Venta']:.2f}": row['ID'] 
                                        for _, row in df.iterrows()}
                    
                    producto_seleccionado = st.selectbox(
                        "Selecciona un producto para actualizar precios:",
                        list(productos_opciones.keys()),
                        key="select_actualizar_precios"
                    )
                    
                    if producto_seleccionado:
                        producto_id = productos_opciones[producto_seleccionado]
                        producto_data = next((item for item in st.session_state.inventario 
                                            if item['ID'] == producto_id), None)
                        
                        if producto_data:
                            with st.form("form_actualizar_precios"):
                                col_precio1, col_precio2 = st.columns(2)
                                
                                with col_precio1:
                                    nuevo_precio_sugerido = st.number_input(
                                        "Nuevo precio sugerido ($):",
                                        min_value=0.0,
                                        value=float(producto_data['Precio_Sugerido']),
                                        step=0.01,
                                        format="%.2f",
                                        key="nuevo_sugerido"
                                    )
                                
                                with col_precio2:
                                    nuevo_precio_venta = st.number_input(
                                        "Nuevo precio de venta ($):",
                                        min_value=0.0,
                                        value=float(producto_data['Precio_Venta']),
                                        step=0.01,
                                        format="%.2f",
                                        key="nuevo_venta"
                                    )
                                
                                col_btn1, col_btn2 = st.columns(2)
                                with col_btn1:
                                    guardar = st.form_submit_button("💾 Actualizar Precios", type="primary", use_container_width=True)
                                with col_btn2:
                                    cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
                                
                                if cancelar:
                                    st.session_state.modo_edicion = None
                                    st.rerun()
                                
                                if guardar:
                                    # Actualizar ambos precios
                                    success1, mensaje1 = actualizar_precio_sugerido(producto_id, nuevo_precio_sugerido)
                                    success2, mensaje2 = actualizar_precio_venta(producto_id, nuevo_precio_venta)
                                    
                                    if success1 and success2:
                                        st.success("✅ Ambos precios actualizados")
                                        st.session_state.modo_edicion = None
                                        st.rerun()
                                    else:
                                        st.error(f"Error: {mensaje1 if not success1 else mensaje2}")
            
            # MODO NORMAL: GESTIÓN DE PRODUCTOS
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
                
                # MODO: AGREGAR PRODUCTO - MODIFICADO
                if st.session_state.modo_edicion == 'agregar':
                    st.subheader("📝 Agregar Nuevo Producto")
                    
                    with st.form("form_agregar_producto", clear_on_submit=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            todas_categorias = obtener_todas_categorias()
                            
                            categoria = st.selectbox("Categoría:", todas_categorias, key="cat_agregar")
                            producto = st.text_input("Nombre del Producto:", key="prod_agregar")
                            color = st.text_input("Color:", key="color_agregar")
                            ubicacion = st.selectbox("Ubicación inicial:", ["Bodega", "Exhibido"], key="ubicacion_agregar")
                        
                        with col2:
                            talla = st.text_input("Talla:", placeholder="M, 32, Unitalla...", key="talla_agregar")
                            cantidad = st.number_input("Cantidad total:", min_value=1, value=1, step=1, key="cant_agregar")
                            precio_sugerido = st.number_input("Precio Sugerido ($):", min_value=0.0, value=0.0, step=0.01, format="%.2f", key="precio_sug_agregar")
                            precio_venta = st.number_input("Precio Venta Inicial ($):", min_value=0.0, value=0.0, step=0.01, format="%.2f", key="precio_venta_agregar")
                        
                        submitted = st.form_submit_button("➕ Agregar al Inventario", type="primary", use_container_width=True)
                        
                        if submitted:
                            if not producto or not color or not talla:
                                st.error("❌ Completa todos los campos")
                            else:
                                nuevo_producto = crear_nuevo_producto(
                                    producto=producto,
                                    talla=talla,
                                    color=color,
                                    categoria=categoria,
                                    entrada_total=cantidad,
                                    precio_sugerido=precio_sugerido,
                                    precio_venta=precio_venta if precio_venta > 0 else precio_sugerido,
                                    ubicacion_inicial=ubicacion
                                )
                                
                                if agregar_producto(nuevo_producto):
                                    st.success(f"✅ {producto} agregado en {ubicacion}")
                                    st.balloons()
                                    st.session_state.modo_edicion = None
                                    st.rerun()
                
                # MODO: EDITAR PRODUCTO - MODIFICADO
                elif st.session_state.modo_edicion == 'editar':
                    st.subheader("✏️ Editar Producto Existente")
                    
                    if df.empty:
                        st.info("No hay productos para editar.")
                    else:
                        # Lista de productos para seleccionar
                        productos_opciones = {f"{row['Producto']} ({row['Talla']}, {row['Color']}) - Bodega:{row['Stock_Bodega']} | Exhibido:{row['Stock_Exhibido']}": row['ID'] 
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
                                        
                                        nueva_ubicacion = st.selectbox(
                                            "Ubicación principal:",
                                            ["Bodega", "Exhibido"],
                                            index=0 if producto_data['Ubicacion'] == 'Bodega' else 1,
                                            key="ubicacion_editar"
                                        )
                                    
                                    with col2:
                                        nueva_talla = st.text_input("Talla:", 
                                                                  value=producto_data['Talla'],
                                                                  key="talla_editar")
                                        
                                        nueva_cantidad = st.number_input("Cantidad total:", 
                                                                        min_value=1, 
                                                                        value=int(producto_data['Entrada_Total']),
                                                                        step=1,
                                                                        key="cant_editar")
                                        
                                        nuevo_precio_sugerido = st.number_input("Precio Sugerido ($):", 
                                                                              min_value=0.0, 
                                                                              value=float(producto_data['Precio_Sugerido']),
                                                                              step=0.01,
                                                                              format="%.2f",
                                                                              key="precio_sug_editar")
                                        
                                        nuevo_precio_venta = st.number_input("Precio Venta ($):", 
                                                                            min_value=0.0, 
                                                                            value=float(producto_data['Precio_Venta']),
                                                                            step=0.01,
                                                                            format="%.2f",
                                                                            key="precio_venta_editar")
                                    
                                    st.info(f"📝 Ventas: {producto_data['Ventas_Total']} | Stock Total: {producto_data['Stock_Total']}")
                                    st.info(f"📦 Bodega: {producto_data['Stock_Bodega']} | 🛍️ Exhibido: {producto_data['Stock_Exhibido']}")
                                    
                                    # Botones de acción
                                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                                    
                                    with col_btn1:
                                        guardar = st.form_submit_button("💾 Guardar Cambios", type="primary", use_container_width=True)
                                    
                                    with col_btn2:
                                        solo_stock = st.form_submit_button("📦 Solo Ajustar Stock", use_container_width=True)
                                    
                                    with col_btn3:
                                        if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                            st.session_state.modo_edicion = None
                                            st.rerun()
                                    
                                    if solo_stock:
                                        success, message = editar_producto(producto_id, {
                                            'Categoria': producto_data['Categoria'],
                                            'Producto': producto_data['Producto'],
                                            'Talla': producto_data['Talla'],
                                            'Color': producto_data['Color'],
                                            'Entrada_Total': nueva_cantidad,
                                            'Precio_Sugerido': producto_data['Precio_Sugerido'],
                                            'Precio_Venta': producto_data['Precio_Venta'],
                                            'Ubicacion': nueva_ubicacion
                                        })
                                        if success:
                                            st.success(message)
                                            st.session_state.modo_edicion = None
                                            st.rerun()
                                        else:
                                            st.error(message)
                                    
                                    if guardar:
                                        datos_actualizados = {
                                            'Categoria': nueva_categoria,
                                            'Producto': nuevo_producto,
                                            'Talla': nueva_talla,
                                            'Color': nuevo_color,
                                            'Entrada_Total': nueva_cantidad,
                                            'Precio_Sugerido': nuevo_precio_sugerido,
                                            'Precio_Venta': nuevo_precio_venta,
                                            'Ubicacion': nueva_ubicacion
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
                        # Mostrar TODOS los productos
                        productos_eliminar = {f"{row['Producto']} ({row['Talla']}, {row['Color']}) - Ventas: {row['Ventas_Total']}": row['ID'] 
                                            for _, row in df.iterrows()}
                        
                        producto_eliminar = st.selectbox(
                            "Selecciona un producto para eliminar:",
                            list(productos_eliminar.keys()),
                            key="select_eliminar"
                        )
                        
                        if producto_eliminar:
                            producto_id = productos_eliminar[producto_eliminar]
                            producto_data = next((item for item in st.session_state.inventario 
                                                if item['ID'] == producto_id), None)
                            
                            if producto_data:
                                st.warning(f"⚠️ ¿Estás seguro de eliminar **{producto_data['Producto']}**?")
                                
                                # Mostrar advertencia si tiene ventas
                                if producto_data['Ventas_Total'] > 0:
                                    st.error(f"⚠️ **ADVERTENCIA:** Este producto tiene {producto_data['Ventas_Total']} ventas registradas.")
                                
                                col_info1, col_info2 = st.columns(2)
                                with col_info1:
                                    st.write(f"**Categoría:** {producto_data['Categoria']}")
                                    st.write(f"**Talla:** {producto_data['Talla']}")
                                    st.write(f"**Ubicación:** {producto_data['Ubicacion']}")
                                with col_info2:
                                    st.write(f"**Color:** {producto_data['Color']}")
                                    st.write(f"**Precio Venta:** ${producto_data['Precio_Venta']:,.2f}")
                                    st.write(f"**Ventas:** {producto_data['Ventas_Total']}")
                                
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
                
                # MODO: VER INVENTARIO
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
                            valor_inventario = (df['Stock_Total'] * df['Precio_Venta']).sum()
                            st.metric("💰 Valor Inventario", f"${valor_inventario:,.2f}")
                        with col_res3:
                            productos_con_stock = len(df[df['Stock_Total'] > 0])
                            st.metric("📈 Productos con Stock", f"{productos_con_stock}")
                        
                        # Búsqueda
                        search_inv = st.text_input("🔍 Buscar en inventario:", key="search_inv")
                        
                        if search_inv:
                            filtered_inv = df[
                                df['Producto'].str.contains(search_inv, case=False, na=False) |
                                df['Categoria'].str.contains(search_inv, case=False, na=False) |
                                df['Color'].str.contains(search_inv, case=False, na=False) |
                                df['Talla'].str.contains(search_inv, case=False, na=False) |
                                df['Ubicacion'].str.contains(search_inv, case=False, na=False)
                            ]
                        else:
                            filtered_inv = df
                        
                        # Mostrar tabla
                        if not filtered_inv.empty:
                            display_inv = filtered_inv.copy()
                            display_inv['Precio_Sugerido'] = display_inv['Precio_Sugerido'].apply(lambda x: f"${x:,.2f}")
                            display_inv['Precio_Venta'] = display_inv['Precio_Venta'].apply(lambda x: f"${x:,.2f}")
                            
                            st.dataframe(
                                display_inv[['Categoria', 'Producto', 'Talla', 'Color', 'Ubicacion',
                                           'Stock_Bodega', 'Stock_Exhibido', 'Stock_Total', 
                                           'Ventas_Total', 'Precio_Sugerido', 'Precio_Venta']],
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    'Categoria': st.column_config.TextColumn("Categoría"),
                                    'Producto': st.column_config.TextColumn("Producto"),
                                    'Talla': st.column_config.TextColumn("Talla"),
                                    'Color': st.column_config.TextColumn("Color"),
                                    'Ubicacion': st.column_config.TextColumn("📍 Ubicación"),
                                    'Stock_Bodega': st.column_config.NumberColumn("📦 Bodega", format="%d"),
                                    'Stock_Exhibido': st.column_config.NumberColumn("🛍️ Exhibido", format="%d"),
                                    'Stock_Total': st.column_config.NumberColumn("📊 Total", format="%d"),
                                    'Ventas_Total': st.column_config.NumberColumn("📈 Ventas", format="%d"),
                                    'Precio_Sugerido': st.column_config.TextColumn("💰 Sugerido"),
                                    'Precio_Venta': st.column_config.TextColumn("💵 Venta")
                                }
                            )
                        else:
                            st.info("No hay productos que coincidan con la búsqueda.")

# ============================================
# EJECUCIÓN
# ============================================
if __name__ == "__main__":
    main()