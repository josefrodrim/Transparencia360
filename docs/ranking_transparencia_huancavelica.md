# Ranking de transparencia salarial: municipalidades de Huancavelica

Generado con `scripts/ranking_transparencia.py 09`. Mide si cada municipalidad publica los salarios de su
personal en el Portal de Transparencia Estándar (PTE, rubro Personal) entre 2024-01 y 2026-10, y qué tan
completo, actual y limpio es lo publicado. Corte: 31/10/2026.

| Criterio | Puntos | Cómo se mide |
|---|---|---|
| Publicación | 40 | Meses con datos sobre los 34 del periodo |
| Completitud | 25 | Mediana de (suma publicada ÷ gasto en personal 2.1 del MEF del mismo mes): 80 % o más = 25; más de 120 % (⚠, no interpretable) = 0 |
| Actualidad | 15 | Antigüedad del último mes publicado: 15 si tiene ≤ 2 meses, 0 si tiene 24 o más |
| Oportunidad | 10 | Mediana de días entre el fin del mes y la carga principal: 10 si ≤ 30, 0 si ≥ 180 |
| Calidad | 10 | Proporción de registros sin errores (total ≠ suma de componentes, total 0, nombre incompleto) |

Completitud, oportunidad y calidad se escalan si hay menos de 6 meses publicados: un solo mes no basta para
evaluar cómo publica una municipalidad.

Las municipalidades que no publicaron ningún mes tienen 0 puntos y se listan aparte, ordenadas por su gasto
en personal (cuanto más gastan, más pesa la falta de información).

## Publican salarios (10 de 102)

| # | Municipalidad | Puntaje | Meses publicados | Último mes | Completitud | Demora (días) | Registros con error | Publicación | Completitud | Actualidad | Oportunidad | Calidad |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Municipalidad Distrital de Ascensión (090118) | **99** | 34/34 | 2026-10 | 79 % | 0 | 7 % | 40 | 25 | 15 | 10 | 9 |
| 2 | Municipalidad Provincial de Acobamba (090201) | **92** | 32/34 | 2026-08 | 64 % | 25 | 2 % | 38 | 20 | 15 | 10 | 10 |
| 3 | Municipalidad Provincial de Huancavelica (090101) | **82** | 26/34 | 2026-09 | 72 % | 110 | 3 % | 31 | 23 | 15 | 5 | 10 |
| 4 | Municipalidad Provincial de Tayacaja (090701) | **74** | 19/34 | 2025-07 | 87 % | 29 | 0 % | 22 | 25 | 6 | 10 | 10 |
| 5 | Municipalidad Distrital de San Antonio de Antaparco (090310) | **66** | 7/34 | 2026-04 | 81 % | 24 | 0 % | 8 | 25 | 12 | 10 | 10 |
| 6 | Municipalidad Distrital de Yauli (090117) | **40** | 14/34 | 2026-07 | 2 % | 212 | 19 % | 16 | 1 | 14 | 0 | 8 |
| 7 | Municipalidad Distrital de Caja (090204) | **27** | 8/34 | 2026-01 | 7 % | 288 | 46 % | 9 | 2 | 10 | 0 | 5 |
| 8 | Municipalidad Provincial de Angaraes (090301) | **20** | 4/34 | 2024-06 | 10 % | 47 | 0 % | 5 | 2 | 0 | 6 | 7 |
| 9 | Municipalidad Distrital de Ccochaccasa (090304) | **8** | 1/34 | 2025-02 | 111 % | 258 | 100 % | 1 | 4 | 3 | 0 | 0 |
| 10 | Municipalidad Distrital de Huando (090119) | **4** | 1/34 | 2024-09 | 541 % ⚠ | 14 | 4 % | 1 | 0 | 0 | 2 | 2 |

## No publican salarios (92 de 102): 0 puntos

| # | Municipalidad | Provincia | Gasto en personal 2025 (MEF) | Ficha en el PTE |
|---|---|---|---|---|
| 1 | Municipalidad Distrital de Acoria (090103) | Huancavelica | 3 172 239 | sí |
| 2 | Municipalidad Distrital de Paucara (090206) | Acobamba | 2 493 383 | sí |
| 3 | Municipalidad Provincial de Churcampa (090501) | Churcampa | 2 076 356 | sí |
| 4 | Municipalidad Distrital de Colcabamba (090705) | Tayacaja | 1 889 307 | sí |
| 5 | Municipalidad Provincial de Castrovirreyna (090401) | Castrovirreyna | 1 603 447 | sí |
| 6 | Municipalidad Provincial de Huaytará (090601) | Huaytará | 1 327 078 | sí |
| 7 | Municipalidad Distrital de Daniel Hernández (090706) | Tayacaja | 1 297 983 | sí |
| 8 | Municipalidad Distrital de Ahuaycha (090704) | Tayacaja | 865 457 | sí |
| 9 | Municipalidad Distrital de Acraquia (090703) | Tayacaja | 615 950 | sí |
| 10 | Municipalidad Distrital de Surcubamba (090717) | Tayacaja | 541 398 | sí |
| 11 | Municipalidad Distrital de Quichuas (090719) | Tayacaja | 533 285 | sin confirmar |
| 12 | Municipalidad Distrital de Pilpichaca (090607) | Huaytará | 484 010 | sí |
| 13 | Municipalidad Distrital de Paucarbamba (090507) | Churcampa | 472 967 | sí |
| 14 | Municipalidad Distrital de Rosario (090208) | Acobamba | 469 496 | sí |
| 15 | Municipalidad Distrital de Andabamba (090202) | Acobamba | 460 404 | sí |
| 16 | Municipalidad Distrital de Anco (090502) | Churcampa | 446 784 | sí |
| 17 | Municipalidad Distrital de Tintay Puncu (090718) | Tayacaja | 433 336 | sí |
| 18 | Municipalidad Distrital de Salcabamba (090714) | Tayacaja | 431 790 | sí |
| 19 | Municipalidad Distrital de Pazos (090711) | Tayacaja | 425 455 | sí |
| 20 | Municipalidad Distrital de Secclla (090312) | Angaraes | 423 858 | sí |
| 21 | Municipalidad Distrital de Marcas (090205) | Acobamba | 404 835 | sí |
| 22 | Municipalidad Distrital de Huachocolpa (090707) | Tayacaja | 390 373 | sí |
| 23 | Municipalidad Distrital de Salcahuasi (090715) | Tayacaja | 387 202 | sí |
| 24 | Municipalidad Distrital de Huaribamba (090709) | Tayacaja | 378 688 | sí |
| 25 | Municipalidad Distrital de Nuevo Occoro (090113) | Huancavelica | 370 415 | sí |
| 26 | Municipalidad Distrital de Cosme (090511) | Churcampa | 359 936 | sin confirmar |
| 27 | Municipalidad Distrital de Anchonga (090302) | Angaraes | 357 815 | sí |
| 28 | Municipalidad Distrital de Chinchihuasi (090503) | Churcampa | 353 263 | sí |
| 29 | Municipalidad Distrital de Anta (090203) | Acobamba | 348 371 | sí |
| 30 | Municipalidad Distrital de Locroja (090506) | Churcampa | 345 084 | sí |
| 31 | Municipalidad Distrital de San Pedro de Coris (090509) | Churcampa | 339 777 | sí |
| 32 | Municipalidad Distrital de Acostambo (090702) | Tayacaja | 337 664 | sí |
| 33 | Municipalidad Distrital de Andaymarca (090720) | Tayacaja | 332 924 | sin confirmar |
| 34 | Municipalidad Distrital de El Carmen (090504) | Churcampa | 331 245 | sí |
| 35 | Municipalidad Distrital de Moya (090112) | Huancavelica | 329 567 | sí |
| 36 | Municipalidad Distrital de Congalla (090306) | Angaraes | 318 888 | sí |
| 37 | Municipalidad Distrital de Ticrapo (090413) | Castrovirreyna | 308 498 | sí |
| 38 | Municipalidad Distrital de Chupamarca (090405) | Castrovirreyna | 305 398 | sí |
| 39 | Municipalidad Distrital de Vilca (090116) | Huancavelica | 304 546 | sí |
| 40 | Municipalidad Distrital de Chincho (090305) | Angaraes | 297 740 | sí |
| 41 | Municipalidad Distrital de Lambras (090724) | Tayacaja | 296 000 | sí |
| 42 | Municipalidad Distrital de Palca (090114) | Huancavelica | 291 350 | sí |
| 43 | Municipalidad Distrital de Huachocolpa (090106) | Huancavelica | 291 086 | sí |
| 44 | Municipalidad Distrital de Cuenca (090105) | Huancavelica | 289 566 | sí |
| 45 | Municipalidad Distrital de Pachamarca (090510) | Churcampa | 284 629 | sí |
| 46 | Municipalidad Distrital de Julcamarca (090309) | Angaraes | 284 149 | sí |
| 47 | Municipalidad Distrital de Pomacocha (090207) | Acobamba | 281 453 | sí |
| 48 | Municipalidad Distrital de Pichos (090722) | Tayacaja | 281 002 | sin confirmar |
| 49 | Municipalidad Distrital de Huayllay Grande (090308) | Angaraes | 280 173 | sí |
| 50 | Municipalidad Distrital de Santa Ana (090411) | Castrovirreyna | 276 173 | sí |
| 51 | Municipalidad Distrital de Izcuchaca (090108) | Huancavelica | 271 971 | sí |
| 52 | Municipalidad Distrital de Aurahua (090403) | Castrovirreyna | 271 907 | sí |
| 53 | Municipalidad Distrital de San Marcos de Rocchac (090716) | Tayacaja | 271 592 | sí |
| 54 | Municipalidad Distrital de Arma (090402) | Castrovirreyna | 261 963 | sí |
| 55 | Municipalidad Distrital de Santiago de Tucuma (090723) | Tayacaja | 261 884 | sin confirmar |
| 56 | Municipalidad Distrital de Roble (090721) | Tayacaja | 256 472 | sin confirmar |
| 57 | Municipalidad Distrital de Acobambilla (090102) | Huancavelica | 253 309 | sí |
| 58 | Municipalidad Distrital de Santiago de Chocorvos (090613) | Huaytará | 247 217 | sí |
| 59 | Municipalidad Distrital de San Miguel de Mayocc (090508) | Churcampa | 246 050 | sí |
| 60 | Municipalidad Distrital de Santo Tomás de Pata (090311) | Angaraes | 244 982 | sí |
| 61 | Municipalidad Distrital de Tambo (090616) | Huaytará | 241 654 | sí |
| 62 | Municipalidad Distrital de Laria (090109) | Huancavelica | 240 953 | sí |
| 63 | Municipalidad Distrital de Conayca (090104) | Huancavelica | 238 071 | sí |
| 64 | Municipalidad Distrital de Callanmarca (090303) | Angaraes | 232 258 | sí |
| 65 | Municipalidad Distrital de La Merced (090505) | Churcampa | 231 854 | sí |
| 66 | Municipalidad Distrital de Pilchaca (090115) | Huancavelica | 231 681 | sí |
| 67 | Municipalidad Distrital de Mariscal Cáceres (090111) | Huancavelica | 228 729 | sí |
| 68 | Municipalidad Distrital de Cochabamba (090725) | Tayacaja | 215 650 | sin confirmar |
| 69 | Municipalidad Distrital de Huachos (090407) | Castrovirreyna | 211 947 | sí |
| 70 | Municipalidad Distrital de Santo Domingo de Capillas (090615) | Huaytará | 206 688 | sí |
| 71 | Municipalidad Distrital de Huanca-Huanca (090307) | Angaraes | 205 306 | sí |
| 72 | Municipalidad Distrital de Huamatambo (090408) | Castrovirreyna | 201 293 | sí |
| 73 | Municipalidad Distrital de Manta (090110) | Huancavelica | 199 683 | sí |
| 74 | Municipalidad Distrital de Capillas (090404) | Castrovirreyna | 199 442 | sí |
| 75 | Municipalidad Distrital de Ñahuimpuquio (090710) | Tayacaja | 195 128 | sí |
| 76 | Municipalidad Distrital de San Antonio de Cusicancha (090610) | Huaytará | 194 271 | sí |
| 77 | Municipalidad Distrital de Cocas (090406) | Castrovirreyna | 185 476 | sí |
| 78 | Municipalidad Distrital de Mollepampa (090409) | Castrovirreyna | 182 826 | sí |
| 79 | Municipalidad Distrital de Ayavi (090602) | Huaytará | 180 554 | sí |
| 80 | Municipalidad Distrital de Huayacundo Arma (090604) | Huaytará | 177 747 | sí |
| 81 | Municipalidad Distrital de Querco (090608) | Huaytará | 177 319 | sí |
| 82 | Municipalidad Distrital de Quito-Arma (090609) | Huaytará | 167 731 | sí |
| 83 | Municipalidad Distrital de San Francisco de Sangayaico (090611) | Huaytará | 164 542 | sí |
| 84 | Municipalidad Distrital de Ocoyo (090606) | Huaytará | 160 196 | sí |
| 85 | Municipalidad Distrital de Córdova (090603) | Huaytará | 159 318 | sí |
| 86 | Municipalidad Distrital de Tantara (090412) | Castrovirreyna | 154 319 | sí |
| 87 | Municipalidad Distrital de Huayllahuara (090107) | Huancavelica | 153 685 | sí |
| 88 | Municipalidad Distrital de San Isidro (090612) | Huaytará | 132 701 | sí |
| 89 | Municipalidad Distrital de Quishuar (090713) | Tayacaja | 131 012 | sí |
| 90 | Municipalidad Distrital de Santiago de Quirahuara (090614) | Huaytará | 119 055 | sí |
| 91 | Municipalidad Distrital de Laramarca (090605) | Huaytará | 66 933 | sí |
| 92 | Municipalidad Distrital de San Juan (090410) | Castrovirreyna | 64 988 | sí |

**Resumen:** 10 de 102 municipalidades publican algo; juntas representan el 50 % del gasto en personal del departamento en 2025 (S/ 39 430 220 de S/ 78 092 371). Las otras 92 gastaron S/ 38 662 151 sin publicar un solo salario.

## Lectura (escrita a mano; no la regenera el script)

- **Solo 5 municipalidades publican de forma útil** (≥ 66 puntos): Ascensión, Acobamba, Huancavelica, Tayacaja y
  San Antonio de Antaparco. Ascensión, un distrito, es la única que publicó los 34 meses.
- **Tayacaja dejó de publicar** en julio de 2025 tras publicar bien (87 % de completitud). La MP Huancavelica carga con
  unos 110 días de retraso.
- **Yauli y Caja publican, pero casi vacío:** cubren el 2 % y el 7 % de su gasto, con demoras de 7 a 10 meses, y Caja
  tiene errores en el 46 % de sus registros.
- **Angaraes (Lircay)** publicó 4 meses en 2024 con fragmentos del personal (10 % de cobertura) y nada desde entonces.
- **Las 92 que no publican gastaron S/ 38,7 millones en personal en 2025.** Acoria (S/ 3,2 M), Paucara (S/ 2,5 M) y
  la Provincial de Churcampa (S/ 2,1 M) encabezan la lista. Todas, salvo 7 sin ficha confirmada, tienen ficha en el
  PTE: el canal existe, pero no lo usan para el personal.
