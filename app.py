import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime
import plotly.graph_objects as go
import streamlit as st  # Ya importado, pero para referencia

# Definir scopes
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Cargar credenciales desde Streamlit secrets
credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scopes
)

gc = gspread.authorize(credentials)

# URL de la hoja de cálculo
spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1gExXuXBN_pj-09T9dg8BbbXQaJDDLUf4ODbyyOpnKB4/edit?usp=sharing'

# Abrir la hoja de cálculo
spreadsheet = gc.open_by_url(spreadsheet_url)

# Seleccionar la hoja (worksheet index 1)
worksheet = spreadsheet.get_worksheet(1)

# Obtener todos los datos y convertirlos en un DataFrame
@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_data():
    try:
        data = worksheet.get_all_values()
        if not data:
            st.error("No se encontraron datos en la hoja de cálculo.")
            return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        df.columns = df.columns.str.strip()
        # Intentar múltiples formatos de fecha
        df['Fecha DAV'] = pd.to_datetime(df['Fecha DAV'], format='%d/%m/%Y', errors='coerce')
        # Si falla, intentar formato americano
        if df['Fecha DAV'].isna().all():
            df['Fecha DAV'] = pd.to_datetime(df['Fecha DAV'], format='%m/%d/%Y', errors='coerce')
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%m/%d/%Y %H:%M:%S', errors='coerce')
        df['Litros'] = pd.to_numeric(df['Litros'], errors='coerce')
        df = df.dropna(subset=['Litros', 'Fecha DAV', 'Timestamp'])  # Validación básica
        df = df[(df['Verificacion OD'] == '1') & (df['Verificado'] != 'Destino')]
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return pd.DataFrame()



# Función para generar la tabla y el mapa de calor
def generate_hover_text(volumen_data, tabla):
    hover_text = []
    for i, row in volumen_data.iterrows():
        hover_text_row = []
        for j, value in row.items():
            subset = tabla[(tabla['Expedició'] == i) & (tabla['Destí'] == j)]
            arribades = subset['Arribades'].values[0] if not subset.empty else 'N/A'
            marca = subset['Marca temporal'].values[0] if not subset.empty else 'N/A'
            data_dav = subset['Data DAV'].values[0] if not subset.empty else 'N/A'
            text = (f"Expedició: {i}<br>"
                    f"Destí: {j}<br>"
                    f"Volum: {value:.1f} L<br>"
                    f"Arribades: {arribades}<br>"
                    f"Marca temporal: {marca}<br>"
                    f"Data DAV: {data_dav}")
            hover_text_row.append(text)
        hover_text.append(hover_text_row)
    return hover_text

def crear_tabla_y_mapa(df, titulo):
    if df.empty:
        return pd.DataFrame(), go.Figure()
    try:
        tabla = df.groupby(['Expedicion', 'Envio']).agg(
            Volum=('Litros', 'sum'),
            Arribades=('Verificacion OD', 'size'),
            MarcaTemporal=('Timestamp', 'first'),
            DataDAV=('Fecha DAV', 'first')
        ).reset_index()

        tabla = tabla.rename(columns={
            'Expedicion': 'Expedició',
            'Envio': 'Destí',
            'Volum': 'Volum (L)',
            'MarcaTemporal': 'Marca temporal',
            'DataDAV': 'Data DAV'
        })

        volumen_data = tabla.pivot_table(
            index='Expedició',
            columns='Destí',
            values='Volum (L)',
            aggfunc='sum',
            fill_value=0
        )

        hover_text = generate_hover_text(volumen_data, tabla)

        fig_heatmap = go.Figure(data=go.Heatmap(
            z=volumen_data.values,
            x=volumen_data.columns,
            y=volumen_data.index,
            colorscale='YlOrRd',
            hoverinfo='text',
            text=hover_text,
            hovertemplate='%{text}'
        ))
        theme = 'plotly_dark' if st._config.get_option('theme.base') == 'dark' else 'plotly'
        fig_heatmap.update_layout(
            template=theme,
            title=f'Mapa de Calor de Volum de Most per Instal·lacions d\'Expedició i Destí ({titulo})',
            xaxis_title='Destí',
            yaxis_title='Expedició',
            width=1200,
            height=900
        )

        return tabla, fig_heatmap
    except Exception as e:
        st.error(f"Error al generar visualización: {str(e)}")
        return pd.DataFrame(), go.Figure()

# Título de la app
st.title('Gestió Mostos')

# Menú lateral para seleccionar sección
section = st.sidebar.selectbox('Selecciona una secció', ['Gestió de Mostos', 'Previsiones'])

if section == 'Gestió de Mostos':
    if st.button("Actualizar Datos"):
        load_data.clear()
    df = load_data()
    
    if not df.empty:
        # Obtener las dos fechas más recientes disponibles en los datos
        # Obtener fecha actual (hoy) y fecha anterior (ayer) en formato europeo
        fecha_hoy = datetime.datetime.now().strftime('%d/%m/%Y')
        fecha_ayer = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%d/%m/%Y')
        
        # Verificar si hay datos disponibles
        fechas_disponibles = df['Fecha DAV'].dt.strftime('%d/%m/%Y').unique()
        
        # Solo usar fechas exactas: hoy y ayer
        fecha_reciente = fecha_hoy
        fecha_anterior = fecha_ayer
        
        df_hoy = df[df['Fecha DAV'].dt.strftime('%d/%m/%Y') == fecha_reciente]
        df_ayer = df[df['Fecha DAV'].dt.strftime('%d/%m/%Y') == fecha_anterior]
        
        # Mostrar información sobre las fechas
        st.info(f"📅 Mostrando datos de: **{fecha_reciente}** (hoy) y **{fecha_anterior}** (ayer)")
    else:
        st.error("No se encontraron datos válidos")
        df_hoy = pd.DataFrame()
        df_ayer = pd.DataFrame()
    # Crear y mostrar tabla y mapa de calor para hoy
    with st.spinner('Cargando datos...'):
        tabla_hoy, fig_heatmap_hoy = crear_tabla_y_mapa(df_hoy, f"Hoy ({fecha_reciente})")
    st.subheader(f'Tabla - Hoy ({fecha_reciente})')
    if not df_hoy.empty:
        st.dataframe(tabla_hoy)
    else:
        st.info("No hay datos disponibles para hoy.")
    st.subheader(f'Mapa de Calor - Hoy ({fecha_reciente})')
    if not df_hoy.empty:
        st.plotly_chart(fig_heatmap_hoy)
    else:
        st.info("No hay datos disponibles para mostrar el mapa de calor de hoy.")

    with st.spinner('Cargando datos...'):
        tabla_ayer, fig_heatmap_ayer = crear_tabla_y_mapa(df_ayer, f"Ayer ({fecha_anterior})")
    st.subheader(f'Tabla - Ayer ({fecha_anterior})')
    if not df_ayer.empty:
        st.dataframe(tabla_ayer)
    else:
        st.info("No hay datos disponibles para ayer.")
    st.subheader(f'Mapa de Calor - Ayer ({fecha_anterior})')
    if not df_ayer.empty:
        st.plotly_chart(fig_heatmap_ayer)
    else:
        st.info("No hay datos disponibles para mostrar el mapa de calor de ayer.")

elif section == 'Previsiones':
    st.subheader('Previsiones - Càrrega d\'arxiu Excel')
    st.markdown("""**Explicacions:**
- **Rendiment**: Es calcula com el 66% del Total Kg.
- **Previsió Sortida Cisternes**: Es calcula dividint el Rendiment per 20.000 (capacitat d'una cisterna).
""")
    uploaded_file = st.file_uploader("Puja l'arxiu Excel", type=['xlsx'])
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file, header=6, engine='openpyxl')
            grouped_df = df.groupby('Razón Social').agg({'Total Kg:': 'sum', 'Zona': 'first'}).reset_index()
            grouped_df['Rendiment'] = (grouped_df['Total Kg:'] * 0.66).round(0)
            grouped_df['Previsió Sortida Cisternes'] = (grouped_df['Rendiment'] / 20000).round(0)
            for col in ['Total Kg:', 'Rendiment', 'Previsió Sortida Cisternes']:
                grouped_df[col] = grouped_df[col].astype(int)
            st.subheader('Resultats agrupats per Celler')
            st.dataframe(grouped_df)

            chunks = [grouped_df[i:i+5] for i in range(0, len(grouped_df), 5)]
            for i, chunk in enumerate(chunks):
                fig = go.Figure()
                theme = 'plotly_dark' if st._config.get_option('theme.base') == 'dark' else 'plotly'
                for col, name in [('Total Kg:', 'Total Kg'), ('Rendiment', 'Rendiment (66%)')]:
                    fig.add_trace(go.Bar(x=chunk['Razón Social'], y=chunk[col], name=name))
                fig.add_trace(go.Scatter(
                    x=chunk['Razón Social'],
                    y=chunk['Previsió Sortida Cisternes'],
                    name='Previsió Sortida Cisternes',
                    yaxis='y2',
                    mode='lines+markers',
                    marker=dict(color='rgba(102, 102, 102, 0.8)')
                ))
                fig.update_layout(
                    template=theme,
                    title=f'Gràfic {i+1}: Entrada Total Raïm, Rendiment, i Previsió Sortida Cisternes',
                    xaxis_title='Celler',
                    yaxis_title='Kg',
                    yaxis2=dict(title='Previsió', side='right', overlaying='y', showgrid=False),
                    xaxis=dict(tickangle=-45),
                    barmode='group',
                    width=900,
                    height=600
                )
                st.plotly_chart(fig)
        except Exception as e:
            st.error(f"Error al processar l'arxiu: {str(e)}")