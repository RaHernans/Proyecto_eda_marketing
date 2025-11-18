##Importación de librerías.

import re
import unicodedata
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

# =========================
# Utilidades y helpers
# =========================

   # Conversión de fechas: eliminar acentos, separar día, mes, año, pasar texto mes a número, formato estandar.
SPANISH_MONTHS = {
    "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
    "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
    "septiembre": "09", "setiembre": "09", "octubre": "10",
    "noviembre": "11", "diciembre": "12",
}
 
def _strip_accents(text: str) -> str:
    if not isinstance(text, str):
        return text
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )

def parse_spanish_month_dates(series: pd.Series) -> pd.Series:
    
    s = series.astype(str).str.strip().str.lower().apply(_strip_accents)
   
    pattern = re.compile(r'^(\d{1,2})[-/\s]([a-zñ]+)[-/\s](\d{4})$')

    def convert_one(x: str) -> str:
        m = pattern.match(x)
        if not m:
            return x
        d, mon, y = m.groups()
        mon_num = SPANISH_MONTHS.get(mon)
        if not mon_num:
            return x
        d = d.zfill(2)
        return f"{d}-{mon_num}-{y}"

   
    month_words = r'(' + '|'.join(SPANISH_MONTHS.keys()) + r')'
    has_spanish = s.str.contains(month_words, na=False)
    transformed = s.where(~has_spanish, s[has_spanish].apply(convert_one))

  
    parsed = pd.to_datetime(transformed, format='%d-%m-%Y', errors='coerce')
    return parsed


# =========================
# 1) Carga de datos
# =========================

def load_data(bank_path: str, customers_path: str):
    bank = pd.read_csv(bank_path)

    # DEBUG: muestra rápida de 'date' cruda
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


# =========================
# 2) Limpieza de campañas
# =========================

def clean_bank(bank: pd.DataFrame) -> pd.DataFrame:
    """Limpieza del dataset bank-additional.csv."""
    df = bank.copy()

    # 2.1 Eliminar columna índice accidental
    if "Unnamed: 0" in df.columns:
        df.drop(columns="Unnamed: 0", inplace=True)

    # 2.2 Normalizar texto en categóricas
    for c in ['job', 'marital', 'education', 'contact', 'poutcome', 'y']:
        if c in df.columns and df[c].dtype == 'object':
            df[c] = df[c].astype(str).str.strip().str.lower()

    # 2.3 Binarios a Int64 (preserva NaN)
    for c in ['default', 'housing', 'loan']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').astype('Int64')

    # 2.4 Manejo robusto de 'date' (meses en español, sin warnings)
    if 'date' in df.columns:
        raw = df['date']

        # Ignoramos UserWarning solo dentro de este bloque
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)

            parsed = parse_spanish_month_dates(raw)

            # Si aún queda poco parseado, probamos formatos numéricos habituales
            if parsed.notna().mean() < 0.90:
                candidates = ["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"]
                best = parsed
                for fmt in candidates:
                    tmp = pd.to_datetime(raw, format=fmt, errors='coerce')
                    if tmp.notna().mean() > best.notna().mean():
                        best = tmp
                parsed = best

        df['date'] = parsed

        # Derivar solo si hay fechas válidas
        if df['date'].notna().sum() > 0:
            df['contact_year'] = df['date'].dt.year
            df['contact_month'] = df['date'].dt.month
        else:
            for c in ('contact_year', 'contact_month'):
                if c in df.columns:
                    df.drop(columns=c, inplace=True)



    # 2.5 Asegurar numéricos (si existen)
    numeric_candidates = [
        'age', 'duration', 'campaign', 'pdays', 'previous',
        'emp.var.rate', 'cons.price.idx', 'cons.conf.idx',
        'euribor3m', 'nr.employed', 'latitude', 'longitude'
    ]
    for c in numeric_candidates:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    return df


# =========================
# 3) Limpieza de clientes
# =========================

def clean_customers(customers: pd.DataFrame) -> pd.DataFrame:
    df = customers.copy()

    if 'Dt_Customer' in df.columns:
        df['Dt_Customer'] = pd.to_datetime(df['Dt_Customer'], errors='coerce')

    for c in ['Income', 'Kidhome', 'Teenhome', 'NumWebVisitsMonth']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    return df


# =========================
# 4) Integración (left join)
# =========================

def merge_data(bank: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    """Une bank y customers por id_ ↔ ID (left join)."""
    if 'id_' in bank.columns and 'ID' in customers.columns:
        merged = bank.merge(customers, left_on='id_', right_on='ID', how='left')
    else:
        merged = bank.copy()
    return merged


# =========================
# 5) (Opcional) columnas casi vacías
# =========================

def drop_mostly_nulls(df: pd.DataFrame, thresh: float = 0.98) -> pd.DataFrame:
    to_drop = [c for c in df.columns if df[c].isna().mean() >= thresh]
    if to_drop:
        print(f"⚠️ Eliminando columnas casi vacías (≥{int(thresh*100)}% nulos): {to_drop}")
        df = df.drop(columns=to_drop)
    return df


# =========================
# 6) Análisis descriptivo
# =========================

def descriptive_analysis(df: pd.DataFrame) -> dict:
    summary = {}
    summary['shape'] = df.shape
    summary['nulls'] = df.isna().sum().sort_values(ascending=False)

    num_df = df.select_dtypes(include=['number'])
    summary['describe_num'] = num_df.describe().T

    if 'y' in df.columns:
        summary['target_balance'] = df['y'].value_counts(normalize=True).rename('Proporción')

    summary['corr'] = num_df.corr(numeric_only=True) if num_df.shape[1] >= 2 else pd.DataFrame()
    return summary


# =========================
# 7) Visualizaciones
# =========================

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


# =========================
# 8) Ejecución
# =========================

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

    # (Opcional) eliminar columnas casi vacías
    df = drop_mostly_nulls(df, thresh=0.98)

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

    # Mostrar gráficos 
    plt.show()


if __name__ == "__main__":
    main()






