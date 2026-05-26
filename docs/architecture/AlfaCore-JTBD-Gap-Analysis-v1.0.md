# AlfaCore — Customer / Mechanic JTBD Gap Analysis v1.0

**Scope:** End-to-end Jobs-To-Be-Done analysis for the AlfaCore service across two audiences — luxury Italian-platform vehicle owners (Alfa Romeo / Fiat / Maserati) and the dealership/independent-specialist service operation that supports them. Maps every JTBD against the named Odoo Enterprise module set, distinguishing native capability from configuration, third-party integration, and bespoke development.

**Companion to:** `Alfa-Odoo-Server-Plan-v1.0.md` (v1.0 sandbox plan) and `AlfaCore-Service-Plan-v1.0.md` (customer-facing service plan). This document is the *gap audit* — what the plans above don't yet solve, and what the cost of solving each is.

**Audience:** Dealership ownership, operations management, service advisors, master technicians, solution architects, and the AlfaCore engineering team.

**Posture:** Same engineering doctrine as ANDREW v2 Part X — honest boundaries (Pattern 10), auto-detect over config (Pattern 2), per-VIN isolation (Pattern 4). Every Odoo claim in this document is testable against a real v19 Enterprise installation; nothing is asserted from training-data memory alone.

**Status:** Draft v1.0. Outstanding: Pro-tier loaner fleet sizing, OEM data-access posture (Stellantis is the operative reality, not the speculative case), and whether the dealership-mode features should ship in AlfaCore v1 or split to a separate `alfa_dms` suite for B2B customers.

---

## 1. Framework

### 1.1 Methodology

Each JTBD is captured in canonical form:

> *When I [situation], I want to [motivation], so I can [expected outcome].*

For every JTBD, the analysis records:

1. **The job** — situation, motivation, outcome
2. **The actor** — customer persona or staff role
3. **Today's friction** — what fails or frustrates in the current dealer/independent reality
4. **The Odoo fit** — what the named module set provides natively
5. **The gap** — what's missing
6. **The fix classification** — Native / Configuration / Integration / Custom (see §1.3)
7. **AlfaCore module mapping** — which existing or new module owns the fix
8. **Automation opportunity** — where the workflow can run without human touch
9. **KPI / reporting** — how success is measured
10. **Risk / failure mode** — what breaks if the gap isn't closed

### 1.2 JTBD priority taxonomy

| Priority | Definition | Implication |
|---|---|---|
| **P0** | Blocks pilot launch; customer-facing expectation can't be met without it | Must ship in AlfaCore v1 |
| **P1** | Required for scale beyond 50 customers or for Pro-tier viability | Ship in v1.1, locked to pilot exit |
| **P2** | Differentiator vs. generic OBD apps; raises NPS but isn't blocking | Ship post-pilot, demand-validated |
| **P3** | Operational efficiency or future-state; nice to have | Backlog, revisit at 200+ customers |

### 1.3 Fix classification legend

| Class | Definition | Cost shape |
|---|---|---|
| **N** — **Native** | Odoo v19 Enterprise ships the capability; configuration only (no code) | Hours |
| **C** — **Configuration** | Native module, but requires non-trivial Studio work, custom fields, automated actions, server actions | Days |
| **I** — **Integration** | Third-party SaaS or hardware with an API; Odoo connector exists or is a thin shim | Days to weeks |
| **X** — **Custom** | Bespoke Python module, new models, controllers, OWL components | Weeks to months |
| **N+X** | Mostly native, but a custom extension is required to make it luxury-grade | Variable |

Every gap in §2–§4 carries a fix class. The §5 module-fit matrix totals the classification distribution per module.

### 1.4 The Italian platform context

This analysis is calibrated to *Italian-platform* expectations specifically, not to the generic "luxury car" archetype. The relevant tells:

- **Multi-generational ownership patterns.** Alfa and Maserati buyers are disproportionately repeat purchasers and household-multi-vehicle owners. A husband-and-wife Stelvio + Giulia household, or a Stelvio + Levante + GranTurismo collector, is more common than the Bentley/Rolls model of single-flagship purchase.
- **Driving-as-identity.** These owners drive their cars. They are not garage queens. The service relationship is high-frequency (every 6–10K km) and emotionally weighted. The car is read as personal expression.
- **Independent-specialist preference at high mileage.** Owners over 80,000 km routinely defect from dealer service to trusted Italian specialists. AlfaCore's positioning hits this defection zone explicitly.
- **TSB and recall sensitivity.** FCA/Stellantis platforms have well-known weak points (Multi-Air solenoids, transfer case fluid intervals, AFLS calibration drift, Q4 actuator wear). Owners read the forums. They expect their specialist to know more than the forums do.
- **Documentation as luxury signal.** A printed service history with photos and torque-verified entries is a status artifact. Owners reference it at resale.

The audit weights JTBDs accordingly. A Bentley dealership's "Champagne in the lounge" job is *not* prioritized here; "the specialist remembered I run BR1 oil at 5W-40 not 0W-40" *is*.

### 1.5 What this audit explicitly excludes

Honest boundaries up front.

- **New vehicle sales floor.** AlfaCore does not sell new vehicles. The CRM analysis is service-side only.
- **Body shop / collision repair.** Different specialty, different parts network, different insurance workflow. Out of scope for v1.
- **Detail and ceramic coating retail.** Listed in the source prompt but excluded for v1 — these are pass-through revenue at low margin and do not earn module scope on their own. Revisit at P3.
- **Tire / seasonal wheel storage.** Same exclusion. P3 backlog.
- **Insurance claim primary handling.** AlfaCore will surface insurance-relevant documentation but does not act as an insurance intermediary.
- **Multi-tenant DMS-as-a-service.** This audit assumes one operator. If AlfaCore evolves into a platform sold to multiple independent specialist shops, a separate multi-tenancy audit is required.

---

## 2. Customer-Side JTBDs

### 2.1 Discovery & Onboarding

#### JTBD 2.1.1 — Find a specialist that knows my car

> *When my warranty is expiring and I no longer trust the dealer's service department, I want to find an independent specialist who genuinely knows my model, so I can preserve my car's value and avoid being treated as a generic Stellantis VIN.*

| Aspect | Detail |
|---|---|
| Actor | New customer prospect, 60K–120K km, post-warranty defection zone |
| Today's friction | Forum posts, Google reviews, word-of-mouth; no structured way to evaluate specialist competence pre-engagement |
| Odoo fit | **Website** module provides CMS; **CRM** captures inbound leads; **Surveys** can frame an intake questionnaire |
| Gap | Native website is generic; no Italian-platform-specific intake flow; no public-facing "what your scanner will show" preview that proves competence |
| Fix class | **C** for the configured marketing site; **X** for the diagnostic preview tool that proves expertise |
| AlfaCore module | `alfa_core_portal` extends `website`; a new public-facing DTC explainer endpoint surfaces curated `alfa_core.dtc` entries by VIN-decoded platform |
| Automation | Inbound web form → CRM lead → automated qualification email with one curated DTC explainer relevant to the prospect's stated symptom |
| KPI | Lead-to-trial conversion; trial-to-paid conversion |
| Risk | If the public DTC explainer leaks the curated library, the moat erodes — gate behind email capture |

#### JTBD 2.1.2 — Onboard without re-entering my whole car

> *When I sign up, I want my car's history to populate automatically from my VIN, so I'm not retyping eight years of Mopar receipts.*

| Aspect | Detail |
|---|---|
| Today's friction | Every new shop starts from zero; service history lives in PDFs in the customer's email |
| Odoo fit | **Contacts** captures partner record; **Documents** can store PDFs; **Studio** can add custom fields |
| Gap | **No native VIN decoder** in Odoo. **No native OEM service-history pull** (Stellantis Mopar Service does not expose a customer-data API to third parties). |
| Fix class | **X** for VIN decoder (build against NHTSA vPIC public API for the decode, then enrich with `alfa_fleet` Italian-platform lookup tables); **N+X** for service history — accept PDF/photo uploads, OCR via Documents' built-in extraction, write to `alfa_fleet.service.event` records |
| AlfaCore module | `alfa_fleet` (existing in v1.0 plan) + new `alfa_core_onboarding` wizard |
| Automation | VIN entered → vPIC decode → `alfa_fleet.vehicle` auto-populated; PDF receipt upload → OCR → draft service event awaiting customer confirmation |
| KPI | Time-to-first-complete-vehicle-profile; % of historical service events captured at onboarding |
| Risk | NHTSA vPIC is US-centric; Canadian VINs decode but may not return trim/engine cleanly — needs a fallback to manual entry with John's review queue |

#### JTBD 2.1.3 — Trust this stranger with my car's data

> *When I'm being asked for my VIN, location, and driving patterns, I want to understand exactly what's collected, by whom, and what my recourse is, so I can opt in with informed consent.*

| Aspect | Detail |
|---|---|
| Odoo fit | None native — Odoo's GDPR module exists but is opt-in-record-keeping only, no consent UI |
| Gap | PIPEDA-grade consent capture, versioned consent text, granular per-category opt-in, export/erasure endpoints |
| Fix class | **X** — built in `alfa_core_base` per Service Plan §10.2 |
| AlfaCore module | `alfa_core_base` (PIPEDA fields on partner) + `alfa_core_app_api` (export/erasure endpoints) |
| Automation | Annual re-consent reminder if consent text version has changed |
| KPI | Consent capture rate at onboarding; opt-out rate by category; export request response time |
| Risk | A single PIPEDA complaint to the OPC can damage the brand permanently — under-invest here at peril |

#### JTBD 2.1.4 — Pair the scanner without calling support

> *When my AlfaCore scanner arrives, I want to be running my first scan in under five minutes, so the unboxing experience matches the price tag.*

| Aspect | Detail |
|---|---|
| Today's friction | OBD dongles ship with cryptic Bluetooth PIN cards and apps that demand permissions without context |
| Odoo fit | None — pairing UX is entirely in the PWA |
| Fix class | **X** — `alfa_core_app_api` device pairing endpoints + PWA pairing flow |
| Automation | QR code on dongle → camera scan → BLE auto-discover → pairing token validate → device active |
| KPI | Time from box-open to first successful scan (target ≤ 5 min, p90) |
| Risk | iOS Web Bluetooth quirks — pairing must have a native-fallback path documented before pilot |

#### JTBD 2.1.5 — See real value within the first 48 hours

> *When I've just paid for a subscription, I want at least one tangible insight about my car in the first two days, so the purchase feels validated.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Marketing Automation** can drive the email cadence; **Knowledge** can host the content |
| Gap | The *what* of the content — Italian-platform-specific welcome content, generated to the customer's exact VIN/platform/mileage/engine |
| Fix class | **N+X** — Marketing Automation native, custom content generation hook in `alfa_core_diagnosis` |
| Automation | First successful scan → triggered email "Your Stelvio's GME 2.0T at 89,000 km — what to watch for in the next 10,000 km" |
| KPI | 48h activation rate (% with ≥ 1 scan + ≥ 1 content engagement); D7 retention |
| Risk | Generic content feels like spam; the cadence must be tuned to engine code + mileage band, not just "you're a customer" |

---

### 2.2 Profile & Preference Management

#### JTBD 2.2.1 — Tell you about my fluid preferences once

> *When I tell you I run Selenia K Pure Energy 5W-40 instead of the default, I want that recorded against my VIN forever, so the next service I book doesn't list 0W-30.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Contacts** custom fields via Studio; **Inventory** product variants; **Subscriptions** stored preferences |
| Gap | None of the above is structured for *per-VIN* preferences (oil weight, oil brand, brake fluid spec, transmission fluid spec, coolant brand) |
| Fix class | **X** — `alfa_fleet.vehicle.preference` model with strongly-typed slots (oil, brake fluid, coolant, transmission fluid, ATF, transfer case fluid, washer fluid, tire pressure deltas, alignment specs) |
| AlfaCore module | `alfa_fleet` extension — one preference set per vehicle, defaulting from platform/engine but customer-overridable |
| Automation | Service template generation reads the preference set; parts picker filters to the preferred SKU first |
| KPI | % of services completed with customer-preferred fluids vs. shop default |
| Risk | If preferences silently override a manufacturer requirement (e.g., customer prefers 0W-30 but engine requires 0W-20 for Multi-Air longevity), the system must fail loud — Pattern 2 |

#### JTBD 2.2.2 — Be remembered as a person, not a VIN

> *When I call or message, I want the advisor to know my name, my car's history, and the conversation we had last month, so I'm not re-explaining who I am.*

| Aspect | Detail |
|---|---|
| Odoo fit | **CRM** activities log; **Discuss** chatter on partner; **Helpdesk** ticket history |
| Gap | Each module logs in its own silo. A unified "everything we know about this person" pane is not native. |
| Fix class | **C+X** — partner form extension with a custom "Relationship Tape" widget pulling from all silos chronologically |
| AlfaCore module | `alfa_core_portal` (customer view) and a back-office equivalent in `alfa_core_base` |
| Automation | Inbound call/SMS → Caller ID match → partner record pre-opens with Relationship Tape at top |
| KPI | Advisor "context time" — seconds from inbound contact to context fully loaded |
| Risk | Caller ID requires telephony integration (Twilio, Zadarma, OnSIP) — not native |

#### JTBD 2.2.3 — Manage my household's cars in one place

> *When I have a Stelvio and my partner has a Giulia, I want one login, one billing relationship, one calendar, two cars, so we don't have parallel duplicate accounts.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Contacts** supports parent/child partners (company → contact); **Sales** supports multiple ship-to addresses |
| Gap | Not designed for household relationships where both partners are decision-makers on shared assets. Vehicle ownership is single-FK in the v1.0 plan. |
| Fix class | **C+X** — `alfa_fleet.vehicle.ownership` becomes a Many2many through-model with role (`primary_driver`, `secondary_driver`, `account_holder`, `authorized_caller`) |
| AlfaCore module | `alfa_fleet` schema extension |
| Automation | Service notifications respect the role — only `primary_driver` and `account_holder` get pickup-ready pings; both drivers see calendar events |
| KPI | % of multi-vehicle households on consolidated billing |
| Risk | Divorce / vehicle sale workflows must handle ownership transfer cleanly with PIPEDA-correct data separation |

#### JTBD 2.2.4 — Tell you my schedule once

> *When I work weekdays and only have Saturdays, I want every booking option to respect that, so I'm not declining slot offers manually.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Appointments** module allows resource availability rules; **Calendar** can sync customer external calendars |
| Gap | Native Appointments handles *operator* availability, not *customer* availability constraints. Customer prefers can be stored but aren't first-class in slot-suggestion logic. |
| Fix class | **C** — Studio extension of `calendar.event` + automated action filtering proposed slots against partner availability prefs |
| Automation | Booking offer email includes only slots that match preferences |
| KPI | Slot-acceptance rate (offers accepted / offers sent) |
| Risk | None significant |

---

### 2.3 Service Lifecycle From Customer View

#### JTBD 2.3.1 — Diagnose without leaving home

> *When my MIL comes on, I want to know if I'm driving to work safely tomorrow, so I'm not gambling on a Sunday-night warning light.*

This is the AlfaCore core JTBD. Fully covered by the Service Plan §3 and §8. **Fix class N+X — already specified.**

Cross-references: scanner upload → triage rule engine → diagnosis report → recommendation set. P0.

#### JTBD 2.3.2 — Approve the work I want, decline the work I don't

> *When you tell me my car needs $X, I want a line-item breakdown I can approve in parts, so I'm not forced into all-or-nothing.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Sales** order lines can be approved/declined individually via the portal; **Sign** captures signature on the result |
| Gap | The portal sale-order view is industrial — not luxury-grade. Itemization needs to surface diagnostic provenance: "this $340 repair traces to your scan of Oct 14, code P0301." |
| Fix class | **C** — Studio extension of portal sale-order template; **X** — custom field `sale.order.line.alfa_core_diagnosis_id` linking each line back to its source diagnosis recommendation |
| AlfaCore module | `alfa_core_portal` overrides the portal sale view |
| Automation | Line approve/decline triggers re-quote; declined lines log to vehicle file as "customer-acknowledged deferred maintenance" with auto-rebreaker at next visit |
| KPI | Line-level approval rate; deferred-line capture rate at next visit |
| Risk | If the UX permits accidental "approve all" without per-line review, the customer experience inverts to feeling rushed — friction by design |

#### JTBD 2.3.3 — See what they see in real time

> *When my car is in the shop, I want to see photos and videos of what the technician is finding, so I'm not making decisions blind.*

| Aspect | Detail |
|---|---|
| Today's friction | The dealer mails a 30-second walkaround video at most. Some shops use Tekmetric / AutoVitals digital inspection — these are SaaS, not in Odoo's orbit |
| Odoo fit | **Documents** stores files; **Field Service** has limited inline-photo capability; the **mobile app** allows photo upload |
| Gap | **No native digital inspection workflow** in Odoo. No structured "inspection point → photo → severity" model. Photos in Documents are loose files, not anchored to a specific repair line. |
| Fix class | **X** — major build. `alfa_core_inspection.point`, `alfa_core_inspection.template` (configurable per service type), `alfa_core_inspection.line` with photo/video Many2many. PWA technician interface (tablet-first). |
| AlfaCore module | New `alfa_core_inspection` module |
| Automation | Inspection completion → photo gallery published to customer portal → push notification to customer |
| KPI | Inspection completeness; customer engagement with inspection (time spent viewing); approval rate post-inspection |
| Risk | Highest-effort gap in this entire document. Could consume 6 weeks alone. But: this is the *single biggest* perceived luxury differentiator. Not building this leaves AlfaCore feeling like a $24/mo OBD app, not a $59/mo concierge service. |

#### JTBD 2.3.4 — Know when my car is ready

> *When my car is finished, I want to know within 2 minutes — not when I show up at 5pm to find it's been ready since noon.*

| Aspect | Detail |
|---|---|
| Odoo fit | **SMS** module (via IAP or Twilio); **WhatsApp** (Enterprise v17+ via Meta Business API); **email**; portal notifications |
| Gap | Channel selection per customer; deliverability tracking; "ready for pickup" is a workflow state that needs to fire automation across all three channels simultaneously |
| Fix class | **C+I** — Configuration of channel preferences on partner; **I** for WhatsApp Business API setup (requires Meta verification) |
| AlfaCore module | `alfa_core_base` partner extension for channel prefs; `alfa_core_diagnosis` triggers state-change automations |
| Automation | `alfa_service.order.state` → `ready_for_pickup` triggers parallel send across customer-preferred channels |
| KPI | Median notification-to-pickup elapsed time |
| Risk | WhatsApp template messages require pre-approval from Meta; cannot be ad-hoc — must use approved templates |

#### JTBD 2.3.5 — Pick up without ceremony

> *When I arrive to collect my car, I want to walk in, sign once, and drive out — not stand at a counter while paperwork is reprinted.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Sign** for electronic signature; **Accounting** for payment; **Customer Portal** for pre-acceptance |
| Gap | Pre-arrival workflow that completes invoice, payment, and signature in the portal *before* the customer drives in |
| Fix class | **N+C** — Sign and pre-payment are native; portal flow needs Studio configuration to chain them |
| Automation | "Ready" state → automated portal task: review invoice → e-sign acceptance → pay → key release token issued |
| KPI | "Counter time" — minutes from arrival to drive-away (target ≤ 3 min for fully pre-cleared customers) |
| Risk | Payment failure at counter is a luxury-experience-killer; pre-payment must be optional but heavily incentivized |

#### JTBD 2.3.6 — Get a loaner that doesn't feel like punishment

> *When my car is in for a week, I want a loaner that's at least platform-comparable (no Compass when I drive a Stelvio), so the service experience doesn't downgrade my daily.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Fleet** module manages owned vehicles — fuel, contracts, internal services. **NOT** designed for loaner allocation to customers. **Rental** module exists for B2C rental but is not service-loaner-aware. |
| Gap | Loaner-vehicle allocation requires: availability calendar per loaner, customer-vehicle ↔ loaner-tier matching, mileage/condition photo capture in/out, insurance verification, fuel-state tracking, damage waiver Sign workflow |
| Fix class | **X** — new `alfa_core_loaner` module |
| AlfaCore module | New `alfa_core_loaner` — depends on Fleet (for the loaner vehicle records themselves), Sign (waiver), Documents (insurance), Field Service (delivery if home-pickup is offered) |
| Automation | Service order date → loaner allocation suggestion → customer pre-confirms tier → in/out condition workflow on arrival/return |
| KPI | Loaner tier match rate; loaner damage incident rate; customer satisfaction delta with vs. without loaner |
| Risk | Loaner insurance is non-trivial. The shop's commercial policy must cover customer-driven loaners. Out-of-scope for Odoo to manage — surface it as a documentation requirement on the loaner agreement. |

#### JTBD 2.3.7 — Trade my car when I'm ready to upgrade

> *When I'm ready to replace my Stelvio with a Giulia Quadrifoglio, I want a frictionless trade evaluation, so I'm not starting from zero with a new dealer.*

| Aspect | Detail |
|---|---|
| Today's friction | Dealer trade-ins are adversarial by design |
| Odoo fit | **CRM** opportunity; **Sales** for purchase order to customer; **Accounting** for the credit |
| Gap | Vehicle trade-in is a B2C *purchase* by the shop — Odoo's purchase flow is supplier-side, not consumer-side. The valuation logic, condition assessment, title-clearing workflow are bespoke. |
| Fix class | **X** — `alfa_core_tradein` if AlfaCore wants to be in this business. Likely **P3** for AlfaCore v1; defer until the service operation matures. |
| AlfaCore module | Not in v1 scope; flag as future consideration |
| Risk | Title transfer, lien clearing, and provincial registry interactions are jurisdiction-specific and high-friction — out of scope for software alone |

#### JTBD 2.3.8 — Have my warranty work tracked without dealer politics

> *When I have an open recall or warranty repair, I want my specialist to know about it and help me navigate Stellantis even if my car isn't going back to a Stellantis dealer for routine work.*

| Aspect | Detail |
|---|---|
| Odoo fit | None native for OEM warranty/recall tracking |
| Gap | **No public Stellantis API for recall lookup or warranty status.** NHTSA recall database is public (VIN lookup endpoint), but warranty status is OEM-private |
| Fix class | **I** — NHTSA recall API integration for public recalls; **N+X** — manual capture of warranty open campaigns by customer photo of dealer notice or by `alfa_tsb` cross-reference |
| AlfaCore module | `alfa_core_diagnosis` augments scan output with NHTSA recall lookup; `alfa_fleet.vehicle` carries `open_recalls` and `open_warranty_campaigns` fields |
| Automation | Weekly cron pulls NHTSA recalls by VIN for active customers; new recall → push notification + service order proposal |
| KPI | Recall-closure rate among AlfaCore customers vs. baseline |
| Risk | NHTSA covers US-issued recalls; Transport Canada has its own list — both must be polled for Canadian customers (Transport Canada Vehicle Recalls Database, public web scrape only) |

---

### 2.4 Communication & Visibility

#### JTBD 2.4.1 — Reach you the way I prefer

> *When I prefer WhatsApp over email, I want everything to come through WhatsApp, so I'm not chasing notifications across three apps.*

| Aspect | Detail |
|---|---|
| Odoo fit | **SMS** (via Odoo IAP or Twilio); **WhatsApp** (Enterprise v17+); **email**; **Discuss** for in-portal |
| Gap | Channel preference must be honored consistently across every notification source — service status, parts arrival, invoice ready, recall published, scan completed |
| Fix class | **C** — partner extension `preferred_channel`, central mail-routing function that respects it |
| AlfaCore module | `alfa_core_base` |
| Automation | All outbound notifications route through a single helper `_alfa_core_notify(partner, template, context)` that respects the partner's `preferred_channel` |
| KPI | Notification-open rate by channel; channel-preference distribution |
| Risk | WhatsApp Business API per-conversation pricing — accidental over-notification gets expensive; rate-limit at the helper |

#### JTBD 2.4.2 — Know which is urgent without anxiety

> *When you push a notification, I want to know in two seconds whether it's "your car is ready" or "we found something during inspection," so I'm not opening every alert with dread.*

| Aspect | Detail |
|---|---|
| Odoo fit | None native — notification UX is generic |
| Fix class | **C** — visual severity convention in push payloads and message templates |
| Automation | Severity inheritance from the originating record (diagnosis severity → notification severity) |
| KPI | Notification-to-action latency stratified by severity |
| Risk | Severity inflation by overuse destroys the signal — strict criteria for `urgent` |

#### JTBD 2.4.3 — Reach a human when I want to

> *When I'm uncertain, I want to talk to John or an advisor — not navigate a help center or wait three days for an email.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Helpdesk** for ticketing; **Discuss** for live chat; **WhatsApp** for two-way messaging |
| Gap | Native live chat is desktop-web-oriented; mobile chat parity requires PWA work |
| Fix class | **C+X** — Helpdesk for asynchronous; PWA chat panel wraps Discuss for mobile parity |
| AlfaCore module | `alfa_core_portal` mobile chat |
| Automation | Diagnosis state `escalated` auto-creates Helpdesk ticket assigned to John |
| KPI | First-response time on Pro tier (target ≤ 4 business hours) |
| Risk | Living up to the SLA — Pro pricing depends on it |

#### JTBD 2.4.4 — Don't make me read paperwork

> *When you send me a 14-page service invoice, I want a one-screen summary up top, so I only read the detail if I want to.*

| Aspect | Detail |
|---|---|
| Odoo fit | QWeb report templates support arbitrary layout |
| Gap | Default Odoo invoice/sale-order PDFs are industrial — they look like B2B SaaS receipts, not luxury statements |
| Fix class | **C** — Studio + custom QWeb templates with Industrial Futurism styling, header summary card, detailed breakdown below |
| AlfaCore module | `alfa_core_portal` ships custom QWeb templates for sale order, invoice, service order, diagnosis report |
| KPI | Document open rate; customer-reported satisfaction with paperwork clarity |
| Risk | Brand-consistent design system across QWeb, PWA, web, and email requires designer-engineer coordination — easy to drift |

#### JTBD 2.4.5 — Get reminded once

> *When I forget my appointment, I want one well-timed reminder — not five.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Appointments** + **Marketing Automation** reminders; **Calendar** auto-reminders |
| Gap | Coordinating reminders across modules so the customer gets *one* well-timed reminder per channel per event |
| Fix class | **C** — central reminder dispatcher in `alfa_core_base`, suppressing duplicates |
| Automation | Appointment T-24h → single reminder via preferred channel; T-2h → second reminder; T-0 → arrival confirmation prompt |
| KPI | No-show rate; complaint rate about over-notification |
| Risk | The default Odoo cadence sends from multiple modules — accidentally over-noisy; suppression must be opt-in not opt-out at the dispatcher |

#### JTBD 2.4.6 — Re-open the conversation we had before

> *When I message you about a noise I noticed last week, I want the conversation to thread to our last exchange, so I'm not re-explaining the symptom.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Discuss** threads on partner record; **Helpdesk** threads on ticket |
| Gap | Threads scatter across record types. A single "everything I've ever said to AlfaCore" timeline doesn't exist natively |
| Fix class | **C+X** — partner-scoped chatter aggregation view; possibly an OWL component pulling from `mail.message` filtered by `author_id == partner.user_id` |
| AlfaCore module | `alfa_core_base` adds a "Conversations" tab on partner form |
| KPI | Advisor onboarding time (new advisor reading customer history) |
| Risk | None significant — purely additive |

---

### 2.5 Loyalty, Community, Advocacy

#### JTBD 2.5.1 — Refer my friends without paperwork

> *When my friend asks who I trust with my Alfa, I want to send them a referral link that's tracked, so we both get credit.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Loyalty** program exists in Sales (loyalty points, gift cards); referral-link tracking is not native |
| Fix class | **C+X** — referral codes on `res.partner`, attribution via UTM on signup link, reward triggered when referred party completes first paid service |
| AlfaCore module | `alfa_core_base` |
| Automation | Referrer earns subscription credit; referee earns first-service discount |
| KPI | Referral-attributed conversion rate; CAC reduction via referral |
| Risk | None significant; pace the program — over-rewarded referrals lose authenticity |

#### JTBD 2.5.2 — Belong to a community of owners

> *When I'm proud of my Quadrifoglio, I want to see other Quadrifoglios serviced by you — without doxxing anyone — so I feel part of a peer group.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Website** can host a gallery; **eLearning** supports community content |
| Gap | Privacy-aware "anonymized Quadrifoglio gallery" is a content/curation problem, not a software problem |
| Fix class | **C** — curated Knowledge articles + Website gallery |
| Automation | None |
| KPI | Gallery engagement; community-event signup |
| Risk | A poorly-curated gallery looks like a marketing brochure; the bar is genuine community signal |

#### JTBD 2.5.3 — Get invited to events worth attending

> *When you host a Sunday-morning Stelvio cars-and-coffee, I want to know, so I can show up.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Events** module — full event lifecycle, registration, ticketing, attendance |
| Gap | Targeting (only Stelvio owners invited to a Stelvio meet) is configurable but not automatic |
| Fix class | **N+C** — Events module + segment filter on `alfa_fleet.vehicle.model` |
| Automation | Event creation → auto-segmented email blast to matching VIN owners |
| KPI | Event attendance; post-event NPS lift |
| Risk | Events that don't happen damage the brand more than absence — over-promise risk |

#### JTBD 2.5.4 — Be recognized as a longtime customer

> *When I've been with you four years across three cars, I want to be treated like it — without needing to remind anyone.*

| Aspect | Detail |
|---|---|
| Odoo fit | Partner-record date fields and aggregate spend are native |
| Gap | A "tenure tier" surfaced to advisors and surfaced visually in the partner record |
| Fix class | **C** — computed field `customer_tier` (Bronze / Silver / Gold / Platinum) based on tenure × cumulative spend |
| Automation | Tier change triggers congratulatory message; advisor UI surfaces tier badge |
| KPI | Tier-distribution drift; retention by tier |
| Risk | Tier systems can feel transactional — keep the messaging warm, not points-based |

---

### 2.6 Multi-Vehicle / Multi-Household

#### JTBD 2.6.1 — Switch cars in the app without re-logging

> *When I scan my Stelvio Monday and my Giulia Wednesday, I want to switch between them in the app like switching between mailboxes.*

| Aspect | Detail |
|---|---|
| Odoo fit | Partner-vehicle One2many is native |
| Fix class | **C** — PWA vehicle-picker component |
| Automation | First scan after subscription includes a "set this as your default vehicle" prompt |
| KPI | Multi-vehicle engagement ratio |
| Risk | None significant |

#### JTBD 2.6.2 — Share a vehicle's status with my partner

> *When my Giulia is in for service, I want my husband to get the pickup notification too — without sharing my password.*

Covered by §2.2.3 ownership-role model. **P1 to ship.**

#### JTBD 2.6.3 — Move a car between households when life changes

> *When I sell my Stelvio to my brother-in-law, I want his account to inherit the service history with my consent — not start from zero.*

| Aspect | Detail |
|---|---|
| Odoo fit | None native |
| Fix class | **X** — `alfa_core_transfer` wizard with explicit consent capture from both partners, PIPEDA-compliant data transfer |
| AlfaCore module | `alfa_fleet` ownership-transfer wizard |
| Automation | Title transfer record triggers data-transfer prompt |
| KPI | Transfer requests fulfilled; retention of receiving party |
| Risk | Consent capture must be auditable — both partners' confirmation logged |

---

### 2.7 Lifecycle Events

Covered partially in §2.3.7 (trade-in) and §2.3.8 (warranty/recall). The remaining lifecycle events — long-term storage, decommission, donation — are P3 backlog for v1.

---

## 3. Service Department / Mechanic JTBDs

### 3.1 Service Advisor

#### JTBD 3.1.1 — Open the day knowing who's coming and what's needed

> *When I arrive at 7am, I want a prioritized list of today's customers with their vehicles, scans, and parts status — not a series of separate screens.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Calendar** day view; **Project** kanban; **Field Service** day view; **Helpdesk** queue |
| Gap | These views don't compose. A single "advisor cockpit" pulling appointments + diagnostic scans + parts arrivals + escalations in one screen is not native |
| Fix class | **X** — `alfa_core.advisor.cockpit` view, OWL-based dashboard pulling from `alfa_service.order`, `alfa_core.scan.session`, `purchase.order` |
| AlfaCore module | `alfa_core_portal` (back-office mode) |
| Automation | Auto-prioritization by appointment time, parts-arrival status, escalation tier |
| KPI | Time-to-first-customer-contact each morning |
| Risk | Cockpit becomes a wall of badges if not curated — restrict to the next 8 hours of work |

#### JTBD 3.1.2 — Generate an accurate estimate fast

> *When a customer calls about a noise, I want to generate a plausible estimate in under five minutes, so they can decide whether to book.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Sales** quotation with **Project** templates; **Inventory** parts catalog with pricing |
| Gap | Diagnostic-driven estimate generation. "Customer reports a clunk from the rear; suspect rear subframe bushing on Giorgio platform at 110K km" → templated estimate with parts + labor |
| Fix class | **X** — `alfa_core_diagnosis.symptom.template` library, each carrying parts list + labor hours + confidence range |
| AlfaCore module | `alfa_core_diagnosis` |
| Automation | Symptom keyword match → templated estimate populated; advisor reviews and sends |
| KPI | Quote-to-book conversion; quote-accuracy variance (estimate vs. final invoice) |
| Risk | Templates that don't fit the case lead to under-quoting — confidence range must be visible to the advisor |

#### JTBD 3.1.3 — Coordinate parts before the car arrives

> *When a customer books a brake job for next Tuesday, I want the parts ordered today and confirmed before the car is in the bay — not Tuesday morning finding out they're on backorder.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Purchase** orders; **Inventory** reordering rules; **Sales** order-driven procurement |
| Gap | The booking → parts-order linkage is configurable but not first-class. Multi-source parts (dealer counter vs. online vs. aftermarket) need vendor preference per part |
| Fix class | **C+X** — `alfa_parts` (from v1.0) carries vendor-preference per part; Purchase auto-generation from booked service order |
| Automation | Booking → check inventory → reserve or back-order → vendor PO created and emailed |
| KPI | "Parts ready at bay" rate; back-order events per month |
| Risk | Dealer-counter parts (Alfa Romeo of Toronto, Maranello) often require phone-call ordering, not automated — workflow must accommodate manual confirm |

#### JTBD 3.1.4 — Handle the customer who's anxious

> *When a customer is worried, I want to call them with the right information ready — not wing it.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Discuss** call activity; **CRM** activities |
| Fix class | **C** — call-prep template on the customer's "Relationship Tape" (§2.2.2) |
| Automation | "Schedule callback" activity → 30-min reminder → pre-populated context loaded |
| KPI | Anxious-customer escalation rate; resolved-on-first-call rate |
| Risk | None significant |

#### JTBD 3.1.5 — Get sign-off without playing tag

> *When the technician finds something during inspection, I want a streamlined approval workflow that doesn't depend on the customer answering their phone right now.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Sign** for e-signature; **SMS**/**WhatsApp** for the prompt; **Customer Portal** for the review interface |
| Fix class | **C** — chained automation: inspection finding → portal task → push notification → e-sign → state transition |
| Automation | Per JTBD 2.3.2 — covered |
| KPI | Approval round-trip time |
| Risk | None significant |

#### JTBD 3.1.6 — Don't lose money on warranty work

> *When I do warranty work, I want the labor and parts captured cleanly for OEM reimbursement, so we're not chasing chargebacks.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Accounting** analytic accounts; **Project** for cost capture |
| Gap | OEM warranty submission formats are Stellantis-specific (eAuthority for FCA brands). No native integration. |
| Fix class | **X** if AlfaCore is doing this volume; **N+C** if warranty work is rare — use analytic accounts to capture cost and submit manually |
| AlfaCore module | None at v1; flag as P2 if independent-warranty-work volume grows |
| Risk | Stellantis eAuthority requires authorized-dealer login — independent specialists generally cannot submit; this JTBD applies more to a future authorized-dealer customer than to John's independent operation |

#### JTBD 3.1.7 — Communicate with the technician without walking the bay

> *When a customer calls with a question, I want to message the tech working on the car — not walk back to the bay or page them.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Discuss** internal messaging; @mentions trigger notifications |
| Fix class | **N** — Discuss native |
| Automation | None needed |
| KPI | Bay-walk frequency; advisor productivity |
| Risk | Discuss is desktop-default; tablet/phone parity in the bay needs the mobile Odoo app to be active and notifications enabled |

#### JTBD 3.1.8 — End the day with cleanup not chaos

> *When I leave at 6pm, I want every car closed, every customer notified, every payment captured — not three loose ends.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Project** kanban end-of-day; **Discuss** activities review |
| Fix class | **C** — end-of-day cockpit view, same OWL component as 3.1.1 |
| Automation | 5pm trigger → "open items requiring close" digest |
| KPI | Day-end open-item count |
| Risk | None significant |

---

### 3.2 Technician

#### JTBD 3.2.1 — See the full diagnostic context before turning a wrench

> *When I open a hood, I want the scan history, the customer's reported symptom, the prior services on this car, and any open TSBs — without paging through tabs.*

| Aspect | Detail |
|---|---|
| Odoo fit | Field Service mobile view shows the current task; lacks the longitudinal vehicle context |
| Fix class | **X** — tablet-optimized "tech view" pulling from `alfa_fleet.vehicle`, `alfa_core.scan.session`, `alfa_service.order` history, `alfa_tsb` retrieval |
| AlfaCore module | New `alfa_core_tech_view` (or roll into `alfa_core_portal` back-office) |
| Automation | Scan trigger from bay tablet → instant context refresh |
| KPI | Time-to-first-wrench (clock-on to wrench-on) |
| Risk | Tablet UX must be glove-friendly, oil-resistant — design constraint, not software constraint, but informs interaction patterns |

#### JTBD 3.2.2 — Document work without typing

> *When I'm under a Stelvio, I want to capture findings via voice or photo — not stop, wash up, and type into a laptop.*

| Aspect | Detail |
|---|---|
| Odoo fit | Mobile app supports photo capture; voice-to-text via OS keyboard only |
| Gap | Structured voice capture (e.g., "Found play in the front lower control arm bushing") that auto-files to the right inspection point |
| Fix class | **X** — PWA voice-to-text wrapper + LLM classifier mapping free-text to inspection-point taxonomy |
| AlfaCore module | `alfa_core_inspection` (per JTBD 2.3.3) |
| Automation | Voice → text → classify → attach to current task |
| KPI | Inspection documentation completeness; tech satisfaction |
| Risk | Voice-to-text accuracy on technical terms (Multi-Air, transfer case, AFLS) is the limiting factor — needs a curated technical vocabulary file |

#### JTBD 3.2.3 — Capture torque-verified completion

> *When I torque a hub nut to spec, I want a record that the torque was verified — for warranty, for liability, for the customer's history.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Quality** module supports quality-check points but is manufacturing-shaped (MRP-bound) |
| Gap | Service-mode quality check workflow with torque values, fluid amounts, photo confirmation |
| Fix class | **N+C** — Quality module's `quality.point` can be wired to non-manufacturing models with effort; or **X** for a service-specific `alfa_service.quality.check` model |
| AlfaCore module | `alfa_service` extension |
| Automation | Service task completion requires checks signed off; missing check blocks ready-for-pickup state |
| KPI | Quality-check compliance rate; rework rate |
| Risk | Quality module's coupling to MRP can be fragile — a clean custom model may cost less than fighting Quality's assumptions |

#### JTBD 3.2.4 — Get parts to the bay without leaving the bay

> *When I need a torque wrench or a part, I want to request it from the tablet — not walk to the parts counter.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Inventory** picking; **Discuss** for messaging |
| Fix class | **C** — "parts request" workflow from tech view → parts manager notification |
| Automation | Request → inventory check → pick task generated → delivered to bay |
| KPI | Bay-to-counter walk frequency |
| Risk | None significant |

#### JTBD 3.2.5 — Connect bay diagnostic equipment to the customer record

> *When I plug a scope, smoke machine, or wheel aligner into a car, I want the results captured against the customer file — not stored on a USB stick.*

| Aspect | Detail |
|---|---|
| Odoo fit | **IoT** module supports IoT-Box-bridged hardware (scales, printers, barcode scanners, measurement devices) |
| Gap | Most bay diagnostic equipment (Hunter aligners, Snap-on scopes, scan tools) don't speak the IoT Box protocol natively. Data extraction is per-device. |
| Fix class | **I+X** — IoT Box for any device that exposes a generic interface (RS-232, USB-HID, network); per-device drivers for the rest |
| AlfaCore module | `alfa_core_iot` if pursued — likely P2/P3 |
| Automation | Equipment session start → bind to active service order → results upload on completion |
| KPI | Equipment-data attached rate (results captured / equipment sessions) |
| Risk | High effort per equipment type. Triage: integrate the equipment that's used most often (wheel aligner, fluid evacuator), accept that others stay manual |

#### JTBD 3.2.6 — Track my own productivity honestly

> *When I'm rated on hours billed vs. clocked, I want a clear view of where my time went — not a manager's spreadsheet.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Timesheets** on **Project** tasks; **Field Service** time capture |
| Gap | Flat-rate vs. actual analysis — comparing billed flat-rate hours to clocked actual hours per task type |
| Fix class | **C** — computed analytic on timesheet entries; **N+C** for the dashboard |
| AlfaCore module | `alfa_service` analytic extension |
| Automation | Auto-clock on task open; clock off on close (configurable) |
| KPI | Flat-rate efficiency (billed / actual); per-task variance |
| Risk | Tech distrust if the system feels surveillant — frame as "your own performance dashboard," not "manager's tool" |

#### JTBD 3.2.7 — Hand off cleanly at end of shift

> *When my shift ends mid-job, I want the next tech to inherit clean state — not reverse-engineer what I did.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Project** task transfer; **Discuss** handoff notes |
| Fix class | **C** — hand-off template (state of work, parts open, special notes, photos) attached to task transfer |
| Automation | Shift-end → open-task list → prompt to handoff |
| KPI | Handoff completeness; cross-shift rework rate |
| Risk | None significant |

---

### 3.3 Parts Manager

#### JTBD 3.3.1 — See parts flowing in three directions at once

> *When I'm running the parts counter, I'm managing dealer-counter orders, online-aftermarket arrivals, and customer DIY parts pickups — all on the same day.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Purchase**, **Inventory**, **Sales** — each strong individually |
| Gap | A unified parts-flow view showing inbound (PO arrivals), outbound (bay needs), and customer-pickup queue |
| Fix class | **C** — parts cockpit view, same OWL pattern as advisor cockpit |
| AlfaCore module | `alfa_parts` extension |
| Automation | PO receipt → bay-need match → auto-allocate or set aside |
| KPI | Parts-misallocation events; inventory accuracy |
| Risk | Manual receiving discipline must hold — bad data in, bad cockpit out |

#### JTBD 3.3.2 — Cross-reference part numbers fast

> *When a customer asks for `68377611AA` and we only carry `68377611-AA`, I want the system to recognize them as the same part — not show "no results."*

| Aspect | Detail |
|---|---|
| Odoo fit | None — Odoo part search is literal |
| Fix class | **X** — `canon_part_number` field (Pattern 7) plus a normalizer function |
| AlfaCore module | `alfa_parts` |
| Automation | All inbound part-number references run through the normalizer |
| KPI | Part-search hit rate |
| Risk | None significant |

#### JTBD 3.3.3 — Know which aftermarket alternatives are safe

> *When OEM is on backorder and the customer needs the car back, I want to know which aftermarket SKUs are dealer-grade-safe — not just "in stock."*

| Aspect | Detail |
|---|---|
| Odoo fit | None native |
| Fix class | **X** — `alfa_parts.alternative` model linking OEM SKU to evaluated aftermarket SKUs with `evaluation_grade` (safe / interim / not-recommended) plus the source evaluation note |
| AlfaCore module | `alfa_parts` |
| Automation | OEM out-of-stock → suggest evaluated alternatives with grade |
| KPI | Alternative-suggestion acceptance rate |
| Risk | The evaluation library is John's domain expertise — captures of conversations like `Alfa Stelvio transfer case fluid compatibility` literally feed this table |

#### JTBD 3.3.4 — Forecast demand on Italian-platform-specific parts

> *When summer hits, I want to know we'll need more coolant, AC condensers, and 5W-40 — without manually counting.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Inventory** reordering rules; **Forecasting** capability is limited in Odoo |
| Fix class | **C** — seasonal-pattern multipliers on reordering rules |
| Automation | Time-of-year demand curve applied to forecast |
| KPI | Stockout rate by season |
| Risk | Forecast accuracy is data-volume-dependent; first 12 months will be guess-based |

---

### 3.4 Shop Foreman / Service Manager

#### JTBD 3.4.1 — Allocate bays without thinking

> *When I have eight bays and twelve cars, I want bay allocation to optimize for tech skill, equipment, and time — not require my judgment every morning.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Planning** module — shift/resource planning; **Project** task assignment |
| Gap | Bay-as-resource is configurable but the constraint logic (which bay has the AC machine, which tech is certified for AFLS calibration) needs custom modeling |
| Fix class | **C+X** — Planning module + custom constraints on `alfa_service.bay` model |
| AlfaCore module | `alfa_service` extension |
| Automation | Daily allocation proposal generated at end-of-prior-day; manual override available |
| KPI | Bay utilization; allocation-override rate |
| Risk | Over-automation removes the foreman's judgment, which is the actual production-management value-add — surface as proposal, not assignment |

#### JTBD 3.4.2 — Catch problems before customers do

> *When a tech's quality-check failures spike, I want to know within a day — not in a month's review.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Quality** module reports if used; **Dashboards** via Studio |
| Fix class | **C** — daily KPI digest auto-emailed |
| Automation | Threshold breach → alert |
| KPI | Quality-check failure trend |
| Risk | False positives destroy trust in alerts — tune thresholds against real data |

#### JTBD 3.4.3 — Run the shop on a single screen

> *When I walk through the shop, I want one tablet that shows me every bay's status, every tech's task, every escalation — at a glance.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Project** kanban; **Field Service** views |
| Fix class | **C** — foreman dashboard composing existing views |
| Automation | Auto-refresh; bay-state color coding |
| KPI | Foreman walk-time efficiency |
| Risk | None significant |

#### JTBD 3.4.4 — Onboard a new tech without losing weeks

> *When I hire, I want documented procedures, calibrations, and shop standards available in one place — not in five mentors' heads.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Knowledge** module — hierarchical articles, version history |
| Fix class | **N+C** — Knowledge native; content curation is the cost |
| Automation | None |
| KPI | New-tech ramp time |
| Risk | Knowledge content quality is the dependent variable — schedule the curation work |

#### JTBD 3.4.5 — Handle the recall surge cleanly

> *When Stellantis announces a recall affecting 40 of my customers, I want a campaign workflow — not 40 phone calls.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Marketing Automation** for outreach; **CRM** for campaign tracking |
| Gap | Vehicle-population segmentation by recall criteria (VIN range, build date, platform) needs custom logic |
| Fix class | **C+X** — recall-campaign model with VIN-range filter on `alfa_fleet.vehicle` |
| AlfaCore module | `alfa_core_diagnosis` or new `alfa_core_campaign` |
| Automation | Recall published → matching customers identified → outreach sequence triggered |
| KPI | Recall-closure rate; time-to-first-customer-contact post-announcement |
| Risk | False-positive matching (wrong VIN range) damages credibility — segmentation must be auditable |

---

### 3.5 General Manager / Ownership

#### JTBD 3.5.1 — Know the business is healthy without opening 12 reports

> *When I check in on the operation, I want one dashboard showing revenue, throughput, NPS, churn, and red flags.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Dashboards** via Studio; **Accounting** reporting; **CRM** analytics |
| Fix class | **C** — composite dashboard |
| Automation | Daily KPI digest |
| KPI | The dashboard itself |
| Risk | Dashboard sprawl — limit to 6 top-line numbers |

#### JTBD 3.5.2 — Forecast cash flow including parts payables

> *When I'm planning next month, I want forecasted parts payables, subscription revenue, and labor capacity — combined.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Accounting** cash-flow reporting; **Subscriptions** MRR |
| Fix class | **N+C** — native Accounting + custom view combining streams |
| Automation | Forecast refresh weekly |
| KPI | Forecast accuracy variance |
| Risk | Subscription revenue is reasonably predictable; service revenue is lumpy — model variance honestly |

#### JTBD 3.5.3 — Audit any customer interaction

> *When something goes wrong, I want to reconstruct exactly what happened — every message, every decision, every signoff.*

| Aspect | Detail |
|---|---|
| Odoo fit | Odoo's audit log captures field-level changes; mail.message captures communications |
| Fix class | **N** — already there for compliance basics |
| Automation | None |
| KPI | Audit-request fulfillment time |
| Risk | Audit data must be PIPEDA-export-clean — see §2.1.3 |

#### JTBD 3.5.4 — Know when to expand vs. hold

> *When I'm considering hiring a second tech or a second location, I want utilization data and trend data — not gut feel.*

| Aspect | Detail |
|---|---|
| Odoo fit | Combined view from Planning, Timesheets, Accounting |
| Fix class | **C** — capacity-utilization dashboard |
| Automation | Monthly digest |
| KPI | Capacity-utilization ratio |
| Risk | Lagging indicator — pair with leading indicators (booking velocity, waitlist length) |

---

### 3.6 Mobile / Field Service Technician

#### JTBD 3.6.1 — Service the customer where they are

> *When a customer can't drive in (battery dead, won't start), I want to be dispatched with everything I need — not show up missing a part.*

| Aspect | Detail |
|---|---|
| Odoo fit | **Field Service** module — designed for this |
| Fix class | **N+C** — Field Service plus the parts pre-loading workflow |
| Automation | Field-service task → required parts → van inventory check → dispatch when complete |
| KPI | Field-service first-time-fix rate |
| Risk | Field service is genuinely a different operational model — pilot small before committing |

#### JTBD 3.6.2 — Capture work from outside the shop

> *When I'm on a driveway, I want the same documentation discipline as in the bay — photos, signatures, parts.*

Covered by Field Service module + `alfa_core_inspection` (per JTBD 2.3.3). **N+X.**

#### JTBD 3.6.3 — Handle payment in the field

> *When I finish a roadside service, I want to charge the customer there — not invoice and chase.*

| Aspect | Detail |
|---|---|
| Odoo fit | **POS** module; mobile payment hardware via IoT Box or third-party (Stripe Terminal) |
| Fix class | **N+I** — Stripe Terminal Tap-to-Pay on iPhone with Odoo POS bridge |
| Automation | Service complete → POS payment → invoice issued |
| KPI | Field-service collection rate |
| Risk | Payment hardware reliability in field conditions |

---

### 3.7 Quality, Delivery, Detail

Combined here as one role-family. The luxury delivery experience — clean car, branded mat, customer walk-around — is largely a procedural discipline rather than a software workflow. The relevant software touches:

- **Pre-delivery checklist** — `alfa_service.quality.check` (per JTBD 3.2.3) covers procedure capture
- **Delivery photos** — `alfa_core_inspection` (per JTBD 2.3.3) captures the final state for the customer's record
- **Customer walk-around scheduling** — Calendar block; advisor commits to a delivery time, not "come whenever"

**Fix class for the bundle:** N+C, no new modules needed beyond the inspection module already required.

---

## 4. Cross-Cutting Concerns

### 4.1 Communication channel matrix

| Channel | Inbound | Outbound | Two-way | Odoo support | AlfaCore role |
|---|---|---|---|---|---|
| **Email** | Native (mail.thread) | Native | Yes | Strong | All record types route via Discuss |
| **SMS** | Limited (Twilio reply webhook) | Native (via IAP or Twilio) | Limited | Moderate | Notifications + short status |
| **WhatsApp** | Enterprise v17+ | Enterprise v17+ | Yes | Moderate (Meta Business API required) | Primary for international/Italian customers; secondary for North American |
| **Voice call** | Telephony integration required (Twilio, Zadarma, OnSIP) | Same | Yes | Weak — connectors exist but UX is thin | Advisor-initiated; not customer-self-serve |
| **Portal in-app** | Native | Native (Discuss + notifications) | Yes | Strong | Default for asynchronous |
| **Push notification** | n/a | PWA + service worker | n/a | Custom in PWA | Time-critical only |
| **Letter / printed** | n/a | QWeb report → mail | One-way | Strong | Annual service-summary report; tier-recognition letters |

**Gap:** Native unified channel-preference routing (the `_alfa_core_notify` helper per JTBD 2.4.1) is not in Odoo. **Fix: C — single shim in `alfa_core_base`.**

### 4.2 Document & signature lifecycle

| Document type | Generation | Storage | Signature | Customer access |
|---|---|---|---|---|
| Estimate / quote | Sales QWeb (custom template) | sale.order record | Sign module | Portal + email PDF |
| Service authorization | Sales/Project hybrid | sale.order or project.task | Sign module | Portal |
| Loaner agreement | Custom QWeb | `alfa_core_loaner.agreement` | Sign module | Portal |
| Invoice | Accounting QWeb | account.move | Sign optional | Portal |
| Inspection report | Custom QWeb | `alfa_core_inspection.report` | Not required | Portal |
| Diagnostic report | Custom QWeb | `alfa_core.diagnosis.report` | Not required | Portal + PWA |
| PIPEDA export | Custom Python | Filesystem (signed URL) | Not required | One-time signed download |
| Annual service summary | Custom QWeb | `res.partner.service_summary` | Not required | Portal + mailed letter |

**Fix class for the bundle:** C+X — Sign is native; templates need custom design (Industrial Futurism); the export and inspection report require X.

### 4.3 Photo / video as canonical evidence

The single most under-served area in Odoo for automotive service. Native `ir.attachment` is suitable for storage but not for:

- **Per-inspection-point anchoring** (each photo tied to a check)
- **Side-by-side comparison** (before/after, this-visit vs. previous-visit)
- **Privacy-aware redaction** (license plates, faces in background)
- **Bulk capture from tablet** (rapid-fire intake walkaround)

**Fix class: X** — `alfa_core_inspection` is the host module for this. Major build, single highest-leverage investment after the diagnosis engine itself.

### 4.4 IoT and bay equipment

Odoo's **IoT** module (Enterprise) supports the IoT Box hardware for limited device categories: barcode scanners, scales, receipt printers, measurement tools speaking IoT Box protocol. The expensive bay equipment in a luxury service environment — Hunter wheel aligners, Snap-on Modis scopes, Tekmetric/AutoVitals tablets, ATEQ tire-pressure tools — generally does not speak that protocol natively.

**Realistic posture:**

- IoT Box for: shop printer, barcode/QR scanner for parts intake, parts scale
- Manual integration for: bay diagnostic equipment results captured via screenshot/PDF upload, OCR via Documents
- Custom integration only for: equipment where vendor exposes an API and volume justifies (likely Hunter aligners first, due to alignment frequency)

**Fix class: N (IoT for cheap), I (vendor APIs where available), X (proprietary), defer many to P3.**

### 4.5 OEM integration — the honest map

| OEM data source | Public? | Useful? | Realistic access |
|---|---|---|---|
| **NHTSA recall lookup** | Public | Yes | API integration straightforward |
| **NHTSA vPIC VIN decode** | Public | Yes — minimum viable VIN decoder | API integration straightforward |
| **Transport Canada recall database** | Public web only | Yes for Canadian customers | Scrape; manual until ETL written |
| **Stellantis Mopar TechAuthority** | Subscription | Yes — TSBs, service procedures | Per-seat subscription; not API |
| **Stellantis eAuthority warranty** | Dealer-only | High | Requires authorized-dealer status — out of independent-specialist scope |
| **Stellantis SDMS dealer data feed** | Dealer-only | High | Same |
| **Carfax / AutoCheck** | Commercial | Useful for trade-in evaluation | Per-report cost; integration trivial |
| **OEM connected-car telematics** | Per-OEM | Variable | Stellantis Uconnect telematics are not third-party-accessible without owner-authorized OAuth flows; not present at v1 |

**Practical conclusion:** The independent specialist's OEM-integration story is constrained. Public sources (NHTSA, vPIC, Transport Canada) are accessible. Anything dealer-gated is not, regardless of API. **Fix class: I for public; honest exclusion for dealer-gated.**

---

## 5. Module-By-Module Fit Matrix

For each named module, this matrix records: native applicability to AlfaCore's JTBDs, what configuration is required, what third-party integration is needed, what custom development is required, and the AlfaCore module that owns the extension.

| Odoo Module | Edition | Native fit | Config required | Integration required | Custom required | AlfaCore module(s) |
|---|---|---|---|---|---|---|
| **Contacts (base/contacts)** | Community | High — partner model is the foundation | Custom fields for PIPEDA, channel pref, tier, household | None | Ownership-role through-model (M2M) | `alfa_core_base` |
| **Project** | Community | High — service task lifecycle | Service-specific stages, kanban tuning | None | Diagnostic-provenance custom fields | `alfa_service` |
| **CRM** | Community | Moderate — lead capture is fine | Pipeline stages tuned to service-only | None | Service-driven opportunity creation | `alfa_core_base` |
| **Sales** | Community | High — quote/order lifecycle | Quote templates, portal theming | None | Diagnostic provenance, line-level approval UX | `alfa_core_portal`, `alfa_parts` |
| **Inventory** | Community | High — stock and reordering | Locations (bay, parts counter, van), reordering rules | None | Vendor preference; aftermarket alternative model | `alfa_parts` |
| **Accounting** | Enterprise (full) | High — billing, recurring | Tax rules, payment terms, analytic accounts | Stripe/payment gateway | None at v1 | (none — native) |
| **Subscriptions** | Enterprise | High — exactly the AlfaCore tier model | Plans, pricing | Stripe | None at v1 | `alfa_core_base` |
| **Website** | Community | Moderate — generic CMS | Industrial Futurism theme, content build | None | Public DTC explainer endpoint | `alfa_core_portal` |
| **eCommerce** | Community | Moderate — for parts retail | Catalog, checkout flow | None | Diagnosis-driven parts cart | `alfa_parts` |
| **Customer Portal (base)** | Community | Moderate — generic | Heavy template override for luxury feel | None | Diagnostic interactive view, vehicle file view | `alfa_core_portal` |
| **Appointments** | Enterprise | High | Resource calendars, customer-pref slot filtering | None | None at v1 | (none — native + config) |
| **Calendar** | Community | High | Tag conventions | Caldav sync (native) | None | (none) |
| **Helpdesk** | Enterprise | High — Pro-tier ticketing | SLAs, teams, escalation rules | None | Diagnostic-escalated tickets auto-create | `alfa_core_diagnosis` |
| **Field Service** | Enterprise | High — mobile service | Work-order templates, van inventory | Stripe Terminal | Inspection extension | `alfa_core_inspection` |
| **Documents** | Enterprise | High — DMS | Workspaces, workflows | None | OCR-driven service-history capture | `alfa_core_base` |
| **Knowledge** | Enterprise | High — internal docs | Article structure, version control | None | None at v1 | (none) |
| **Discuss** | Community | High — messaging | Channel structure | Optional WhatsApp via Enterprise | None | (none) |
| **Sign** | Enterprise | High — e-signatures | Templates for service auth, loaner, invoice | None | None at v1 | (none) |
| **Email Marketing** | Community | High — campaigns | Segments, templates | None | None | (none) |
| **Marketing Automation** | Enterprise | High — drip campaigns | Workflow design | None | Engine-specific welcome content trigger | `alfa_core_diagnosis` |
| **SMS** | Native via IAP | High | Twilio account if IAP not chosen | Twilio | None | (none) |
| **WhatsApp** | Enterprise v17+ | Moderate — Meta-gated | Meta Business verification, template approval | Meta Business API | None | (none) |
| **Studio** | Enterprise | High — no-code customization | Used heavily for partner extensions, view tuning | None | Auxiliary to all X modules | (cross-cutting) |
| **Surveys** | Community | High — NPS, intake | Survey templates | None | None at v1 | (none) |
| **Fleet** | Community | **Low for AlfaCore use case** — internal-fleet-management shape, not customer-vehicle-shape | Repurposable as loaner-vehicle backing store | None | Customer-vehicle model is separate (`alfa_fleet`); loaner uses Odoo Fleet | `alfa_fleet`, `alfa_core_loaner` |
| **Maintenance** | Community | **Low** — manufacturing-asset shape, not vehicle-shape | Not used at v1 | None | n/a | (none) |
| **Quality** | Enterprise | Low–Moderate — MRP-bound | Service quality checks possible with effort | None | Service quality model is cleaner as custom | `alfa_service` |
| **Planning** | Enterprise | High — bay/tech scheduling | Resource setup, shift templates | None | Bay constraints custom | `alfa_service` |
| **Employees** | Community | High — staff records | Skills, certifications custom fields | None | None at v1 | (none) |
| **Timesheets** | Community | High — labor tracking | Project tasks tuned for service | None | Flat-rate variance computed analytic | `alfa_service` |
| **IoT** | Enterprise | Moderate — limited to IoT-Box-compatible devices | Hardware procurement | Per-device | Per-equipment driver | `alfa_core_iot` (P2/P3) |
| **eLearning** | Community | Moderate | Content build | None | None at v1 | (none — defer P2) |
| **Events** | Community | High — community engagement | Event templates | None | None | (none) |
| **Loyalty (in Sales)** | Enterprise | Moderate | Configuration | None | Referral code custom | `alfa_core_base` |

### 5.1 Module footprint summary

- **17 modules** are predominantly **Native** or **Native + Configuration** — Odoo earns its keep
- **6 modules** require **Integration** with third parties (Twilio, Meta WhatsApp, Stripe Terminal, NHTSA, Transport Canada, per-equipment vendors)
- **9 areas** require **Custom development** beyond config — these define the AlfaCore custom-module suite (see §8)
- **3 modules** named in the prompt are essentially **misfits** for AlfaCore's primary JTBDs — Fleet (wrong shape), Maintenance (wrong shape), Quality (MRP-bound). Each is repurposable with effort but not naturally fit.

---

## 6. Prioritized Gap Register

Compiled from §2, §3, §4. Each gap carries: priority, JTBD reference, fix class, effort estimate (engineering weeks, single engineer), and which AlfaCore module owns it.

### 6.1 P0 — Blocks pilot launch

| # | Gap | JTBD ref | Fix class | Effort | Module |
|---|---|---|---|---|---|
| P0.1 | Scanner-to-portal pipeline (scan → triage → recommendation) | 2.3.1 | X | 6 weeks | `alfa_core_scanner`, `alfa_core_diagnosis`, `alfa_core_app_api`, `alfa_core_portal` |
| P0.2 | PIPEDA consent capture + export + erasure | 2.1.3 | X | 1.5 weeks | `alfa_core_base`, `alfa_core_app_api` |
| P0.3 | Scanner pairing UX (< 5 min onboarding) | 2.1.4 | X | 1 week | `alfa_core_app_api`, PWA |
| P0.4 | Customer-vehicle profile + VIN decoding | 2.1.2 | I+X | 1.5 weeks | `alfa_fleet`, NHTSA vPIC integration |
| P0.5 | Channel-pref-aware notification dispatcher | 2.4.1 | C | 0.5 weeks | `alfa_core_base` |
| P0.6 | Diagnostic-driven service-order pre-populate | 2.3.2, 3.1.2 | X | 1 week | `alfa_core_diagnosis` → `alfa_service` |
| P0.7 | Subscription tiers + billing (Stripe + Subscriptions module) | (3.5.2) | N+C | 1 week | `alfa_core_base` |
| P0.8 | Portal theming to luxury-grade (Industrial Futurism) | 2.4.4 | C | 2 weeks | `alfa_core_portal` |
| **P0 subtotal** | | | | **~14.5 weeks** | |

### 6.2 P1 — Required for scale / Pro-tier viability

| # | Gap | JTBD ref | Fix class | Effort | Module |
|---|---|---|---|---|---|
| P1.1 | Digital inspection workflow (photo/video per inspection point) | 2.3.3, 3.2.2 | X | 6 weeks | `alfa_core_inspection` (NEW) |
| P1.2 | Loaner allocation system | 2.3.6 | X | 3 weeks | `alfa_core_loaner` (NEW) |
| P1.3 | Multi-driver household ownership-role model | 2.2.3, 2.6.2 | C+X | 1.5 weeks | `alfa_fleet` extension |
| P1.4 | NHTSA + Transport Canada recall integration | 2.3.8, 3.4.5 | I | 1 week | `alfa_core_diagnosis` |
| P1.5 | Advisor cockpit view | 3.1.1 | X | 2 weeks | `alfa_core_portal` (back-office) |
| P1.6 | Technician tablet view + context | 3.2.1 | X | 2 weeks | `alfa_core_portal` (back-office) |
| P1.7 | Pro-tier technician review queue | (Service Plan §8.1) | X | 1 week | `alfa_core_diagnosis` |
| P1.8 | Per-vehicle preference store (oil, fluids, alignment) | 2.2.1 | X | 1 week | `alfa_fleet` |
| P1.9 | Part-number canonicalization + aftermarket alternative library | 3.3.2, 3.3.3 | X | 1.5 weeks | `alfa_parts` |
| P1.10 | Sign integration for service authorization & loaner agreement | 2.3.5, 2.3.6 | C | 0.5 weeks | (config only) |
| **P1 subtotal** | | | | **~19.5 weeks** | |

### 6.3 P2 — Differentiator / post-pilot

| # | Gap | JTBD ref | Fix class | Effort | Module |
|---|---|---|---|---|---|
| P2.1 | TSB-augmented diagnosis (RAG against `alfa_tsb`) | 2.3.1 follow-on | X | 2 weeks | `alfa_core_diagnosis` |
| P2.2 | Service-quality check workflow (torque-verified) | 3.2.3 | X | 1.5 weeks | `alfa_service` |
| P2.3 | Voice-to-text technician dictation | 3.2.2 | X | 2 weeks | `alfa_core_inspection` |
| P2.4 | Referral program + customer tiering | 2.5.1, 2.5.4 | C+X | 1 week | `alfa_core_base` |
| P2.5 | Recall campaign workflow | 3.4.5 | X | 1 week | `alfa_core_diagnosis` |
| P2.6 | Field Service for mobile/roadside | 3.6.1–3.6.3 | N+C | 2 weeks | (config + light extension) |
| P2.7 | IoT integration for parts scale + bay printer | 3.2.4, 4.4 | N | 1 week | (native) |
| P2.8 | Customer events / community engagement | 2.5.2, 2.5.3 | N+C | 1 week | (native + content) |
| P2.9 | Annual service-summary report (printed luxury artifact) | 2.4.4 | C | 1 week | `alfa_core_portal` QWeb |
| P2.10 | Anxious-customer prep template + Relationship Tape | 2.2.2, 3.1.4 | X | 1 week | `alfa_core_base` |
| **P2 subtotal** | | | | **~13.5 weeks** | |

### 6.4 P3 — Backlog

P3 items include: trade-in workflow, ownership transfer (sale to private party), seasonal storage, ceramic / detail retail, eLearning content, advanced Hunter aligner / Snap-on Modis IoT integrations, multi-location operations, multi-company support, predictive maintenance ML, Stellantis SDMS/eAuthority integration (gated by dealer status), and the AlfaCore-branded scanner reference unit.

### 6.5 Total engineering effort to pilot-ready service

- **P0 only (minimum viable pilot):** ~14.5 weeks for a single engineer; ~7 weeks with two engineers in parallel where independence allows
- **P0 + P1 (Pro-tier viable, 50+ customer scale):** ~34 weeks single-engineer; ~17 weeks two-engineer
- **P0 + P1 + P2 (differentiated luxury service):** ~47 weeks single-engineer; ~24 weeks with two

These estimates assume the v1.0 Plan's base modules (`alfa_fleet`, `alfa_parts`, `alfa_service`, `alfa_tsb`) ship in parallel per the v1.0 phased deployment. If those slip, AlfaCore P0 extends accordingly.

---

## 7. Risks & Operational Failure Points

### 7.1 Customer-expectation mismatch risks

| Risk | Likelihood | Severity | Mitigation |
|---|---|---|---|
| Customer expects native iOS app, gets PWA | Moderate | Moderate | Onboarding sets expectation; PWA "Add to Home Screen" UX must be polished |
| First-scan UX takes > 5 minutes | Moderate | High | Onboarding flow is P0; measure ruthlessly |
| Triage produces a wrong diagnosis | Low–Moderate | Critical | Layer-2 rule engine, not LLM-only; honest confidence display; technician review for Pro tier |
| Customer expects dealer-grade OEM data integration | Moderate | Moderate | Manage expectation honestly — Stellantis is gated |
| Customer perceives notifications as spam | Moderate | High | Single-dispatcher pattern with strict suppression |
| Customer's Bluetooth setup fails (iOS Web Bluetooth quirks) | Moderate | High | Document fallback; native-wrapper Capacitor build as Plan B |
| Customer wants to clear codes themselves | High | Moderate | Honest boundary — not supported; technician-only |

### 7.2 Operational failure points

| Failure mode | Likelihood | Severity | Mitigation |
|---|---|---|---|
| Scanner clone variance — pairing inconsistent across Vgate batches | High | Moderate | Pin to specific firmware version; vendor diversity (OBDLink MX+ for Pro) |
| Parts not ready at bay on appointment morning | Moderate | High | Pre-booking parts-confirmation workflow (P0.6) |
| WhatsApp template message rejected by Meta | Moderate | Moderate | Pre-approve templates in cohorts; fallback to SMS |
| Single-operator dependency on John | High at v1 | High | Pro tier explicitly time-gated; Knowledge module captures procedures |
| PIPEDA incident (data leak, missed export) | Low | Critical | §10.2 controls; insurance |
| Inference cost spike on Claude API | Moderate | Moderate | ZDE-first default; per-customer caps |
| Bay equipment integration scope creep | High | Moderate | Triage to top-3 by usage; defer rest to P3 |
| Loaner damage liability | Moderate | High | Insurance posture documented; in/out condition photos mandatory |
| Customer churn at 6-month mark when novelty fades | Moderate | High | Engagement curriculum tied to subscription milestones |

### 7.3 Technical risks

| Risk | Likelihood | Severity | Mitigation |
|---|---|---|---|
| Web Bluetooth API breaks on iOS update | Low | High | Capacitor wrapper as fallback; native app contingency planned |
| OBD-II protocol coverage gaps on older Italian platforms (159, Brera) | High | Low–Moderate | KWP2000 + ISO 9141 support in Phase 2; honest exclusion otherwise |
| QNAP host capacity insufficient at scale | Moderate | High | Substrate-promotion decision (Service Plan §13.8) — move to cloud VM at threshold |
| Ollama inference latency spikes during traffic bursts | Moderate | Moderate | Async queue + status-poll pattern; never block customer on inference |
| Odoo version upgrade (v19→v20) breaks custom modules | High (annual) | Moderate | Test in staging; upgrade is 3-month effort each major version |

---

## 8. Recommended Custom Module Map (Beyond v1.0 + Service Plan)

Beyond the modules already named in the v1.0 Plan and the Service Plan, this audit surfaces the following new modules:

| Module | Purpose | Gap reference | Priority |
|---|---|---|---|
| **`alfa_core_inspection`** | Digital inspection workflow — points, photos, video, severity, customer publishing | P1.1 (highest single investment) | P1 |
| **`alfa_core_loaner`** | Loaner-vehicle allocation, condition capture, agreement, return | P1.2 | P1 |
| **`alfa_core_campaign`** | Recall + voluntary-campaign customer targeting | P2.5 | P2 |
| **`alfa_core_iot`** | Bay-equipment data capture (selective; not all equipment) | 4.4 | P2/P3 |
| **`alfa_core_tradein`** | Vehicle trade-in workflow | 2.3.7 | P3 |
| **`alfa_core_transfer`** | Ownership transfer between customers (private sale) | 2.6.3 | P2 |

**Total AlfaCore custom-module count at full build-out:** 11 modules (5 from Service Plan + 6 from this gap analysis), on top of the 6 modules from v1.0 Plan. Total platform: ~17 custom modules. Comparable to a mature Odoo industry vertical implementation.

---

## 9. Honest Exclusions From This Audit

Areas the source prompt named that this v1.0 audit deliberately defers or excludes, with the rationale:

- **OEM telematics (Uconnect) integration** — Stellantis does not expose third-party OAuth at the depth required; revisit if/when API surface emerges
- **Stellantis eAuthority warranty submission** — gated by authorized-dealer status; not in independent-specialist scope
- **Stellantis SDMS dealer feeds** — same gate
- **Insurance claim primary handling** — out of scope; surface documentation only
- **Body shop / collision repair** — different vertical; defer
- **Ceramic / detail retail upsells** — pass-through margin; doesn't earn module scope at v1
- **Tire / seasonal wheel storage** — operationally simple, software-light; defer P3
- **Multi-tenant white-label DMS-as-a-service** — different product entirely; separate audit required if pursued
- **Predictive maintenance ML beyond rule-based triage** — data volume insufficient at v1; revisit at 200+ customers and 24+ months of scan history
- **Native iOS/Android applications** — PWA-first; Capacitor wrap as fallback only
- **Voice assistant integration (Siri, Google Assistant, Alexa for Auto)** — long tail; defer

---

## 10. Decisions This Audit Requires Before Build

These are the calls that determine whether the gap register above is the right gap register. They need answers before P0 work begins.

1. **Dealership-mode vs. independent-mode scope.** The audit covers both. If AlfaCore is *only* John's independent operation at v1, the entire 3.5 GM/ownership section and parts of 3.4 simplify. If AlfaCore is positioned to also sell to dealerships as a complementary DMS-adjacent tool, the audit's full scope applies. Material to all phasing.
2. **Inspection module: build at v1 or v1.1?** The single biggest call. Inspection is P1 here, not P0 — meaning pilot can ship without it. But the perceived luxury delta with vs. without is enormous. If pilot customers are paying $59/mo Pro and don't get inspection-with-photos until v1.1, the tier proposition is weaker. Pulling inspection forward to P0 adds ~6 weeks to pilot timeline.
3. **Loaner program: at launch or after?** Loaner allocation is P1. Pilot customers will not need it for low-mileage scans, but Pro-tier customers who book service through AlfaCore expect it. If we ship Pro without loaner, the tier is incomplete.
4. **WhatsApp at launch?** Meta Business approval is 2–4 weeks. If WhatsApp is a P0 channel, start the verification immediately, parallel to engineering.
5. **Telephony integration vendor?** Twilio is the obvious default but is US-priced; Canadian alternatives (Voxbone via Bandwidth, OnSIP) may be cheaper for the Toronto-centric pilot.
6. **Pilot cohort size.** Numbers in §6.5 assume 5–10 customers in pilot. If the pilot is 50+, the P1 items become P0 because the operation cannot scale without them.
7. **The "AlfaCore" name.** Re-raised from Service Plan §13.7. If the audit's full Italian-platform scope holds (Alfa + Fiat + Maserati), the brand must scale beyond Alfa or live with the dissonance.

---

**End of analysis v1.0.**

*This audit complements `Alfa-Odoo-Server-Plan-v1.0.md` and `AlfaCore-Service-Plan-v1.0.md`. The three documents together form the architecture corpus for AlfaCore. Next review: after pilot cohort size and inspection-priority decisions land.*
