# Señales de alerta: gasto en personal de las municipalidades de Huancavelica

Generado con `scripts/senales_alerta.py 09` a partir del MEF (devengado, corte 22/10/2026), RENAMU 2026
(personal declarado al INEI) y el PTE (salarios publicados). **Una señal es un indicio para revisar, no una
prueba de irregularidad**: cada una lista sus explicaciones legítimas posibles. No se nombra a personas.

| Señal | Municipalidades |
|---|---|
| Declara al INEI no tener personal, pero paga planilla | 4 |
| Paga más en locación de servicios que en toda su planilla | 18 |
| Gasto en personal 2026 crece más de 25 % | 11 |
| Pagos al alcalde irregulares en 6 o más meses | 17 |
| El personal publicado no coincide con el declarado al INEI | 1 |
| Declara al INEI el doble o más de locadores que de personal en planilla | 26 |

## Declara al INEI no tener personal, pero paga planilla (4)

- **Criterio:** RENAMU 2026 (P19 = no tiene personal) y aun así el MEF registra gasto CAS en 2025.
- **Explicaciones posibles:** Error al llenar el formulario del INEI.

| Ubigeo | Municipalidad | Provincia | Detalle |
|---|---|---|---|
| 090116 | Municipalidad Distrital de Vilca | Huancavelica | CAS 2025: S/ 30 112; personal 2.1 sin alcalde ni dietas: S/ 212 493 |
| 090202 | Municipalidad Distrital de Andabamba | Acobamba | CAS 2025: S/ 272 528; personal 2.1 sin alcalde ni dietas: S/ 370 488 |
| 090407 | Municipalidad Distrital de Huachos | Castrovirreyna | CAS 2025: S/ 100 097; personal 2.1 sin alcalde ni dietas: S/ 128 331 |
| 090615 | Municipalidad Distrital de Santo Domingo de Capillas | Huaytará | CAS 2025: S/ 90 360; personal 2.1 sin alcalde ni dietas: S/ 113 920 |

## Paga más en locación de servicios que en toda su planilla (18)

- **Criterio:** Locación a personas naturales (2.3.2.9) 2025 > personal y obligaciones sociales (2.1) 2025.
- **Explicaciones posibles:** Contrataciones temporales legítimas (consultorías, proyectos). Esas personas no figuran en el rubro Personal del PTE ni tienen derechos laborales.

| Ubigeo | Municipalidad | Provincia | Detalle |
|---|---|---|---|
| 090107 | Municipalidad Distrital de Huayllahuara | Huancavelica | locación S/ 155 249 frente a planilla S/ 153 685 (1.0×) |
| 090302 | Municipalidad Distrital de Anchonga | Angaraes | locación S/ 413 075 frente a planilla S/ 357 815 (1.2×) |
| 090306 | Municipalidad Distrital de Congalla | Angaraes | locación S/ 423 170 frente a planilla S/ 318 888 (1.3×) |
| 090409 | Municipalidad Distrital de Mollepampa | Castrovirreyna | locación S/ 262 453 frente a planilla S/ 182 826 (1.4×) |
| 090410 | Municipalidad Distrital de San Juan | Castrovirreyna | locación S/ 282 640 frente a planilla S/ 64 988 (4.3×) |
| 090502 | Municipalidad Distrital de Anco | Churcampa | locación S/ 908 580 frente a planilla S/ 446 784 (2.0×) |
| 090510 | Municipalidad Distrital de Pachamarca | Churcampa | locación S/ 304 925 frente a planilla S/ 284 629 (1.1×) |
| 090603 | Municipalidad Distrital de Córdova | Huaytará | locación S/ 343 550 frente a planilla S/ 159 318 (2.2×) |
| 090608 | Municipalidad Distrital de Querco | Huaytará | locación S/ 214 863 frente a planilla S/ 177 319 (1.2×) |
| 090609 | Municipalidad Distrital de Quito-Arma | Huaytará | locación S/ 242 004 frente a planilla S/ 167 731 (1.4×) |
| 090611 | Municipalidad Distrital de San Francisco de Sangayaico | Huaytará | locación S/ 266 500 frente a planilla S/ 164 542 (1.6×) |
| 090612 | Municipalidad Distrital de San Isidro | Huaytará | locación S/ 242 400 frente a planilla S/ 132 701 (1.8×) |
| 090613 | Municipalidad Distrital de Santiago de Chocorvos | Huaytará | locación S/ 408 850 frente a planilla S/ 247 217 (1.7×) |
| 090614 | Municipalidad Distrital de Santiago de Quirahuara | Huaytará | locación S/ 201 400 frente a planilla S/ 119 055 (1.7×) |
| 090710 | Municipalidad Distrital de Ñahuimpuquio | Tayacaja | locación S/ 283 050 frente a planilla S/ 195 128 (1.5×) |
| 090713 | Municipalidad Distrital de Quishuar | Tayacaja | locación S/ 181 703 frente a planilla S/ 131 012 (1.4×) |
| 090716 | Municipalidad Distrital de San Marcos de Rocchac | Tayacaja | locación S/ 287 500 frente a planilla S/ 271 592 (1.1×) |
| 090721 | Municipalidad Distrital de Roble | Tayacaja | locación S/ 263 589 frente a planilla S/ 256 472 (1.0×) |

## Gasto en personal 2026 crece más de 25 % (11)

- **Criterio:** Personal 2.1 ene–sep 2026 frente a ene–sep 2025. 2026 es año de elecciones municipales.
- **Explicaciones posibles:** Aumentos dispuestos por norma, nuevas plazas presupuestadas o pago de deudas laborales.

| Ubigeo | Municipalidad | Provincia | Detalle |
|---|---|---|---|
| 090107 | Municipalidad Distrital de Huayllahuara | Huancavelica | S/ 109 750 → S/ 144 347 (+32 %) |
| 090115 | Municipalidad Distrital de Pilchaca | Huancavelica | S/ 157 046 → S/ 199 980 (+27 %) |
| 090119 | Municipalidad Distrital de Huando | Huancavelica | S/ 406 470 → S/ 517 900 (+27 %) |
| 090207 | Municipalidad Distrital de Pomacocha | Acobamba | S/ 208 182 → S/ 293 782 (+41 %) |
| 090305 | Municipalidad Distrital de Chincho | Angaraes | S/ 211 832 → S/ 280 169 (+32 %) |
| 090307 | Municipalidad Distrital de Huanca-Huanca | Angaraes | S/ 144 713 → S/ 210 612 (+46 %) |
| 090407 | Municipalidad Distrital de Huachos | Castrovirreyna | S/ 149 338 → S/ 214 320 (+44 %) |
| 090411 | Municipalidad Distrital de Santa Ana | Castrovirreyna | S/ 179 461 → S/ 284 199 (+58 %) |
| 090412 | Municipalidad Distrital de Tantara | Castrovirreyna | S/ 108 918 → S/ 158 710 (+46 %) |
| 090601 | Municipalidad Provincial de Huaytará | Huaytará | S/ 951 351 → S/ 1 293 186 (+36 %) |
| 090714 | Municipalidad Distrital de Salcabamba | Tayacaja | S/ 298 201 → S/ 379 684 (+27 %) |

## Pagos al alcalde irregulares en 6 o más meses (17)

- **Criterio:** Meses de 2025–2026 en los que la compensación del alcalde se devenga en 0 o acumulada (≥ 1,9 veces la mensual): indica atrasos en la gestión de la planilla.
- **Explicaciones posibles:** Retrasos administrativos sin perjuicio económico.

| Ubigeo | Municipalidad | Provincia | Detalle |
|---|---|---|---|
| 090102 | Municipalidad Distrital de Acobambilla | Huancavelica | 11 de 21 meses en 0 o acumulados (mensual típico S/ 4 100) |
| 090202 | Municipalidad Distrital de Andabamba | Acobamba | 11 de 21 meses en 0 o acumulados (mensual típico S/ 4 100) |
| 090204 | Municipalidad Distrital de Caja | Acobamba | 6 de 21 meses en 0 o acumulados (mensual típico S/ 4 100) |
| 090303 | Municipalidad Distrital de Callanmarca | Angaraes | 7 de 21 meses en 0 o acumulados (mensual típico S/ 2 750) |
| 090312 | Municipalidad Distrital de Secclla | Angaraes | 6 de 21 meses en 0 o acumulados (mensual típico S/ 4 100) |
| 090403 | Municipalidad Distrital de Aurahua | Castrovirreyna | 7 de 21 meses en 0 o acumulados (mensual típico S/ 4 100) |
| 090410 | Municipalidad Distrital de San Juan | Castrovirreyna | 6 de 21 meses en 0 o acumulados (mensual típico S/ 2 600) |
| 090411 | Municipalidad Distrital de Santa Ana | Castrovirreyna | 15 de 21 meses en 0 o acumulados (mensual típico S/ 3 605) |
| 090504 | Municipalidad Distrital de El Carmen | Churcampa | 6 de 21 meses en 0 o acumulados (mensual típico S/ 4 352) |
| 090509 | Municipalidad Distrital de San Pedro de Coris | Churcampa | 6 de 21 meses en 0 o acumulados (mensual típico S/ 4 100) |
| 090603 | Municipalidad Distrital de Córdova | Huaytará | 6 de 21 meses en 0 o acumulados (mensual típico S/ 3 502) |
| 090605 | Municipalidad Distrital de Laramarca | Huaytará | 10 de 21 meses en 0 o acumulados (mensual típico S/ 2 852) |
| 090606 | Municipalidad Distrital de Ocoyo | Huaytará | 6 de 21 meses en 0 o acumulados (mensual típico S/ 3 552) |
| 090614 | Municipalidad Distrital de Santiago de Quirahuara | Huaytará | 6 de 21 meses en 0 o acumulados (mensual típico S/ 2 652) |
| 090713 | Municipalidad Distrital de Quishuar | Tayacaja | 6 de 21 meses en 0 o acumulados (mensual típico S/ 2 600) |
| 090714 | Municipalidad Distrital de Salcabamba | Tayacaja | 8 de 21 meses en 0 o acumulados (mensual típico S/ 4 700) |
| 090717 | Municipalidad Distrital de Surcubamba | Tayacaja | 7 de 21 meses en 0 o acumulados (mensual típico S/ 4 752) |

## El personal publicado no coincide con el declarado al INEI (1)

- **Criterio:** Solo para quienes publican: registros en el PTE de 2025-12 frente al total declarado a RENAMU al 31/12/2025, con una diferencia mayor al 30 %.
- **Explicaciones posibles:** RENAMU incluye personal pagado con proyectos de inversión; el PTE puede omitir regímenes.

| Ubigeo | Municipalidad | Provincia | Detalle |
|---|---|---|---|
| 090118 | Municipalidad Distrital de Ascensión | Huancavelica | PTE 2025-12: 56 registros; RENAMU 31/12/2025: 95 personas |

## Declara al INEI el doble o más de locadores que de personal en planilla (26)

- **Criterio:** RENAMU: personal de locación / orden de servicios al 31/12/2025 ≥ 2 × total de personal en planilla.
- **Explicaciones posibles:** Municipalidades que operan principalmente con locadores, o error de llenado.

| Ubigeo | Municipalidad | Provincia | Detalle |
|---|---|---|---|
| 090106 | Municipalidad Distrital de Huachocolpa | Huancavelica | locación 31 frente a 7 en planilla |
| 090107 | Municipalidad Distrital de Huayllahuara | Huancavelica | locación 21 frente a 3 en planilla |
| 090203 | Municipalidad Distrital de Anta | Acobamba | locación 22 frente a 8 en planilla |
| 090302 | Municipalidad Distrital de Anchonga | Angaraes | locación 29 frente a 11 en planilla |
| 090406 | Municipalidad Distrital de Cocas | Castrovirreyna | locación 8 frente a 4 en planilla |
| 090409 | Municipalidad Distrital de Mollepampa | Castrovirreyna | locación 13 frente a 6 en planilla |
| 090502 | Municipalidad Distrital de Anco | Churcampa | locación 27 frente a 13 en planilla |
| 090503 | Municipalidad Distrital de Chinchihuasi | Churcampa | locación 23 frente a 9 en planilla |
| 090504 | Municipalidad Distrital de El Carmen | Churcampa | locación 25 frente a 7 en planilla |
| 090507 | Municipalidad Distrital de Paucarbamba | Churcampa | locación 34 frente a 14 en planilla |
| 090510 | Municipalidad Distrital de Pachamarca | Churcampa | locación 21 frente a 6 en planilla |
| 090511 | Municipalidad Distrital de Cosme | Churcampa | locación 18 frente a 9 en planilla |
| 090602 | Municipalidad Distrital de Ayavi | Huaytará | locación 7 frente a 2 en planilla |
| 090603 | Municipalidad Distrital de Córdova | Huaytará | locación 13 frente a 5 en planilla |
| 090604 | Municipalidad Distrital de Huayacundo Arma | Huaytará | locación 8 frente a 4 en planilla |
| 090606 | Municipalidad Distrital de Ocoyo | Huaytará | locación 12 frente a 2 en planilla |
| 090608 | Municipalidad Distrital de Querco | Huaytará | locación 12 frente a 3 en planilla |
| 090609 | Municipalidad Distrital de Quito-Arma | Huaytará | locación 10 frente a 2 en planilla |
| 090610 | Municipalidad Distrital de San Antonio de Cusicancha | Huaytará | locación 9 frente a 4 en planilla |
| 090611 | Municipalidad Distrital de San Francisco de Sangayaico | Huaytará | locación 9 frente a 2 en planilla |
| 090612 | Municipalidad Distrital de San Isidro | Huaytará | locación 11 frente a 4 en planilla |
| 090613 | Municipalidad Distrital de Santiago de Chocorvos | Huaytará | locación 15 frente a 4 en planilla |
| 090614 | Municipalidad Distrital de Santiago de Quirahuara | Huaytará | locación 13 frente a 1 en planilla |
| 090616 | Municipalidad Distrital de Tambo | Huaytará | locación 10 frente a 5 en planilla |
| 090711 | Municipalidad Distrital de Pazos | Tayacaja | locación 29 frente a 14 en planilla |
| 090713 | Municipalidad Distrital de Quishuar | Tayacaja | locación 9 frente a 2 en planilla |

## Municipalidades con dos o más señales (20)

| Ubigeo | Municipalidad | Señales |
|---|---|---|
| 090107 | Municipalidad Distrital de Huayllahuara | 3: Declara al INEI el doble o más de locadores que de personal en planilla; Paga más en locación de servicios que en toda su planilla; Gasto en personal 2026 crece más de 25 % |
| 090603 | Municipalidad Distrital de Córdova | 3: Pagos al alcalde irregulares en 6 o más meses; Declara al INEI el doble o más de locadores que de personal en planilla; Paga más en locación de servicios que en toda su planilla |
| 090614 | Municipalidad Distrital de Santiago de Quirahuara | 3: Pagos al alcalde irregulares en 6 o más meses; Declara al INEI el doble o más de locadores que de personal en planilla; Paga más en locación de servicios que en toda su planilla |
| 090713 | Municipalidad Distrital de Quishuar | 3: Pagos al alcalde irregulares en 6 o más meses; Declara al INEI el doble o más de locadores que de personal en planilla; Paga más en locación de servicios que en toda su planilla |
| 090202 | Municipalidad Distrital de Andabamba | 2: Pagos al alcalde irregulares en 6 o más meses; Declara al INEI no tener personal, pero paga planilla |
| 090302 | Municipalidad Distrital de Anchonga | 2: Declara al INEI el doble o más de locadores que de personal en planilla; Paga más en locación de servicios que en toda su planilla |
| 090407 | Municipalidad Distrital de Huachos | 2: Gasto en personal 2026 crece más de 25 %; Declara al INEI no tener personal, pero paga planilla |
| 090409 | Municipalidad Distrital de Mollepampa | 2: Declara al INEI el doble o más de locadores que de personal en planilla; Paga más en locación de servicios que en toda su planilla |
| 090410 | Municipalidad Distrital de San Juan | 2: Pagos al alcalde irregulares en 6 o más meses; Paga más en locación de servicios que en toda su planilla |
| 090411 | Municipalidad Distrital de Santa Ana | 2: Pagos al alcalde irregulares en 6 o más meses; Gasto en personal 2026 crece más de 25 % |
| 090502 | Municipalidad Distrital de Anco | 2: Declara al INEI el doble o más de locadores que de personal en planilla; Paga más en locación de servicios que en toda su planilla |
| 090504 | Municipalidad Distrital de El Carmen | 2: Pagos al alcalde irregulares en 6 o más meses; Declara al INEI el doble o más de locadores que de personal en planilla |
| 090510 | Municipalidad Distrital de Pachamarca | 2: Declara al INEI el doble o más de locadores que de personal en planilla; Paga más en locación de servicios que en toda su planilla |
| 090606 | Municipalidad Distrital de Ocoyo | 2: Pagos al alcalde irregulares en 6 o más meses; Declara al INEI el doble o más de locadores que de personal en planilla |
| 090608 | Municipalidad Distrital de Querco | 2: Declara al INEI el doble o más de locadores que de personal en planilla; Paga más en locación de servicios que en toda su planilla |
| 090609 | Municipalidad Distrital de Quito-Arma | 2: Declara al INEI el doble o más de locadores que de personal en planilla; Paga más en locación de servicios que en toda su planilla |
| 090611 | Municipalidad Distrital de San Francisco de Sangayaico | 2: Declara al INEI el doble o más de locadores que de personal en planilla; Paga más en locación de servicios que en toda su planilla |
| 090612 | Municipalidad Distrital de San Isidro | 2: Declara al INEI el doble o más de locadores que de personal en planilla; Paga más en locación de servicios que en toda su planilla |
| 090613 | Municipalidad Distrital de Santiago de Chocorvos | 2: Declara al INEI el doble o más de locadores que de personal en planilla; Paga más en locación de servicios que en toda su planilla |
| 090714 | Municipalidad Distrital de Salcabamba | 2: Pagos al alcalde irregulares en 6 o más meses; Gasto en personal 2026 crece más de 25 % |

## Lectura (escrita a mano; no la regenera el script)

- **El patrón más extendido es el personal fuera de planilla:** 18 distritos pagan más en locación de servicios que en
  toda su planilla, y 26 declaran al INEI el doble o más de locadores que de trabajadores. Esas personas no aparecen
  en el rubro Personal del PTE, así que aunque estas municipalidades publicaran, la mayor parte de quienes trabajan
  para ellas seguiría sin verse. Casos extremos: San Juan (Castrovirreyna) gasta 4,3 veces su planilla en locación;
  Córdova, 2,2 veces; Anco, 2,0 veces (S/ 909 mil).
- **Andabamba declara al INEI no tener personal**, pero el MEF le registra S/ 272 mil en CAS en 2025, y paga al
  alcalde con atrasos en 11 de 21 meses.
- **Santa Ana (Castrovirreyna)** paga al alcalde de forma irregular en 15 de 21 meses (hasta S/ 20 335 de golpe en
  marzo de 2026) y su gasto en personal sube 58 % en el año electoral.
- **11 municipalidades suben su gasto en personal más de 25 % en 2026**, año de elecciones municipales; la más grande
  es la Provincial de Huaytará (+36 %, S/ 342 mil más en nueve meses).
- **Ascensión, la mejor del ranking,** publica 56 registros en diciembre de 2025 pero declaró 95 personas al INEI: ni
  la mejor publica a todo su personal (o su declaración al INEI incluye personal de obras).
- **No marcado por el script, pero llamativo:** la Provincial de Tayacaja declara al INEI 212 locadores y 212
  trabajadores en planilla, el mismo número; probable error de llenado.
