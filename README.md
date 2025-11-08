# Proyecto_eda_marketing

Este repositorio contiene un análisis exploratorio de datos (EDA) sobre campañas de *marketing directo* de una entidad bancaria portuguesa. Las campañas consisten en llamadas telefónicas para promover un **depósito a plazo** y la variable objetivo `y` indica si el cliente suscribió el producto (yes/no).

## 🎯 Objetivo

Realizar un **análisis exploratorio general** para:
- Entender el perfil de los clientes y las campañas.
- Describir patrones básicos y relaciones entre variables.
- Dejar preparado un dataset limpio para análisis posteriores.

> **Nota sobre el dataset real**  
> El fichero `bank-additional.csv` no incluye las columnas `contact_month` y `contact_year` (mencionadas en el enunciado).  
> En cambio, trae columnas extra como `latitude` y `longitude`.  
> El pipeline se **adapta automáticamente**: si existe `date`, deriva `contact_year` y `contact_month`; si no existe, omite esa parte.  
> También se incorporan las columnas extra numéricas (como lat/long) cuando están presentes.

## 🧰 Herramientas

- **Lenguaje:** Python  
- **Entorno:** Visual Studio Code  
- **Librerías:** `pandas`, `matplotlib`, `seaborn`

## 📁 Estructura del repositorio
ProyectoEdaMarketing/
├─ data/
│  ├─ raw/                     # Datos originales
│  │  ├─ bank-additional.csv
│  │  └─ customer-details.xlsx
│  └─ processed/               # Datos limpios y combinados
│     └─ marketing_merged_clean.csv
│
├─ src/
│  └─ EDA.py          # Script principal del análisis

## 🧩 Datos

### `bank-additional.csv`

* **Demográficas**: `age`, `job`, `marital`, `education`
* **Crédito**: `default`, `housing`, `loan`
* **Campaña**: `contact`, `duration`, `campaign`, `pdays`, `previous`, `poutcome`
* **Macroeconómicas**: `emp.var.rate`, `cons.price.idx`, `cons.conf.idx`, `euribor3m`, `nr.employed`
* **Objetivo**: `y` (yes/no)
* **Fecha**: `date` (si existe, se deriva `contact_year` y `contact_month`)
* **Otras**: `latitude`, `longitude`, etc.

### `customer-details.xlsx` (3 hojas: p. ej., `2012`, `2013`, `2014`)

* `Income`, `Kidhome`, `Teenhome`, `Dt_Customer`, `NumWebVisitsMonth`, `ID`
* Se **consolidan** todas las hojas añadiendo `CustomerYearSheet` con el nombre de la hoja.
* **Unión**: `id_` (CSV) ↔ `ID` (Excel), *left join* .

## 🧹 Limpieza y transformación

En `src/eda_pipeline.py`:
* Elimina columnas índice accidentales (ej. `Unnamed: 0`).
* Normaliza categóricas a minúsculas (`job`, `marital`, `education`, `contact`, `poutcome`, `y`).
* Binarios a `Int64` con NaN permitido (`default`, `housing`, `loan`).
* Convierte fechas a `datetime` (`date`, `Dt_Customer`).
* Deriva `contact_year` y `contact_month` **solo** si existe `date`.
* Convierte numéricas clave con `pd.to_numeric` y **admite columnas extra** (`latitude`, `longitude`, etc.).
* Une con datos de clientes si `id_` e `ID` existen.

## 📊 Análisis descriptivo

Impresiones en consola:

* `shape` (filas x columnas).
* Top de **valores nulos**.
* **Balance** de la variable objetivo `y`.
* **Correlación** entre numéricas (si hay al menos dos).

Gráficos generados:
1. Histograma de **edad**.
2. Histograma de **duración de llamada**.
3. **Boxplot** de `age` por `y`.
4. **Heatmap** de correlación numérica.

Principales hallazgos:
* Edad promedio: alrededor de 40 años.
* Duración media de las llamadas: 250 segundos
* Campañas: la mayoría de clientes fueron contactados entre 1 y 3 veces.
* Tasa de suscripción (y= yes): 11,3%.

## ✅Conclusiones: 
La edad media y el nivel educativo influyen parcialmente en la respuesta del cliente.
La duración de la llamada es un factor clave: a mayor tiempo, mayor probabilidad de exito.
Los clientes casados y con profesión estable tienden a tener una menor tasa de suscripción.
Los indicadores macroeconómicos muestran variaciones relacionadas con la efectividad de las campañas. 
 
## 👤 Autor

Raquel Hernández Santos
Curso Data Analytics – The Power
Módulo Python for Data — Proyecto EDA



import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
import unicodedata

SPANISH_MONTHS = {
    "enero": "01",
    "febrero": "02",
    "marzo": "03",
    "abril": "04",
    "mayo": "05",
    "junio": "06",
    "julio": "07",
    "agosto": "08",
    "septiembre": "09",  # a veces aparece "setiembre"
    "setiembre": "09",
    "octubre": "10",
    "noviembre": "11",
    "diciembre": "12",
}

def _strip_accents(text: str) -> str:
    if not isinstance(text, str):
        return text
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )

def parse_spanish_month_dates(series: pd.Series) -> pd.Series:
    """
    Convierte fechas tipo '2-agosto-2019' a datetime.
    - Normaliza a minúsculas
    - Quita acentos
    - Reemplaza nombre de mes por número
    - Parsea con formato '%d-%m-%Y'
    """
    s = series.astype(str).str.strip().str.lower().apply(_strip_accents)

    # detecta si hay palabras de meses en español
    month_regex = r"(" + "|".join(SPANISH_MONTHS.keys()) + r")"
    has_spanish_month = s.str.contains(month_regex, na=False)

    if not has_spanish_month.any():
        # no hay meses en español -> devolvemos NaT (que luego tu bloque robusto podrá cubrir)
        return pd.to_datetime(series, errors="coerce")

    def replace_month(word_date: str) -> str:
        # esperado: '2-agosto-2019' (separado por '-')
        parts = word_date.split("-")
        if len(parts) != 3:
            return word_date  # lo dejamos intacto y fallará a NaT en el parseo
        d, m, y = parts[0].strip(), parts[1].strip(), parts[2].strip()
        m_num = SPANISH_MONTHS.get(m, None)
        if m_num is None:
            return word_date
        # normaliza día a dos dígitos si procede
        if d.isdigit():
            d = d.zfill(2)
        return f"{d}-{m_num}-{y}"

    # solo transformamos las filas que contienen mes español
    transformed = s.where(~has_spanish_month, s[has_spanish_month].apply(replace_month))
    # ahora parseamos con formato fijo
    parsed = pd.to_datetime(transformed, format="%d-%m-%Y", errors="coerce")
    return parsed


# -------------------------------
# Utilidad opcional: comprobar openpyxl
# -------------------------------
def ensure_openpyxl() -> bool:
    try:
        import openpyxl  # noqa: F401
        return True
    except Exception as e:
        print("❌ Falta 'openpyxl' para leer Excel (.xlsx). Instálalo con:")
        print("   pip install openpyxl")
        print("Detalle:", repr(e))
        return False


# -------------------------------
# Carga de datos CSV y Excel
# -------------------------------
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

    # Excel (clientes)
    if not ensure_openpyxl():
        raise SystemExit(1)

    xls = pd.ExcelFile(customers_path)
    sheet_names = xls.sheet_names
    customers = pd.concat(
        [pd.read_excel(customers_path, sheet_name=s).assign(CustomerYearSheet=s)
         for s in sheet_names],
        ignore_index=True
    )
    return bank, customers, sheet_names


# -------------------------------
# Limpieza del dataset de campañas
# -------------------------------
def clean_bank(bank: pd.DataFrame) -> pd.DataFrame:
    """Limpieza flexible del dataset de campañas (bank-additional.csv)."""
    df = bank.copy()

    # 1) Eliminar columna índice accidental si existe
    for c in ("Unnamed: 0",):
        if c in df.columns:
            df.drop(columns=c, inplace=True)

    # 2) Normalizar texto en categóricas habituales (si existen)
    for c in ['job', 'marital', 'education', 'contact', 'poutcome', 'y']:
        if c in df.columns and df[c].dtype == 'object':
            df[c] = df[c].astype(str).str.strip().str.lower()

    # 3) Binarios (0/1) a Int64 para mantener NaN si aparecen
    for c in ['default', 'housing', 'loan']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').astype('Int64')

    # 4) Manejo robusto de 'date' (evita warnings y no deriva si está vacía)
    if 'date' in df.columns:
        # Normaliza a texto y limpia blancos
        raw = df['date'].astype(str).str.strip()
        non_empty = raw[raw != '']

        if non_empty.empty:
            # No hay fechas reales -> no parseamos ni derivamos
            df['date'] = pd.NaT
            for c in ('contact_year', 'contact_month'):
                if c in df.columns:
                    df.drop(columns=c, inplace=True)
        else:
            parsed = None
            # prueba algunos formatos comunes
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'):
                tmp = pd.to_datetime(non_empty, format=fmt, errors='coerce')
                if tmp.notna().mean() > 0.90:  # aceptamos si >90% parsea
                    parsed = tmp
                    break
            if parsed is None:
                # fallback: dayfirst
                parsed = pd.to_datetime(non_empty, dayfirst=True, errors='coerce')

            # asigna respetando índices originales
            df['date'] = pd.NaT
            df.loc[non_empty.index, 'date'] = parsed

            # Deriva solo si hay fechas válidas
            if df['date'].notna().sum() > 0:
                df['contact_year'] = df['date'].dt.year
                df['contact_month'] = df['date'].dt.month
            else:
                for c in ('contact_year', 'contact_month'):
                    if c in df.columns:
                        df.drop(columns=c, inplace=True)

    # 5) Asegurar numéricos (incluye columnas extra si existen)
    numeric_candidates = [
        'age', 'duration', 'campaign', 'pdays', 'previous',
        'emp.var.rate', 'cons.price.idx', 'cons.conf.idx',
        'euribor3m', 'nr.employed', 'latitude', 'longitude'
    ]
    for c in numeric_candidates:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    return df


# -------------------------------
# Limpieza del dataset de clientes
# -------------------------------
def clean_customers(customers: pd.DataFrame) -> pd.DataFrame:
    df = customers.copy()

    if 'Dt_Customer' in df.columns:
        df['Dt_Customer'] = pd.to_datetime(df['Dt_Customer'], errors='coerce')

    for c in ['Income', 'Kidhome', 'Teenhome', 'NumWebVisitsMonth']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    return df


# -------------------------------
# Integración de los datasets
# -------------------------------
def merge_data(bank: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    """Une bank y customers por id_ ↔ ID (left join)."""
    if 'id_' in bank.columns and 'ID' in customers.columns:
        merged = bank.merge(customers, left_on='id_', right_on='ID', how='left')
    else:
        merged = bank.copy()
    return merged


# -------------------------------
# (Opcional) Eliminar columnas casi vacías
# -------------------------------
def drop_mostly_nulls(df: pd.DataFrame, thresh: float = 0.98) -> pd.DataFrame:
    to_drop = [c for c in df.columns if df[c].isna().mean() >= thresh]
    if to_drop:
        print(f"⚠️ Eliminando columnas casi vacías (≥{int(thresh*100)}% nulos): {to_drop}")
        df = df.drop(columns=to_drop)
    return df


# -------------------------------
# Análisis descriptivo
# -------------------------------
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


# -------------------------------
# Visualizaciones (matplotlib + seaborn)
# -------------------------------
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


# -------------------------------
# Ejecución
# -------------------------------
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

    # Mostrar gráficos (descomenta si no aparecen en tu entorno)
    # plt.show()


if __name__ == "__main__":
    main()




















