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
│  └─ EDA.py          # Script del análisis
│  
├─ README.md

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


## 1.📥 Carga de datos
Se utilizan dos archivos:

1. bank-additional.csv (datos de campañas telefónicas)
2. customer-details.xlsx (datos de clientes, dividido en 3 hojas: 2012, 2013 y 2014)

El script:
- carga el CSV con Pandas
- carga las tres hojas del Excel y las combina en un único DataFrame
- añade la columna CustomerYearSheet para indicar el año original
- muestra información de depuración (DEBUG) sobre la columna date, que viene en
texto y con meses en español:
Ejemplos:
2-agosto-2019
14-septiembre-2016
29-noviembre-2015

## 🧹 2. Limpieza y transformación de datos (en `src/eda_pipeline.py`)

## 2.1 Limpieza del dataset de campañas (clean_bank)

Se realizan las siguientes operaciones:

1. Eliminación de columnas accidentales
- Se elimina Unnamed: 0 

2. Normalización de texto en columnas categóricas
- Se convierten a minúsculas, se eliminan espacios y se homogenizan valores.

3. Conversión de columnas binarias
- Se convierten default, housing y loan a tipo Int64 (permite NaN).

4. Conversión de la columna date
Como las fechas vienen con el mes en español, se creó una función específica para:

- eliminar acentos
- separar día, mes y año
- convertir el mes textual a número
- generar una fecha válida para Pandas

A partir de la fecha se crean:

- contact_year
- contact_month

5. Conversión de columnas numéricas
Columnas que deberían ser numéricas se pasan a pd.to_numeric() con errors='coerce'.

## 2.2 Limpieza del dataset de clientes (clean_customers)
Se realiza:

- conversión de la columna Dt_Customer a fecha
- conversión a numérico de Income, Kidhome, Teenhome y NumWebVisitsMonth

## 🔗 3. Integración de datasets (Left Join)

Se realiza una unión LEFT entre:

- bank (tabla principal, columna id_)
- customers (tabla secundaria, columna ID)

Código:
bank.merge(customers, left_on='id_',right_on='ID', how='left')

Esto garantiza que:
- se conservan todas las filas de campañas
- se añade información del cliente cuando existe
- si un cliente no está en el Excel, aparece como NaN



## 🗑 4. Eliminación de columnas casi vacías
Si una columna tiene ≥98% de nulos, se elimina para mejorar la calidad del análisis.
Ejemplos eliminados:
- cons.price.idx
- euribor3m


## 📉 5. Análisis descriptivo

La función descriptive_analysis obtiene:

1. Dimensión del dataset (número de filas y columnas)
2. Conteo de valores nulos por columna
3. Estadísticas descriptivas (media, mediana, desviación estándar, etc)
4. Balance de la variable objetivo y: 
     Resultados:
    - ❌ NO contrató  → 88,7%
    - ✅ SÍ contrató  → 11,3%
El dataset está claramente desbalanceado.

5. Matriz de correlación entre variables numéricas (si hay al menos 2).


## 📊 6. Visualizaiones 
Se generan gráficas con Matplotlib y Seaborn:

1. Histograma de edad
2. Histograma de duración de llamadas
3. Boxplot de edad según respuesta
4. Heatmap de correlaciones

Las gráficas se muestran con: 
ptl.show()

Las visualizaciones permiten observar rangos de edad predominantes, sesgos en la duración de llamadas, ausencia de diferencia significativa de edad entre quienes contratan y quienes no, y correlación moderada entre algunas variables económicas.

Principales hallazgos:
* Edad promedio: alrededor de 40 años.
* Duración media de las llamadas: 250 segundos
* Campañas: la mayoría de clientes fueron contactados entre 1 y 3 veces.
* Tasa de suscripción (y= yes): 11,3%.

El flujo completo se ejecuta mediante el comando:
python src/EDA.py


## ✅ 7. Conclusiones: 

* La campaña tiene una tasa de conversión baja (11,3%)
* La duración de la llamada es un factor clave. Se mostró una distribución muy sesgada hacia valores bajos, indicando que muchas llamadas fueron breves. Esto puede sugerir baja disponibilidad o o interés inicial de algunos clientes. También indica que a mayor tiempo de llamada, mayor probabilidad de éxito.
* Las edades de clientes que contratan y no contratan son similares.
* Los indicadores macroeconómicos muestran variaciones relacionadas con la efectividad de las campañas.



## 👤 Autor

Raquel Hernández Santos
Curso Data Analytics – The Power
Módulo Python for Data — Proyecto EDA

