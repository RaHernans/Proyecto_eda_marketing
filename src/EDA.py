


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

#Carga de datos CSV y Excel
def load_data(bank_path: str, customers_path: str):
    bank = pd.read_csv(bank_path)
# >>> DEBUG fecha cruda (apenas cargar CSV)
if 'date' in bank.columns:
    print("\n[DEBUG] 'date' cruda (CSV) ANTES de limpiar:")
    print("  dtype:", bank['date'].dtype)
    print("  n_nulos:", bank['date'].isna().sum())
    print("  n_blancos:", (bank['date'].astype(str).str.strip() == '').sum())
    print("  muestra_10:", bank['date'].astype(str).head(10).tolist())
else:
    print("\n[DEBUG] No existe columna 'date' en el CSV")

    xls = pd.ExcelFile(customers_path)
    sheet_names = xls.sheet_names
    customers = pd.concat(
        [pd.read_excel(customers_path, sheet_name=s).assign(CustomerYearSheet=s)
         for s in sheet_names],
        ignore_index=True
    )
    return bank, customers, sheet_names

#Limpieza del dataset de campañas.
def clean_bank(bank: pd.DataFrame) -> pd.DataFrame:
    df = bank.copy()

    # Eliminar columna índice creada al exportar el archivo CSV.
    for c in ["Unnamed: 0"]:
        if c in df.columns:
            df = df.drop(columns=c)

    if 'date' in df.columns:
        raw = df['date'].astype(str).str.strip()
        print("\n[DEBUG] 'date' en clean_bank() ANTES de parsear:")
        print("  n_nulos:", df['date'].isna().sum())
        print("  n_blancos:", (raw == '').sum())
        print("  muestra_no_vacios:", raw[raw != ''].head(5).tolist())

        # Trata blancos como NaN antes del parseo
        df['date'] = raw.replace('', pd.NA)

    # >>> aquí ya haces el parseo robusto, o lo saltas si está vacía:
    if 'date' in df.columns and df['date'].notna().sum() > 0:
        # PRUEBAS DE FORMATO (elige una o deja el fallback)
        parsed = pd.to_datetime(df['date'], format='%Y-%m-%d', errors='coerce')
        if parsed.notna().mean() < 0.5:
            parsed = pd.to_datetime(df['date'], format='%d/%m/%Y', errors='coerce')
        if parsed.notna().sum() == 0:
            parsed = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')

        df['date'] = parsed
        if df['date'].notna().sum() > 0:
            df['contact_year'] = df['date'].dt.year
            df['contact_month'] = df['date'].dt.month
    else:
        # Si está vacía, asegúrate de no dejar derivadas colgando
        for c in ['contact_year', 'contact_month']:
            if c in df.columns:
                df = df.drop(columns=c)

    # ... resto de limpieza
    return df   

    # Normalizar texto.
    for c in ['job', 'marital', 'education', 'contact', 'poutcome', 'y']:
        if c in df.columns and df[c].dtype == 'object':
            df[c] = df[c].astype(str).str.strip().str.lower()

    # Conversión de columnas binarias al tipo Int64.
    for c in ['default', 'housing', 'loan']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').astype('Int64')

    # Conversión de fechas.
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d', errors='coerce')
        df['contact_year'] = df['date'].dt.year
        df['contact_month'] = df['date'].dt.month

    # Transformación de columnas numéricas.
    numeric_candidates = [
        'age', 'duration', 'campaign', 'pdays', 'previous',
        'emp.var.rate', 'cons.price.idx', 'cons.conf.idx',
        'euribor3m', 'nr.employed', 'latitude', 'longitude'
    ]
    for c in numeric_candidates:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    return df

#Limpieza del dataset de clientes. 
def clean_customers(customers: pd.DataFrame) -> pd.DataFrame:
    df = customers.copy()
    if 'Dt_Customer' in df.columns:
        df['Dt_Customer'] = pd.to_datetime(df['Dt_Customer'], errors='coerce')

    for c in ['Income', 'Kidhome', 'Teenhome', 'NumWebVisitsMonth']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    return df

#ntegración de los datasets a traves el ID.
def merge_data(bank: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    """Une bank y customers por id_ ↔ ID."""
    if 'id_' in bank.columns and 'ID' in customers.columns:
        merged = bank.merge(customers, left_on='id_', right_on='ID', how='left')
    else:
        merged = bank.copy()
    return merged

#Análisis descriptivo 

#Resumen estadítico
def descriptive_analysis(df: pd.DataFrame) -> dict:
    summary = {}
    summary['shape'] = df.shape
    summary['nulls'] = df.isna().sum().sort_values(ascending=False)
    num_df = df.select_dtypes(include=['number'])
    summary['describe_num'] = num_df.describe().T

    if 'y' in df.columns:
        summary['target_balance'] = df['y'].value_counts(normalize=True).rename('Proporción')

    if num_df.shape[1] >= 2:
        summary['corr'] = num_df.corr(numeric_only=True)
    else:
        summary['corr'] = pd.DataFrame()

    return summary

#Visualizaciones con matplotlib y seaborn.
def quick_plots(df: pd.DataFrame):
    # Histograma de edad
    if 'age' in df.columns:
        plt.figure()
        plt.hist(df['age'].dropna(), bins=30)
        plt.title("Distribución de edad")
        plt.xlabel("Edad")
        plt.ylabel("Frecuencia")
        plt.tight_layout()

    # Histograma de duración de llamadas
    if 'duration' in df.columns:
        plt.figure()
        plt.hist(df['duration'].dropna(), bins=30)
        plt.title("Duración de llamada (segundos)")
        plt.xlabel("Segundos")
        plt.ylabel("Frecuencia")
        plt.tight_layout()

    # Boxplot de edad por suscripción
    if 'y' in df.columns and 'age' in df.columns:
        plt.figure()
        sns.boxplot(x='y', y='age', data=df)
        plt.title("Edad según suscripción (y)")
        plt.tight_layout()

    # Heatmap de correlaciones
    num_df = df.select_dtypes(include=['number'])
    if num_df.shape[1] >= 2:
        plt.figure(figsize=(9, 7))
        sns.heatmap(num_df.corr(numeric_only=True), cmap="coolwarm", annot=False)
        plt.title("Matriz de correlación (variables numéricas)")
        plt.tight_layout()

#Ejecución: 
def main():
    bank_path = "data/raw/bank-additional.csv"
    customers_path = "data/raw/customer-details.xlsx"

    # Cargar datos
    bank, customers, sheet_names = load_data(bank_path, customers_path)
    print("Columnas del dataset bank-additional:", list(bank.columns))
    print("Hojas del Excel de clientes:", sheet_names)

    # Limpiar
    bank = clean_bank(bank)
    customers = clean_customers(customers)

    # Unir
    df = merge_data(bank, customers)

    # Guardar limpio
    output = "data/processed/marketing_merged_clean.csv"
    df.to_csv(output, index=False)
    print(f"Dataset limpio guardado en: {output}")

    # Análisis descriptivo
    summary = descriptive_analysis(df)
    print("Shape:", summary['shape'])
    print("Principales nulos:\n", summary['nulls'].head(10))
    if 'target_balance' in summary:
        print("Balance de y:\n", summary['target_balance'])

    # Visualizaciones
    quick_plots(df)

    # Mostrar gráficosS
    # plt.show()


if __name__ == "__main__":
    main()


