# Catálogo de fuentes — Fase 1 (Huancavelica)

Última verificación: 2026-10-28.

## 1. PTE — rubro Personal (VERIFICADO, en uso)

| Atributo | Valor |
|---|---|
| Entidad | Municipalidad Provincial de Huancavelica (MPH) |
| `id_entidad` PTE | `980` |
| RUC | `20171725144` (el que trae el propio CSV) |
| Página de consulta | https://www.transparencia.gob.pe/personal/pte_transparencia_personal.aspx?id_entidad=980&id_tema=32 |
| Descarga | `GET /personal/pte_transparencia_personal_genera.aspx?id_entidad=980&in_anno_consulta=AAAA&ch_mes_consulta=MM&ch_tipo_regimen=0&vc_dni_funcionario=&vc_nombre_funcionario=&ch_tipo_descarga=N` |
| Formatos | `N=1` XLS, `N=2` **CSV (UTF-8, usado)**, `N=3` XML. HTML: tabla de 30 filas por página |
| robots.txt | Solo `Disallow: /enlaces/pte_transparencia_verificar.aspx`; el rubro Personal está permitido |
| Acceso | Público, sin CAPTCHA ni login. Extractor con 3 s entre peticiones y User-Agent identificado |
| Periodo sin datos | Respuesta HTTP 200 con cuerpo vacío (0 bytes) |

### Campos publicados (CSV)

`PK_ID_PERSONAL` (id interno del PTE, no es DNI), `VC_PERSONAL_RUC_ENTIDAD`, `IN_PERSONAL_ANNO`, `IN_PERSONAL_MES`,
`VC_PERSONAL_REGIMEN_LABORAL` (código), `VC_PERSONAL_PATERNO`, `VC_PERSONAL_MATERNO`, `VC_PERSONAL_NOMBRES`,
`VC_PERSONAL_CARGO`, `VC_PERSONAL_DEPENDENCIA`, `MO_PERSONAL_REMUNERACIONES`, `MO_PERSONAL_HONORARIOS`,
`MO_PERSONAL_INCENTIVO`, `MO_PERSONAL_GRATIFICACION`, `MO_PERSONAL_OTROS_BENEFICIOS`, `MO_PERSONAL_TOTAL`,
`VC_PERSONAL_OBSERVACIONES`, `FEC_REG` (fecha de carga en el PTE, formato `M/D/AAAA h:mm:ss AM/PM`).

- **No se publican** DNI, fecha de inicio/fin del vínculo, grado académico ni tipo de remuneración (bruta/neta).
  La tabla HTML los etiqueta como "DETALLE DE INGRESOS" y "TOTAL INGRESOS"; no hay que asumir que sea el neto.
- Los códigos de régimen salen del selector de la página: 1 CAS, 2 Régimen 276, 3 Régimen 728/OTROS, 4 PAC, 5 FAG,
  6 PNUD, 7 Altos Funcionarios, 8 Pensionistas, 9 Ley Servir.
- Validado: en el periodo 2026-08, las 30 filas de la página 1 del HTML coinciden campo a campo con el CSV
  (`scrapers/tests/test_integracion_pte.py`).

### Cobertura y calidad observadas (2024-01 → 2026-10)

- El selector de años va de 2013 a 2026. Se extrajo 2024-01 → 2026-10: **26 periodos con datos, 8 vacíos**
  (2024-07 a 2024-12, 2026-06 y 2026-10). 2020-06 también está vacío; falta evaluar 2013-2023.
- **Desfase de publicación:** por ejemplo, 2025-12 se cargó el 2026-05-13 y 2026-08 el 2026-10-09.
- **Cargas duplicadas:** 2025-02, 2026-02, 2026-04 y 2026-07 contienen el listado cargado dos veces (dos lotes
  con distinta `FEC_REG`), lo que duplica el total publicado. En 2026-04 los lotes difieren en algunas personas.
  El extractor marca los duplicados exactos (`duplicado_de`) y los excluye de los agregados, pero no los elimina.
- **Meses idénticos:** 2025-03 → 2025-12 tienen exactamente el mismo listado (cargado el 2026-05-13). También son
  idénticos 2024-02/2024-03 y 2026-08/2026-09. Puede ser real o una re-publicación del mismo listado; se informa
  y no se corrige.
- **Orden de filas inestable:** el mismo periodo descargado dos veces llega con las filas en distinto orden. La
  detección de cambios usa una huella canónica (filas ordenadas), no el SHA-256 de los bytes.
- 2024-04 tiene solo 95 registros (frente a unos 330 en los meses vecinos): posible publicación incompleta.
- Rango de totales individuales en 2026-08: S/ 1,050.00 – S/ 7,280.00.

### Consideraciones legales

- La Resolución TTAIP 002518-2023 considera confidencial el detalle de las afectaciones de la planilla (descuentos).
  El PTE no las publica y MuniLens tampoco debe obtenerlas.
- Antes de publicar fichas individualizadas hace falta una revisión de cumplimiento (Ley 29733 y su reglamento).
  Por ahora los datos solo se guardan localmente en `data/` (excluido de git).

## 2. INEI — Directorio Nacional de Municipalidades (VERIFICADO, en uso)

| Atributo | Valor |
|---|---|
| Página | https://www.gob.pe/institucion/inei/informes-publicaciones/3364652-nation-registry-of-municipalities-renamu-2026 |
| Archivo usado | "Directorio Nacional de Municipalidades Provinciales y Distritales - Octubre 2026" (XLSX), actualizado al **14/10/2026**. SHA-256 `b9741bbc…69663` |
| robots.txt (gob.pe) | Solo prohíbe `/admin/` y `?sheet=`; la descarga desde el CDN está permitida |
| Extractor | `munilens-inei --url <xlsx>` → `database/seeds/municipalidades.csv` + `.meta.json` |

- Columnas: Ubigeo, Departamento, Provincia, Distrito, Cargo, Nombres y Apellidos del Alcalde, Sexo, Dirección, Código
  de ciudad, Teléfonos, Correo Electrónico. **No se extraen** sexo, dirección, teléfonos ni correos (algunos son
  personales). El nombre del alcalde (fuente: JNE) solo se guarda en `data/processed`, no en el seed versionado.
- **Nacional:** 1 893 municipalidades (196 provinciales y 1 697 distritales).
- **Huancavelica (ubigeo 09): 102 municipalidades**, 7 provinciales y 95 distritales: Huancavelica 19, Tayacaja 23,
  Huaytará 16, Castrovirreyna 13, Angaraes 12, Churcampa 11, Acobamba 8. Esto supera los 94 distritos del INEI 2017
  por la creación de distritos nuevos en Tayacaja (+7) y Churcampa (+1). Ninguna municipalidad de Huancavelica tiene
  nota al pie.
- Las provinciales no siempre llevan el nombre de su capital: Angaraes → Lircay (090301), Tayacaja → Pampas (090701).
- Errores de la fuente corregidos y registrados en `.meta.json`: "ApurÍmac" (030612) y "San MartÍn" (221006). Solo se
  unifican diferencias de mayúsculas; cualquier otra inconsistencia detiene la carga.
- La URL del XLSX cambia en cada edición (hay versiones de agosto y diciembre de 2025, y de febrero, septiembre y
  octubre de 2026), así que se pasa por parámetro y se guarda en el meta.

## 3. Pendientes de verificar

| Fuente | URL candidata | Estado |
|---|---|---|
| PTE — `id_entidad` de las 101 municipalidades restantes de Huancavelica | buscador de entidades del PTE | Pendiente. Ejemplo hallado: Yauli = `11910` |
| PTE — ficha de entidad MPH | https://www.transparencia.gob.pe/enlaces/pte_transparencia_enlaces.aspx?id_entidad=980 | Accesible, sin analizar |
| Web institucional MPH | https://www.munihuancavelica.gob.pe/es/ | Sin verificar |
| Datos Abiertos | https://www.datosabiertos.gob.pe/ | No se encontró ningún dataset de planillas municipales de Huancavelica |
| INEI — población por distrito | — | Pendiente (para indicadores per cápita) |
