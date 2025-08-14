import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# Definir scopes
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

try:
    # Cargar credenciales
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    gc = gspread.authorize(credentials)
    
    # Conectar a la hoja
    spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1gExXuXBN_pj-09T9dg8BbbXQaJDDLUf4ODbyyOpnKB4/edit?usp=sharing'
    spreadsheet = gc.open_by_url(spreadsheet_url)
    worksheet = spreadsheet.get_worksheet(1)
    
    # Obtener datos
    data = worksheet.get_all_values()
    print(f"Total de filas obtenidas: {len(data)}")
    
    if not data:
        print("❌ No hay datos en la hoja")
        exit()
    
    # Crear DataFrame
    df = pd.DataFrame(data[1:], columns=data[0])
    print(f"\nColumnas disponibles: {list(df.columns)}")
    print(f"Filas en DataFrame inicial: {len(df)}")
    
    # Limpiar nombres de columnas
    df.columns = df.columns.str.strip()
    print(f"\nColumnas después de limpiar: {list(df.columns)}")
    
    # Verificar conversiones de fecha
    print("\n=== VERIFICANDO CONVERSIONES DE FECHA ===")
    print(f"Muestra de 'Fecha DAV': {df['Fecha DAV'].head().tolist()}")
    
    # Intentar conversión de fechas
    df['Fecha DAV'] = pd.to_datetime(df['Fecha DAV'], format='%m/%d/%Y', errors='coerce')
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%m/%d/%Y %H:%M:%S', errors='coerce')
    
    print(f"Fechas DAV válidas: {df['Fecha DAV'].notna().sum()}")
    print(f"Timestamps válidos: {df['Timestamp'].notna().sum()}")
    
    # Verificar conversión de litros
    print(f"\nMuestra de 'Litros': {df['Litros'].head().tolist()}")
    df['Litros'] = pd.to_numeric(df['Litros'], errors='coerce')
    print(f"Litros válidos: {df['Litros'].notna().sum()}")
    
    # Aplicar filtros básicos
    print("\n=== APLICANDO FILTROS ===")
    df_filtered = df.dropna(subset=['Litros', 'Fecha DAV', 'Timestamp'])
    print(f"Después de eliminar NaN: {len(df_filtered)} filas")
    
    # Verificar valores de filtros
    print(f"\nValores únicos de 'Verificacion OD': {df_filtered['Verificacion OD'].unique()}")
    print(f"Valores únicos de 'Verificado': {df_filtered['Verificado'].unique()}")
    
    # Aplicar filtros de verificación
    df_verified = df_filtered[(df_filtered['Verificacion OD'] == '1') & (df_filtered['Verificado'] != 'Destino')]
    print(f"Después de filtros de verificación: {len(df_verified)} filas")
    
    # Verificar fechas de hoy y ayer
    hoy = datetime.datetime.now().strftime('%m/%d/%Y')
    ayer = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%m/%d/%Y')
    
    print(f"\n=== FILTROS DE FECHA ===")
    print(f"Fecha de hoy: {hoy}")
    print(f"Fecha de ayer: {ayer}")
    
    # Verificar fechas en los datos
    fechas_unicas = df_verified['Fecha DAV'].dt.strftime('%m/%d/%Y').unique()
    print(f"Fechas únicas en los datos: {sorted([f for f in fechas_unicas if pd.notna(f)])}")
    
    df_hoy = df_verified[df_verified['Fecha DAV'].dt.strftime('%m/%d/%Y') == hoy]
    df_ayer = df_verified[df_verified['Fecha DAV'].dt.strftime('%m/%d/%Y') == ayer]
    
    print(f"\nFilas para hoy ({hoy}): {len(df_hoy)}")
    print(f"Filas para ayer ({ayer}): {len(df_ayer)}")
    
    if len(df_hoy) > 0:
        print(f"\nMuestra de datos de hoy:")
        print(df_hoy[['Expedicion', 'Envio', 'Litros']].head())
    
    if len(df_ayer) > 0:
        print(f"\nMuestra de datos de ayer:")
        print(df_ayer[['Expedicion', 'Envio', 'Litros']].head())
    
    print("\n=== DIAGNÓSTICO DE FILTROS COMPLETADO ===")
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()