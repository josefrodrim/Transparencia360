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

## 3. Cruce INEI ↔ PTE y disponibilidad de salarios (2026-10-29)

- `database/seeds/pte_entidades_09.csv`: 95/102 municipalidades con `id_entidad` de confianza alta. Pendientes: Cosme
  (090511) y los distritos nuevos de Tayacaja 090719–090723 y 090725, sin ficha identificable en el PTE.
- **Sondeo exhaustivo** (autorizado por el usuario): las 95 municipalidades, mes a mes de 2024-01 a 2026-10
  (≈3 200 consultas, 3 s entre cada una).
- **Resultado: solo 10 de 102 municipalidades publicaron alguna vez personal con remuneraciones en el periodo.**
  Las otras 85 cruzadas tienen 0 registros en los 34 meses.

| Ubigeo | Municipalidad | Meses con datos (de 34) | Periodo publicado | Último mes | Personas (último mes) | Mediana S/ | Máximo S/ | Filas con total inconsistente |
|---|---|---|---|---|---|---|---|---|
| 090101 | Municipalidad Provincial de Huancavelica | 26 | 2024-01 → 2026-09 | 2026-09 | 351 | 1,864.19 | 7,280.00 | 0/10269 (0.0 %) |
| 090117 | Municipalidad Distrital de Yauli | 14 | 2024-01 → 2026-07 | 2026-07 | 1 | 1,360.00 | 1,360.00 | 0/106 (0.0 %) |
| 090118 | Municipalidad Distrital de Ascensión | 34 | 2024-01 → 2026-10 | 2026-10 | 49 | 2,152.07 | 4,000.00 | 132/2023 (6.5 %) |
| 090119 | Municipalidad Distrital de Huando | 1 | 2024-09 → 2024-09 | 2024-09 | 25 | 1,700.00 | 230,300.00 | 1/26 (3.8 %) |
| 090201 | Municipalidad Provincial de Acobamba | 32 | 2024-01 → 2026-08 | 2026-08 | 136 | 1,425.00 | 7,500.00 | 83/4195 (2.0 %) |
| 090204 | Municipalidad Distrital de Caja | 8 | 2024-01 → 2026-01 | 2026-01 | 1 | 2,060.00 | 2,060.00 | 0/13 (0.0 %) |
| 090301 | Municipalidad Provincial de Angaraes | 4 | 2024-01 → 2024-06 | 2024-06 | 64 | 2,000.00 | 4,000.00 | 0/333 (0.0 %) |
| 090304 | Municipalidad Distrital de Ccochaccasa | 1 | 2025-02 → 2025-02 | 2025-02 | 2 | 1,200.50 | 1,800.00 | 1/2 (50.0 %) |
| 090310 | Municipalidad Distrital de San Antonio de Antaparco | 7 | 2025-10 → 2026-04 | 2026-04 | 16 | 2,100.00 | 3,605.21 | 0/104 (0.0 %) |
| 090701 | Municipalidad Provincial de Tayacaja | 19 | 2024-01 → 2025-07 | 2025-07 | 8 | 6,632.10 | 18,704.42 | 0/3356 (0.0 %) |

- Personas = registros únicos del último mes publicado. Los importes son los publicados (columna total) y no se
  anualizan.
- **Total inconsistente** (Ascensión, Acobamba, Huando, Ccochaccasa): filas en las que el total no coincide con la suma
  de los componentes (p. ej. remuneración S/ 7 200 y total S/ 3 000). Es un error de la entidad al publicar: se
  conserva tal cual y se marca; no se elige una de las dos cifras.
- **Monto atípico** (Huando, 2024-09): Gerente Municipal con remuneración S/ 230 000 (total S/ 230 300), frente a una
  mediana de S/ 1 700. Probable error de digitación en la fuente; se marca `monto_atipico` para revisión y no se corrige.
- **Registros partidos** (Yauli, 2024-07): un campo con saltos de línea sin comillas partía el registro; el lector lo
  reconstruye y lo anota como `fila_reparada`.
- Cobertura irregular: Angaraes solo publicó 2024-01→2024-06; Tayacaja deja de publicar en 2025-07 (último mes con solo
  8 personas); Huando y Ccochaccasa publicaron un único mes; Yauli y Caja, 1 registro en su último mes publicado.
- Conclusión: el PTE cubre de forma útil a ~4 municipalidades (MP Huancavelica, Ascensión, MP Acobamba, y en parte
  MP Tayacaja). Para el resto hacen falta vías alternativas (MEF agregado; solicitudes Ley 27806).

## 4. MEF — devengado mensual (VERIFICADO, en uso)

| Atributo | Valor |
|---|---|
| Catálogo | https://www.datosabiertos.gob.pe/dataset/presupuesto-y-ejecución-de-gasto-–-devengado-mensual |
| Archivos | `https://fs.datosabiertos.mef.gob.pe/datastorefiles/{AAAA}-Gasto-Devengado-Mensual.csv` (2025+), `{AAAA}-Gasto-Devengado.csv` (≤2024). ~2,5 GB/año, todo el sector público |
| Acceso | Descarga pública; el servidor acepta `Range` (se usa para reanudar). También hay API `api.datosabiertos.mef.gob.pe/DatosAbiertos/v1/datastore_search` (CKAN), sin `resource_id` de gasto identificado |
| Extractor | `munilens-mef --departamento 09 --anios 2024,2025,2026`: streaming filtrado (`NIVEL_GOBIERNO=M`, `DEPARTAMENTO_EJECUTORA=09`); guarda solo el subconjunto en `data/raw/mef_gasto_devengado/09/` |

- 2026 (corte 22/10/2026): devengado de enero a septiembre; 51 918 filas de Huancavelica; **104 ejecutoras en las 102
  municipalidades** (cobertura total, a diferencia del PTE).
- **Corrección verificada:** el CAS vigente se registra en **2.1.1.13** (dentro de personal), no en 2.3.2.8; en 2026 no
  hay registros en 2.3.2.8. Se suma 2.3.2.8 como CAS solo para años anteriores.
- Indicadores: `personal` (2.1 completa), `cas` (2.1.1.13 + 2.3.2.8), `dietas` (2.1.1.10), `locacion_pn` (2.3.2.9,
  honorarios a personas naturales), `pensiones` (2.2).
- **No es comparable 1:1 con el PTE.** MP Huancavelica, 2026-08: PTE S/ 759 668 frente a MEF 2.1 S/ 1 155 593. La 2.1
  incluye aportes del empleador, gastos variables, dietas y sentencias, y el devengado no coincide necesariamente con
  el mes de pago. Ascensión (+64 %) y Acobamba (+45 %) muestran la misma diferencia.
- Son montos agregados por municipalidad: no identifican personas.

## 4.1 Directorios de funcionarios en gob.pe (VERIFICADO para Lircay, uso manual)

- La ficha PTE de cada entidad puede enlazar a un directorio publicado en gob.pe. MP Angaraes (id 11921) enlaza
  `https://www.gob.pe/institucion/muniangaraes/informes-publicaciones/5721517-directorio-de-la-mpal-2025` (página
  titulada «Directorio de la MPAL - 2026»): un DOCX con 34 cargos de gerencias y subgerencias, y un PDF con el
  alcalde y 9 regidores.
- **Sirve para saber quién ocupa cada cargo, pero no trae salarios.** Se cruza por nombre con el PTE Personal.
- **Contiene datos personales sensibles** (DNI, celulares, correos personales y domicilios de las autoridades). Solo se
  toman el nombre y el cargo; los archivos descargados no se guardan y nunca se versionan.
- Cruce de Lircay (2026-10-31): de las 27 personas del directorio (34 cargos), 6 coinciden por nombre con alguien publicado en el
  PTE de 2024 (S/ 3 000–4 000 mensuales, CAS); los demás, incluidos el gerente municipal y el alcalde, nunca
  aparecieron en el PTE.

## 5. Pendientes de verificar

| Fuente | URL candidata | Estado |
|---|---|---|
| PTE — `id_entidad` de las 101 municipalidades restantes de Huancavelica | buscador de entidades del PTE | Pendiente. Ejemplo hallado: Yauli = `11910` |
| PTE — ficha de entidad MPH | https://www.transparencia.gob.pe/enlaces/pte_transparencia_enlaces.aspx?id_entidad=980 | Accesible, sin analizar |
| Web institucional MPH | https://www.munihuancavelica.gob.pe/es/ | Sin verificar |
| Datos Abiertos | https://www.datosabiertos.gob.pe/ | No se encontró ningún dataset de planillas municipales de Huancavelica |
| INEI — población por distrito | — | Pendiente (para indicadores per cápita) |
