# Coloured OBD adapter cables (A1-A6, 3-pin, SGW) - research

> **Shared research.** This document is shared with CUORE, the car-side diagnostic tool
> ([github.com/dangelojohn/CUORE](https://github.com/dangelojohn/CUORE), wiki page
> [Adapter-Cables](https://github.com/dangelojohn/CUORE/wiki/Adapter-Cables)). The same
> findings are kept in both places so that the shop-side platform and the car-side tool agree
> on which cable does what. AlfaCore also carries a wiki page, `Adapter-Cables`.
>
> **Research documentation only.** No AlfaCore module code depends on this file. It is a web
> research record dated 2026-10-22. Nothing was connected to a car, adapter, COM port or server.

## Why this matters for AlfaCore service writers and technicians

AlfaCore ingests scans (`alfa_core_scanner`) and triages DTCs (`alfa_core_diagnosis`). Whether a
scan can reach a given module at all depends on the cable between the scan tool and the car's
16-pin diagnostic socket. Many Alfa Romeo, Maserati, Ferrari, Fiat and Jeep systems sit on CAN or
K-line pins that a plain OBD-II lead does not bring to the tool. The coloured cables (A1 to A6),
the 3-pin lead and the Security Gateway (SGW) bypass are passive break-out leads that re-route
those pins. For a service writer this answers "can the tool reach the airbag, ABS, steering or
infotainment modules on this car?"; for a technician it answers "which lead do I fit, and which
one must I never fit."

Use the platform matrix in section 3 to pick the cable for a car, and the per-row confidence
labels to decide how far to trust each claim.

### Safety cautions (read before fitting any lead)

These are restated from the research below; each carries the confidence level given there.

- **Green (A1) ties car pins 1, 7, 9 and 12 together.** On low-speed-CAN cars this shorts the two
  CAN data lines. The MES vehicle list warns against interfaces with a short between pins 1 and 9
  on Grande Punto, Punto Evo, Fiat 500, Doblo (152 and 263), Alfa Mito, Giulietta and Ypsilon 2011
  (relayed via search summary). Giulia and Stelvio are not named in that warning; the rule
  "never fit a pin 1/9 short on Giulia or Stelvio" is consistent with the mechanism, but no public
  source names those cars.
- **2018+ cars sit behind a Security Gateway (SGW).** It blocks actuator tests and DTC clearing.
  MES states "It is not possible to unlock the SGW module with Multiecuscan". The 12+8 bypass
  lead is a physical workaround, not a coloured cable. Disconnect it before dealer visits.
- **A bypass must carry the second high-speed CAN on pins 12/13** for grey (A6) to work
  (AlfaOBD). The vendor listing does not say whether the 12+8 lead carries them.
- **Check labels and continuity.** Vendors mislabel colours (Gendan's 6-pack page labels grey as
  "Adapter 5"; other listings name blue "Control unit"). One grey cable's labels were questioned
  on a forum: test continuity before relying on a lead.
- **Some interfaces make the colours unnecessary** (OBDLink MX+/EX, vLinker MS/FD/FD+/MC/MC+/FS
  for the middle-speed CAN, per AlfaOBD). Do not fit a cable the interface already covers.
- **Bitrates are largely unsourced.** Only the blue lead has a stated bitrate (125 kbps, one
  vendor listing). The 500 kbps figure for grey is the project's own and is not confirmed by any
  public source read.
- **Ferrari and Maserati:** no MES or AlfaOBD support was found for Ferrari; Maserati is listed by
  AlfaOBD with OBDLink MX+/EX only and no coloured cable.

## Research

**Scope:** MultiEcuScan (MES) / FiatECUScan / AlfaOBD coloured break-out leads. Nothing was connected to a car, adapter, COM port or server.

Confidence key: **official** = multiecuscan.net or alfaobd.com itself; **forum** = owner/user posts; **listing** = vendor product page only.
Method caveats: official MES adapter pages (multiecuscan.net/Adapters.aspx, forum threads) returned 404; mhhauto, giuliaforums, alfaowner, stelvioforum, clubalfa returned 403/402/redirect to a paywall, so those are quoted from search-engine summaries only ("via search"). No page I could open gives a bitrate for A6 or any CAN bus on any cable except Gendan's "125kbps" for the blue lead.

## 1. Summary table

| ID | Colour | Code | Car-side pins -> tool pins | Bus | Bitrate | Main use | Confidence |
|---|---|---|---|---|---|---|---|
| A1 | green | Adapter 1 | tool 7 -> car 1,7,9,12 | K-line | n/s | ABS, power steering, older K-line cars | official (models) + listing (pins) |
| A2 | red | Adapter 2 | tool 7 -> car 3 | K-line | n/s | Airbag | official (models) + listing |
| A3 | yellow | Adapter 3 | tool 6->car 1, tool 14->car 9, tool 7->car 12 | Low-speed CAN (+K pin 12) | n/s | 500, Punto, Panda, Giulietta, Mito, ProMaster pre-2022 | official + listing |
| A4 | purple | Adapter 4 | tool 7 -> car 7,8,11,13 | K-line (pin 13) | n/s | Electric hood / TPMS | listing-only (+MES tag A4P13) |
| A5 | blue | Adapter 5 | tool 6->car 3, tool 14->car 11 | MS-CAN / BHCAN (project: CAN-IHS) | 125 kbps (listing) | Giulia/Stelvio infotainment and body, Chrysler/Dodge/Fiat later models | official (tags, "middle-speed CAN") + listing + forum |
| A6 | grey | Adapter 6 | tool 6->car 12, tool 14->car 13 | 2nd high-speed CAN (project: CAN-CH) | 500 kbps per project; not in any source | Giulia/Stelvio ABS, airbag, EPS; 500X, Renegade/Compass MP, Toro, ProMaster 2022+ | official + listing |
| 3PIN | not stated | 16/3, LEAD3PIN | 3-pin round to OBD-II | K-line | n/s | Pre-2001 Fiat/Alfa/Lancia (and Ferrari 3-pin cars via forum) | official (models) + listing + forum |
| SGW | n/a | 12+8 bypass | replaces SGW connectors | all CAN behind gateway | n/s | 2018+ Giulia/Stelvio/500X/Renegade, etc. | official notes + listing |
| FUCHS | n/s | 16pin multi / MS-HS CANBUS | n/s | n/s | n/s | name only | listing-only |
| white | white | - | - | - | - | not found | not found |
| black | black | - | - | - | - | not found (MES). Black only as casing colour on generic leads | not found |
| other | orange, Adapter 7+, etc. | - | - | - | - | not found | not found |

n/s = not stated by any source read.
"tool X -> car Y" follows Gendan's phrasing: "diagnostic tool end pin X connects to car end pin Y" (the female end carrying your ELM/OBDLink, the male end into the car).

## 2. Detail sections

### A5 - blue (the in-project CAN-IHS cable)
- Vendor/product: MultiECUScan kit item "Adapter 5". Gendan FESBLUE "MultiECUScan MS-CAN Adaptor Cable (Adapter 5)" GBP 12.50; Alfissimo "Adapters (Blue & Grey)" ref 1000-56-GREY USD 36; Electronic-Fuchs "Blauer Adapter (Adapter 5) fuer Multiecuscan/AlfaOBD" EUR 15.90; Obdauto.fr "ADAPTATEUR BLEU (A5)" EUR 8.99; AsTools 6-piece set SKU A0155 EUR 24.95.
- Connector: 16-pin OBD-II female (tool) to 16-pin OBD-II male (car), passive break-out.
- Pin map: Gendan "pin 6 connects to car end pin 3; pin 14 connects to car end pin 11". MHH Auto, quoting MES helpdesk (via search): "re-directs the CAN from pins 6/14 to pins 3/11". **Confirms project fact (car pins 3/11 brought out on tool pins 6/14).**
- Bus/bitrate: Gendan: "additional systems coverage on vehicles using the 125kbps MS-CAN / BHCAN protocols". AlfaOBD homepage: pins 3 and 11 = "middle-speed CAN". **Confirms 125 kbps** (single listing source). The term "CAN-IHS" appears in none of the sources read; it is the project's name for the same bus (my own knowledge: Chrysler IHS is 125 kbps - not source-confirmed).
- Reaches (Giulia/Stelvio, per Alfissimo module table): amplifier (Ask/Beats), ESEM, Marelli AlfaConnect radio/nav, multimedia control module, comfort seat and wheel (Bitron), TRW climate control, blind-spot sensors left/right (Autoliv). Stelvio 2.0 and 2.9 listed.
- MES supported-vehicles tag list (ELMA5/A5): Giulia, Stelvio, Tonale, Fiat 500X, 500e 2020+, Egea/Tipo, Ducato X290 MCA, Freemont, Chrysler Thema, Dodge Journey, Dodge Neon 2016.
- Cautions: AlfaOBD says blue is needed only with OBDLink LX / CX (Android); not needed with OBDLink MX+/EX, ELS27, or Vgate vLinker MS/FD/FD+/MC/MC+/FS (these multiplex 3/11 themselves). Conflicts: Mercadolibre/Newegg listing text calls blue "Control unit" and grey "Basic control unit" (no pins); Gendan's 6-pack page mislabels grey as "Adapter 5". 2018+ cars need SGW bypass for writes/clears.
- Confidence: official (tags; AlfaOBD "middle-speed") + listing (pins, 125k) + forum.
- Sources: gendan.co.uk/product_FESBLUE.html; gendan.co.uk/product_FESCBL.html; alfaobd.com; multiecuscan.net/SupportedVehiclesList.aspx; shop.alfissimo.com (3019); mhhauto.com/Thread-MultiECUScan-adapters (via search); squadra-tuning.com/obd-tools/multiecuscan/.

### A6 - grey (the in-project CAN-CH cable)
- Vendor/product: Gendan FESGREY "HiSpeed CAN Adaptor Cable (Adapter 6)" GBP 12.50; Alfissimo (same ref as A5); Electronic-Fuchs "Grauer Adapter (Adapter 6)"; Obdauto.fr "(A6)" - recommended there "for Jeep vehicles, especially the Renegade models".
- Pin map: Gendan "pin 6 connects to car end pin 12; pin 14 connects to car end pin 13". Giulia Forums post (via search) states the same list but one member questioned whether a particular grey cable's labels were right (6->12 vs 3->12) - test continuity. **Confirms project fact (car pins 12/13 brought out on tool 6/14).**
- Bus: AlfaOBD: pins 12 and 13 = "second high-speed CAN"; a Stellantis bulletin quoted via search labels pin 12 high, pin 13 low, CAN-C2. Gendan: "secondary high-speed CAN protocols used on vehicles such as the Fiat 500X".
- Bitrate: **not stated in any source read** (Gendan: "not stated"). Project's 500 kbps is unconfirmed by public sources.
- Reaches (Giulia/Stelvio, Alfissimo): Continental ABS MK C1, HALF camera (Bosch), torque-vectoring module, Bosch airbag, steering lock (TRW), ZF electric steering, adaptive headlights, parking control (Bosch).
- Vehicles: AlfaOBD supported_cars "grey adapter": Giulia 2015+, Stelvio 2016+, Fiat 500E New 2020+, 500X 2015+, Argo/Chronos 2017+, Ducato Serie 8 2022+, Toro 2016+, Jeep Compass (MP) 2017+, Jeep Renegade 2014+, Ram ProMaster (VF) 2022+. MES tags also put A6 on Tonale and Ducato X290 MCA.
- Cautions: SGW on 2018+ blocks actuators/DTC clear; "It is not possible to unlock the SGW module with Multiecuscan" (MES list). Bypass must carry the second HS CAN on pins 12/13 (AlfaOBD). Giulia Forums user needed bypass jumpers A1-A2 and A8-A9 plus grey #6 plus an OBDLink SX (via search). A user with Vgate + bypass failed on a 2024 Giulia in MES. Old interfaces (CANtieCAR v3) cannot reach this bus.
- Confidence: official (AlfaOBD) + listing + forum.
- Sources: alfaobd.com; alfaobd.com/supported_cars.html; gendan.co.uk/product_FESGREY.html; shop.alfissimo.com (3019); obdauto.fr; giuliaforums.com/threads/multiecuscan-anyone.45717/ (via search).

### A1 - green
- Pins: tool 7 -> car 1, 7, 9, 12 (Gendan FESCBL; several listings). Bus: K-line on whichever of those pins the module uses. MES tags KLELMA1P1/P9/P12 (inferred: K-line, adapter 1, pin N).
- Vehicles (AlfaOBD "green adapter"): Alfa 147, 159, Brera/Spider, GT; Fiat Bravo T198, Croma T194, Ducato T250 2006-2014, Grand Siena, Idea, Linea, Strada, Uno 195; Lancia Delta T181, Musa, Phedra, Ypsilon T843; Abarth Bravo/Stilo; Croma T154 with 3-pin.
- Cautions: ties pins 1 and 9 together. Fiat Forum / MES forum (via search): "If you plug that cable into a slow-CAN car, it will short the 2 CAN data lines together." MES list banner (via search): "DO NOT USE MODIFIED INTERFACES WITH SHORT CIRCUIT BETWEEN PINS 1 AND 9 ON GRANDE PUNTO, PUNTO EVO, FIAT 500, DOBLO(152), DOBLO(263), ALFA MITO, GIULIETTA, YPSILON 2011". Giulia/Stelvio are not named in that banner; the project rule "never short 1 and 9 on Giulia/Stelvio" is consistent with the mechanism but I found no public source naming Giulia.
- One MES-forum reply (via search) says shorting 1-7-9-12 was once advised for some old cars, "better to buy or make Adapter 1".
- Confidence: official (models) + listing (pins) + forum.

### A2 - red
- Pins: tool 7 -> car 3 only. Airbag K-line (tag A2P3). AlfaOBD lists "red&green adapters" (no red-only row): Panda T169, Sedici, Stilo; with 3-pin: Barchetta, Bravo/Brava, Coupe, Doblo 119, Ducato 230/244, Marea. Confidence: official + listing.

### A3 - yellow
- Pins: tool 6 -> car 1; tool 14 -> car 9; tool 7 -> car 12 (Gendan FESYELLOW; pin 12 for Croma power steering and Xenon). Bus: low-speed CAN. Bitrate not stated.
- Vehicles (AlfaOBD "yellow adapter"): Abarth 500, Grande Punto, Punto Evo; Alfa 4C, Giulietta 2010-2020, Mito; Fiat 500 2007+, 500E 2013-2019, 500L, Doblo 152/263, Ducato X290 2014-2021, Fiorino/Qubo, Grande Punto, Panda T319, Punto 188, Punto Evo; Lancia Ypsilon T846; Ram ProMaster VF 2014-2021 and ProMaster City; Chrysler Ypsilon.
- Cautions: MES "requires only the yellow adapter or direct connection" on Grande Punto (Fiat Forum). A wrong-colour adapter may have fed 12 V to a 5 V-only ELM pin (Fiat Forum speculation). An Italian user saw resistance between pins 1 and 9 with yellow fitted (forum, via search).
- Confidence: official + listing.

### A4 - purple
- Pins: tool 7 -> car 7, 8, 11, 13. Gendan title "Elec Hood / TPMS". Only listing evidence plus MES tags (A4P13 on Croma, Chrysler Delta). Not in the AlfaOBD cars table. Confidence: listing-only.

### 3-pin lead
- Gendan LEAD3PIN; Fuchs "16/3 fuer Fiat OBD 1". Vendors publish no pin map. Team-BHP Palio: 3-pin pin 1 unused, pin 2 signal ground, pin 3 K-line; cheap lead had 1/3 swapped. FerrariChat (550): K-line to OBD 7, L-line to 15, signal ground 5, power 16; Ferrari data access is restricted by Ferrari. Confidence: official (models) + listing + forum.

### SGW bypass (not a coloured cable, but required with A5/A6 on 2018+)
- Gendan SGWBYPASS: 12+8-pin lead replacing the SGW connectors, Giulia/Stelvio 2017+, Ram 2018+, 500L/500X/Doblo 2017+, Grand Cherokee 2018+, Renegade 2017+; does not say pins 12/13 are carried. AlfaOBD recommends zAutomotive and states no bypass exists for Grand Cherokee WL, Ram 2025/26, Alfa Tonale. Disconnect before dealer visits. Confidence: official + listing.

### Interfaces that make cables unnecessary (for context, neutral)
- AlfaOBD: OBDLink MX+/EX handle middle-speed CAN; vLinker MS/FD/FD+/MC/MC+/FS need no colour adapters; OBDKey multipin. MES: MULTIPLEXED and vLinker MS packages "do not need additional adapters (except the 3-pin adapter)". Grey is still listed for the second HS bus with OBDLink MX+/EX in AlfaOBD's Giulia/Stelvio rows.

### Colours with no confirmed cable
white: not found. black: not found as an MES/AlfaOBD adapter (only casing colour on generic leads and a vhbw OBD1-OBD2 adapter). orange / Adapter 7+: not found. Electronic-Fuchs "16pin ABS/AIRBAG/GETRIEBE/SERVO/CAN" and "16pin MS/HS CANBUS": exist as listings with no details.

## 3. Brand / platform matrix

| Platform | Needed for | Source basis |
|---|---|---|
| Giorgio Alfa (Giulia 2015+, Stelvio 2016+, Tonale) | Standard CAN 6/14: no cable. Blue A5 (3/11): infotainment/body. Grey A6 (12/13): ABS, airbag, EPS, etc. 2018+: SGW bypass that also carries 12/13 | official + listing |
| Older Alfa | K-line cars (147, 156, 159, GT, Brera): green (+red). 156/166/GTV/Spider 916/145/146/155/164: full coloured set (+ 3-pin on early). Mito, Giulietta, 4C: yellow | official (AlfaOBD) |
| Maserati Ghibli (M157), Quattroporte (M156), Levante (M161) 2013+ | AlfaOBD lists OBDLink MX+/EX only, no coloured cable. MES: not a supported make. 12+8 SGW bypass listing names Ghibli/Levante (single vendor). Grecale, MC20: no source found | official (AlfaOBD) / not found |
| Ferrari | No MES/AlfaOBD support found. Older 3-pin cars (550, 355) use K-line on 3-pin; owner-derived pins only | forum |
| Fiat / Abarth | Old K-line: green, red&green, 3-pin. Low-speed CAN (500, Punto, Panda, Doblo, Ducato X290, Abarth): yellow. 500X, 500e 2020+, Toro, Argo/Chronos, Ducato Serie 8: grey (and MES blue on 500X/500e/Egea) | official |
| Jeep / Ram / Chrysler / Dodge | Renegade 2014+, Compass MP 2017+, ProMaster 2022+: grey. ProMaster pre-2022 / City: yellow. Chrysler Ypsilon: yellow. Other Jeep/Ram/Chrysler (AlfaOBD): OBDLink LX/MX+/EX/CX only. MES tags: blue A5 on Thema, Freemont, Journey, Neon 2016. Obdauto says A6 "especially Renegade" | official |

## Appendix A. Per-row confidence and sources (from adapter_cables.json)

Machine-readable copy: [`adapter_cables.json`](adapter_cables.json). Reproduced from the data file; "via search summary" means the page itself could not be opened.

### A1 - green

- **Confidence:** official (AlfaOBD supported_cars table) + listing (pin map) + forum (short-circuit explanation)
- **Sources:**
  - https://www.alfaobd.com/supported_cars.html
  - https://www.gendan.co.uk/product_FESCBL.html
  - https://www.gendan.co.uk/category_161.html
  - https://www.astools.eu/products/multiecuscan-adapter-cable-set-6-piece
  - https://electronic-fuchs.de/c/produkte/alfaobd/adapter
  - https://multiecuscan.net/forum/viewtopic.php?p=7755 (via search summary)

### A2 - red

- **Confidence:** official (AlfaOBD) + listing (pin map)
- **Sources:**
  - https://www.alfaobd.com/supported_cars.html
  - https://www.gendan.co.uk/product_FESCBL.html
  - https://www.gendan.co.uk/category_161.html
  - https://www.obdauto.fr/adaptateurs-special-multiecuscan-c102x3404907

### A3 - yellow

- **Confidence:** official (AlfaOBD, MES tag list) + listing (pin map)
- **Sources:**
  - https://www.alfaobd.com/supported_cars.html
  - https://www.alfaobd.com
  - https://www.gendan.co.uk/product_FESYELLOW.html
  - https://www.multiecuscan.net/SupportedVehiclesList.aspx
  - https://www.fiatforum.com/threads/multiscan-adapter.479619/post-4525770
  - https://forum.clubalfa.it/threads/problema-di-connessione-al-body-computer-con-multiecuscan-e-alfa-obd.129797/latest

### A4 - purple (violet)

- **Confidence:** listing-only (pin map, usage) + MES tag list (model association, inference)
- **Sources:**
  - https://www.gendan.co.uk/category_161.html
  - https://www.gendan.co.uk/product_FESCBL.html
  - https://www.multiecuscan.net/SupportedVehiclesList.aspx
  - https://electronic-fuchs.de/c/produkte/alfaobd/adapter

### A5 - blue

- **Confidence:** official (MES tag list; AlfaOBD homepage on blue/middle-speed and 3/11) + listing (pin map, 125k) + forum (MHH Auto helpdesk quote via search summary)
- **Sources:**
  - https://www.alfaobd.com
  - https://www.multiecuscan.net/SupportedVehiclesList.aspx
  - https://www.gendan.co.uk/product_FESBLUE.html
  - https://www.gendan.co.uk/product_FESCBL.html
  - https://shop.alfissimo.com/diagnostic-softwarehardware-multiecuscanalfaobd/3019-diagnostic-adapters-multiecuscanalfa-obd.html
  - https://mhhauto.com/Thread-MultiECUScan-adapters (via search summary; page returned 403)
  - https://squadra-tuning.com/obd-tools/multiecuscan/

### A6 - grey (gray)

- **Confidence:** official (AlfaOBD homepage and supported_cars table) + listing (pin map, module list) + forum
- **Sources:**
  - https://www.alfaobd.com
  - https://www.alfaobd.com/supported_cars.html
  - https://www.multiecuscan.net/SupportedVehiclesList.aspx
  - https://www.gendan.co.uk/product_FESGREY.html
  - https://shop.alfissimo.com/diagnostic-softwarehardware-multiecuscanalfaobd/3019-diagnostic-adapters-multiecuscanalfa-obd.html
  - https://www.obdauto.fr/adaptateurs-special-multiecuscan-c102x3404907
  - https://squadra-tuning.com/obd-tools/multiecuscan/
  - https://www.giuliaforums.com/threads/multiecuscan-anyone.45717/ (via search summary)

### 3PIN - not stated (black lead in listings; colour not confirmed)

- **Confidence:** official (AlfaOBD model list) + listing + forum for pins
- **Sources:**
  - https://www.gendan.co.uk/product_LEAD3PIN.html
  - https://www.alfaobd.com/supported_cars.html
  - https://electronic-fuchs.de/c/produkte/alfaobd/adapter
  - https://www.team-bhp.com/forum/technical-stuff/79893-reliable-fiat-ecu-scanner-post2465850.html
  - https://www.ferrarichat.com/forum/threads/obd2-and-a-97-550.147539

### SGW-12+8 - not applicable (module bypass harness)

- **Confidence:** official (AlfaOBD, MES SGW notes) + listing
- **Sources:**
  - https://www.gendan.co.uk/product_SGWBYPASS.html
  - https://www.alfaobd.com
  - https://www.multiecuscan.net/SupportedVehiclesList.aspx
  - https://autonavaimet.fi/en/tuotteet/FCA12%2B8

### FUCHS-MULTI - not stated

- **Confidence:** listing-only
- **Sources:**
  - https://electronic-fuchs.de/c/produkte/alfaobd/adapter

### VHBW-OBD1 - black (and red/green/yellow/purple in a set listing)

- **Confidence:** listing-only
- **Sources:**
  - https://www.manomano.co.uk/p/vhbw-obd2-adapter-a2-16-pin-obd1-to-obd2-for-car-eg-compatible-with-alfa-romeo-fiat-lancia-auto-45524432
  - https://elektrohungary.com/en/spd/888300218/VHBW-OBD2-Adapter-Kit-16Pin-OBD1-to-OBD2-19-cm

### WHITE - white

- **Confidence:** not found
- **Sources:** none (not found)

### BLACK - black

- **Confidence:** not found
- **Sources:**
  - https://www.renhotecrf.com/?p=29038

### ORANGE-OTHER - orange / any colour beyond green, red, yellow, purple, blue, grey

- **Confidence:** not found
- **Sources:** none (not found)

## 4. Sources (as listed in the research note)
- https://www.alfaobd.com (adapter colours, pin notes, SGW notes)
- https://www.alfaobd.com/supported_cars.html (per-model recommended setup)
- https://www.alfaobd.com/supported_units.html
- https://www.multiecuscan.net (site; no adapter page, points to vehicle support lists)
- https://www.multiecuscan.net/SupportedVehiclesList.aspx (ELMA tags, SGW text)
- https://www.multiecuscan.net/VehicleSupportCheck.aspx
- https://www.gendan.co.uk/product_FESBLUE.html, product_FESGREY.html, product_FESYELLOW.html, product_FESCBL.html, product_LEAD3PIN.html, product_SGWBYPASS.html, category_161.html
- https://shop.alfissimo.com/diagnostic-softwarehardware-multiecuscanalfaobd/3019-diagnostic-adapters-multiecuscanalfa-obd.html
- https://www.astools.eu/products/multiecuscan-adapter-cable-set-6-piece
- https://electronic-fuchs.de/c/produkte/alfaobd/adapter
- https://www.obdauto.fr/adaptateurs-special-multiecuscan-c102x3404907
- https://squadra-tuning.com/obd-tools/multiecuscan/
- https://www.fiatforum.com/threads/multiscan-adapter.479619/post-4525770
- https://www.fiatforum.com/threads/multiscan-ecu.458278 (via search)
- https://mhhauto.com/Thread-MultiECUScan-adapters (via search; 403)
- https://www.giuliaforums.com/threads/multiecuscan-anyone.45717/ (via search; paywalled)
- https://forum.clubalfa.it/threads/problema-di-connessione-al-body-computer-con-multiecuscan-e-alfa-obd.129797/latest (via search)
- https://multiecuscan.net/forum/viewtopic.php?p=7755 and p=7690 (via search)
- https://www.team-bhp.com/forum/technical-stuff/79893-reliable-fiat-ecu-scanner-post2465850.html
- https://www.ferrarichat.com/forum/threads/obd2-and-a-97-550.147539
- https://www.mercadolibre.com.mx/4pcs-obd2-for-alfa-fiat-ecu-scan-car-diagnostic-cables-multi/p/MLM2006016525 (via search; 403)
- https://autonavaimet.fi/en/tuotteet/FCA12%2B8
- https://www.renhotecrf.com/?p=29038, manomano vhbw A2 listing
