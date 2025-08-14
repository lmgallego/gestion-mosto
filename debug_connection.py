import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Definir scopes
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

try:
    print("1. Cargando credenciales...")
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    print("✓ Credenciales cargadas correctamente")
    
    print("2. Autorizando cliente...")
    gc = gspread.authorize(credentials)
    print("✓ Cliente autorizado")
    
    print("3. Conectando a la hoja de cálculo...")
    spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1gExXuXBN_pj-09T9dg8BbbXQaJDDLUf4ODbyyOpnKB4/edit?usp=sharing'
    spreadsheet = gc.open_by_url(spreadsheet_url)
    print("✓ Hoja de cálculo abierta")
    
    print("4. Accediendo a la worksheet...")
    worksheet = spreadsheet.get_worksheet(1)
    print(f"✓ Worksheet accedida: {worksheet.title}")
    
    print("5. Obteniendo datos...")
    data = worksheet.get_all_values()
    print(f"✓ Datos obtenidos: {len(data)} filas")
    
    if data:
        print("6. Primeras 3 filas:")
        for i, row in enumerate(data[:3]):
            print(f"   Fila {i}: {row}")
    
    print("\n=== DIAGNÓSTICO COMPLETADO EXITOSAMENTE ===")
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    print(f"Tipo de error: {type(e).__name__}")
    import traceback
    print("\nTraceback completo:")
    traceback.print_exc()