# Trade-In iPhone Analytics — MacOnline

Suite de dashboards interactivos para analizar el programa de Trade-In de iPhone en tiendas MacOnline.

**Live:** [tradein-iphone-analytics.netlify.app](https://tradein-iphone-analytics.netlify.app)

## Dashboards

| # | Página | Descripción |
|---|--------|-------------|
| 01 | **Dashboard General** | KPIs, volumen mensual, top modelos, migración, capacidad y grado |
| 02 | **Explorador de Tendencias** | Filtros por modelo/fecha, estacionalidad, YoY, tendencias de valor |
| 03 | **Sankey de Migración** | Flujos interactivos entre modelos entregados y comprados |
| 04 | **Insights Avanzados** | Salto generacional, tier, capacidad, retención, impacto grado |
| 05 | **Curvas de Valor** | Depreciación por modelo/grado, correlación valor-volumen |
| 06 | **Benchmark Competitivo** | Apple, Entel, Aufbau/Reuse vs MacOnline por modelo y capacidad |
| 07 | **Elasticidad de Precio** | Respuesta del volumen a cambios de precio, regresión y p-valor |

## Estructura

```
├── data/
│   ├── TD Historico.xlsx              # Datos históricos trade-in
│   ├── Benchmark_...xlsx              # Benchmark competencia
│   └── processed/                     # JSON generados (no editar)
├── scripts/
│   └── process_data.py                # Pipeline: Excel → JSON
├── src/
│   ├── index.html                     # Hub principal
│   ├── dashboard.html                 # Dashboard general
│   ├── explorer.html                  # Explorador de tendencias
│   ├── sankey.html                    # Sankey de migración
│   ├── insights.html                  # Insights avanzados
│   ├── curves.html                    # Curvas de valor
│   ├── benchmark.html                 # Benchmark competitivo
│   ├── elasticity.html                # Elasticidad de precio
│   └── data/processed/*.json          # Datos para los dashboards
├── netlify.toml                       # Config de deploy
└── README.md
```

## Actualizar datos

1. Reemplaza los archivos Excel en `data/`
2. Ejecuta el pipeline:
   ```bash
   pip install pandas openpyxl numpy
   cd scripts
   python process_data.py
   ```
3. Copia los JSON generados:
   ```bash
   cp data/processed/*.json src/data/processed/
   ```
4. Haz commit y push — Netlify despliega automáticamente

## Stack

- **D3.js v7** para visualizaciones
- **HTML/CSS** vanilla (dark theme, DM Sans)
- **Python/pandas** para procesamiento de datos
- **Netlify** para hosting
