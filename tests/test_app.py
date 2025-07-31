import pytest
import pandas as pd
import datetime
import sys
import os

# Añadir el directorio raíz al path para importar app.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import crear_tabla_y_mapa, generate_hover_text

@pytest.fixture
def sample_df():
    """Fixture que proporciona un DataFrame de muestra para pruebas."""
    data = {
        'Fecha DAV': ['10/01/2023', '10/01/2023', '10/02/2023'],
        'Timestamp': ['10/01/2023 10:00:00', '10/01/2023 11:00:00', '10/02/2023 12:00:00'],
        'Litros': [100, 200, 150],
        'Expedicion': ['A', 'B', 'A'],
        'Envio': ['X', 'Y', 'X'],
        'Verificacion OD': ['1', '1', '1'],
        'Verificado': ['Origen', 'Origen', 'Origen']
    }
    df = pd.DataFrame(data)
    df['Fecha DAV'] = pd.to_datetime(df['Fecha DAV'], format='%m/%d/%Y', errors='coerce')
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%m/%d/%Y %H:%M:%S', errors='coerce')
    df['Litros'] = pd.to_numeric(df['Litros'], errors='coerce')
    return df

def test_crear_tabla_y_mapa(sample_df):
    """Prueba la función crear_tabla_y_mapa con datos válidos."""
    tabla, fig = crear_tabla_y_mapa(sample_df, 'Test')
    # Verificar tabla
    assert not tabla.empty
    assert 'Volum (L)' in tabla.columns
    assert tabla['Volum (L)'].sum() == 450  # Suma de Litros
    # Verificar heatmap
    assert fig.data[0].type == 'heatmap'
    assert len(fig.data[0].z) > 0

def test_generate_hover_text():
    """Prueba la función generate_hover_text."""
    # Crear datos de prueba
    volumen_data = pd.DataFrame([[100, 200], [150, 0]], 
                               index=['X', 'Y'], 
                               columns=['A', 'B'])
    
    tabla = pd.DataFrame({
        'Expedició': ['X', 'X', 'Y'],
        'Destí': ['A', 'B', 'A'],
        'Volum (L)': [100, 200, 150],
        'Arribades': [1, 2, 1],
        'Marca temporal': [datetime.datetime(2023, 10, 1, 10, 0), 
                          datetime.datetime(2023, 10, 1, 11, 0),
                          datetime.datetime(2023, 10, 2, 12, 0)],
        'Data DAV': [datetime.datetime(2023, 10, 1), 
                    datetime.datetime(2023, 10, 1),
                    datetime.datetime(2023, 10, 2)]
    })
    
    hover_text = generate_hover_text(volumen_data, tabla)
    
    # Verificaciones
    assert len(hover_text) == 2  # Dos filas
    assert len(hover_text[0]) == 2  # Dos columnas en la primera fila
    assert "Expedició: X" in hover_text[0][0]
    assert "Destí: A" in hover_text[0][0]
    assert "Volum: 100.0 L" in hover_text[0][0]

def test_edge_case_empty_df():
    """Prueba el comportamiento con un DataFrame vacío."""
    empty_df = pd.DataFrame(columns=['Fecha DAV', 'Timestamp', 'Litros', 'Expedicion', 'Envio', 'Verificacion OD', 'Verificado'])
    tabla, fig = crear_tabla_y_mapa(empty_df, 'Empty')
    assert tabla.empty
    # Verificar que se devuelve una figura vacía pero válida
    assert fig is not None

def test_filtrado(sample_df):
    """Prueba la lógica de filtrado por fecha."""
    # Simular filtrado (lógica similar a app)
    df_filtered = sample_df[sample_df['Fecha DAV'].dt.strftime('%m/%d/%Y') == '10/01/2023']
    assert len(df_filtered) == 2
    assert df_filtered['Litros'].sum() == 300

# Ejecutar con: pytest tests/test_app.py -v