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

