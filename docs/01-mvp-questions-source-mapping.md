# MVP Questions - Source Mapping Document

**Version:** 1.0  
**Created:** 2026-05-14  
**Purpose:** Map each of the 20 MVP questions to required official legal sources for ingestion

---

## Source Legend

| Source | Type | Access Method | Priority |
|--------|------|---------------|----------|
| **eCFR Title 8** | Federal Regulations | Bulk XML / API | P0 |
| **USCIS Policy Manual** | Agency Policy | Web scraping / HTML | P0 |
| **INA (U.S. Code Title 8)** | Statutes | GovInfo API / Bulk | P0 |
| **BIA Decisions** | Case Law | DOJ EOIR | P1 |
| **Federal Register** | Rule Updates | API (no key) | P2 |
| **USCIS Forms/Instructions** | Filing Guidance | Web scraping | P1 |

---

## Question Bank with Source Mapping

### Q1: Can I work while my asylum case is pending?
**Topic:** asylum | **Subtopic:** employment_authorization | **Risk:** medium

**Primary Sources:**
- 8 CFR § 208.7 - Employment authorization for asylum applicants
- 8 CFR § 274a.12 - Employment authorization categories
- USCIS Policy Manual Vol. 5, Part B, Chapter 4 - Asylum-Based Employment Authorization

**Secondary Sources:**
- USCIS Form I-765 Instructions
- INA § 208 - Asylum provisions

**Key Citations to Ingest:**
- 8 CFR 208.7(a) - 150-day waiting period
- 8 CFR 208.7(b) - Delay attribution rules
- USCIS PM Vol.5 Pt.B Ch.4 - Adjudication guidance

---

### Q2: What happens if I overstay my visa?
**Topic:** visa_overstay | **Subtopic:** unlawful_presence | **Risk:** high

**Primary Sources:**
- INA § 212(a)(9)(B) - Unlawful presence bars (3/10 year bars)
- INA § 212(a)(9)(C) - Permanent bar for repeat violations
- 8 CFR § 214.2 - Visa status requirements

**Secondary Sources:**
- USCIS Policy Manual Vol. 8, Part B, Chapter 3 - Unlawful Presence
- BIA Matter of Z-P- (precedent on overstay)

**Key Citations to Ingest:**
- INA 212(a)(9)(B)(i) - 3-year bar (>180 days)
- INA 212(a)(9)(B)(i)(II) - 10-year bar (>1 year)
- USCIS PM Vol.8 Pt.B Ch.3 - Calculation methods

---

### Q3: Can I apply for asylum after one year?
**Topic:** asylum | **Subtopic:** filing_deadline | **Risk:** high

**Primary Sources:**
- INA § 208(a)(2)(B) - One-year filing deadline
- 8 CFR § 208.4(a)(2) - Asylum application deadline
- 8 CFR § 208.4(a)(4) - Changed/extraordinary circumstances exceptions

**Secondary Sources:**
- USCIS Policy Manual Vol. 5, Part B, Chapter 2 - Filing Deadline
- Federal Register: Asylum Processing Rule (2022)

**Key Citations to Ingest:**
- INA 208(a)(2)(B) - Statutory one-year rule
- 8 CFR 208.4(a)(4)(i) - Changed circumstances
- 8 CFR 208.4(a)(4)(ii) - Extraordinary circumstances
- USCIS PM Vol.5 Pt.B Ch.2 - Exception adjudication

---

### Q4: What is adjustment of status?
**Topic:** adjustment_of_status | **Subtopic:** definitions | **Risk:** low

**Primary Sources:**
- INA § 245 - Adjustment of status to permanent residence
- 8 CFR § 245.1 - Definitions and eligibility
- 8 CFR § 245.2 - Application procedures

**Secondary Sources:**
- USCIS Policy Manual Vol. 7, Part A - Adjustment Overview
- USCIS Form I-485 Instructions

**Key Citations to Ingest:**
- INA 245(a) - General eligibility
- INA 245(c) - Bars to adjustment
- 8 CFR 245.1(d) - Inspection/admission requirements

---

### Q5: Can I apply for citizenship after getting a green card?
**Topic:** naturalization | **Subtopic:** eligibility | **Risk:** low

**Primary Sources:**
- INA § 316 - Requirements for naturalization
- INA § 319 - Special provisions (marriage-based)
- 8 CFR § 316.1 - Eligibility requirements

**Secondary Sources:**
- USCIS Policy Manual Vol. 12, Part D - Continuous Residence
- USCIS Form N-400 Instructions

**Key Citations to Ingest:**
- INA 316(a) - 5-year permanent residence requirement
- INA 316(b) - Continuous residence
- INA 316(c) - Physical presence (30 months of 5 years)
- INA 319(a) - 3-year rule for spouses of citizens

---

### Q6: What documents do I need for naturalization?
**Topic:** naturalization | **Subtopic:** documentation | **Risk:** low

**Primary Sources:**
- 8 CFR § 316.2 - Filing requirements
- USCIS Form N-400 Instructions (current version)
- INA § 335 - Investigation of applicants

**Secondary Sources:**
- USCIS Policy Manual Vol. 12, Part E - Examination
- USCIS M-476 Naturalization Study Guide

**Key Citations to Ingest:**
- 8 CFR 316.2(a) - Required documents list
- N-400 Instructions - Document checklist
- INA 335(a) - Examination authority

---

### Q7: What is unlawful presence?
**Topic:** unlawful_presence | **Subtopic:** definitions | **Risk:** medium

**Primary Sources:**
- INA § 212(a)(9)(B) - Unlawful presence grounds
- 8 CFR § 214.1 - Status vs. admission
- USCIS Policy Manual Vol. 8, Part B, Chapter 2 - Definitions

**Secondary Sources:**
- BIA Matter of Arrabally and Yerrabelly (departure exceptions)
- Federal Register: Unlawful Presence Memo (2018)

**Key Citations to Ingest:**
- INA 212(a)(9)(B)(ii) - Definition of unlawful presence
- 8 CFR 214.1(a)(4) - Status violation
- USCIS PM Vol.8 Pt.B Ch.2 - Accrual start dates

---

### Q8: What happens if I receive a Notice to Appear?
**Topic:** removal_proceedings | **Subtopic:** nta | **Risk:** high

**Primary Sources:**
- INA § 239 - Notice to Appear requirements
- 8 CFR § 239.1 - Form and service of NTA
- 8 CFR § 1003.15 - EOIR filing requirements

**Secondary Sources:**
- USCIS Policy Manual Vol. 8, Part E - NTA Issuance
- DOJ EOIR Practice Manual
- BIA Matter of Camarillo (NTA deficiencies)

**Key Citations to Ingest:**
- INA 239(a) - NTA content requirements
- 8 CFR 239.1(a) - Form specifications
- 8 CFR 1003.15 - Filing with immigration court
- USCIS PM Vol.8 Pt.E - When USCIS issues NTA

---

### Q9: Can I travel while my green card application is pending?
**Topic:** adjustment_of_status | **Subtopic:** travel | **Risk:** high

**Primary Sources:**
- 8 CFR § 245.2(a)(4)(ii) - Abandonment of application
- INA § 212(a)(7)(A) - Travel document requirements
- 8 CFR § 223.1 - Advance parole definitions

**Secondary Sources:**
- USCIS Policy Manual Vol. 7, Part A, Chapter 5 - Travel
- USCIS Form I-131 Instructions
- USCIS Form I-485 Instructions

**Key Citations to Ingest:**
- 8 CFR 245.2(a)(4)(ii) - Abandonment upon departure
- 8 CFR 223.1(b) - Advance parole effect
- USCIS PM Vol.7 Pt.A Ch.5 - Travel risks and exceptions

---

### Q10: What is advance parole?
**Topic:** advance_parole | **Subtopic:** definitions | **Risk:** medium

**Primary Sources:**
- 8 CFR § 212.5 - Parole of aliens into the U.S.
- 8 CFR § 223.1 - Advance parole definitions
- INA § 212(d)(5) - Parole authority

**Secondary Sources:**
- USCIS Policy Manual Vol. 7, Part A, Chapter 5
- USCIS Form I-131 Instructions
- Federal Register: Advance Parole Guidance (2025)

**Key Citations to Ingest:**
- INA 212(d)(5)(A) - Parole authority
- 8 CFR 212.5(f) - Advance parole process
- 8 CFR 223.1(a) - Definition

---

### Q11: What is a work permit?
**Topic:** employment_authorization | **Subtopic:** definitions | **Risk:** low

**Primary Sources:**
- 8 CFR § 274a.12 - Employment authorization categories
- 8 CFR § 274a.13 - Application procedures
- INA § 274A - Employment eligibility verification

**Secondary Sources:**
- USCIS Policy Manual Vol. 5, Part A - Employment Authorization
- USCIS Form I-765 Instructions

**Key Citations to Ingest:**
- 8 CFR 274a.12(a) - Categories list
- 8 CFR 274a.12(c) - Specific eligibility categories
- 8 CFR 274a.13 - Filing requirements

---

### Q12: Can an F-1 student work?
**Topic:** student_visa | **Subtopic:** employment | **Risk:** medium

**Primary Sources:**
- 8 CFR § 214.2(f)(10) - F-1 employment authorization
- 8 CFR § 214.2(f)(11) - Practical training (OPT/CPT)
- INA § 214(l) - Student visa requirements

**Secondary Sources:**
- USCIS Policy Manual Vol. 2, Part F, Chapter 3 - F-1 Students
- USCIS Form I-765 Instructions (c)(3) category
- SEVP Policy Guidance

**Key Citations to Ingest:**
- 8 CFR 214.2(f)(10)(i) - On-campus employment
- 8 CFR 214.2(f)(10)(ii) - Off-campus economic hardship
- 8 CFR 214.2(f)(11) - OPT/CPT requirements

---

### Q13: What happens if my visa expires?
**Topic:** visa_expiration | **Subtopic:** status_violation | **Risk:** high

**Primary Sources:**
- INA § 212(a)(9)(B) - Unlawful presence consequences
- 8 CFR § 214.1(c) - Duration of status
- 8 CFR § 214.2 - Visa-specific requirements

**Secondary Sources:**
- USCIS Policy Manual Vol. 8, Part B - Unlawful Presence
- DOS Foreign Affairs Manual (visa vs. status)

**Key Citations to Ingest:**
- 8 CFR 214.1(c)(4) - Status expiration vs. visa expiration
- INA 212(a)(9)(B) - Re-entry bars
- USCIS PM Vol.8 Pt.B Ch.3 - Accrual rules

---

### Q14: What is deportability?
**Topic:** deportability | **Subtopic:** definitions | **Risk:** high

**Primary Sources:**
- INA § 237 - Grounds of deportability
- 8 CFR § 237.1 - Deportability definitions
- 8 CFR § 1240.8 - Burden of proof in proceedings

**Secondary Sources:**
- USCIS Policy Manual Vol. 8, Part G - Deportability
- BIA precedent decisions on deportability grounds

**Key Citations to Ingest:**
- INA 237(a)(1) - Inadmissible at entry
- INA 237(a)(2) - Criminal grounds
- INA 237(a)(3) - Document fraud
- INA 237(a)(4) - Security grounds

---

### Q15: What is inadmissibility?
**Topic:** inadmissibility | **Subtopic:** definitions | **Risk:** high

**Primary Sources:**
- INA § 212 - Grounds of inadmissibility
- 8 CFR § 212.1 - Inadmissibility definitions
- 8 CFR § 212.7 - Waivers of inadmissibility

**Secondary Sources:**
- USCIS Policy Manual Vol. 8, Part F - Inadmissibility
- DOS Foreign Affairs Manual 9 FAM 302

**Key Citations to Ingest:**
- INA 212(a)(1) - Health grounds
- INA 212(a)(2) - Criminal grounds
- INA 212(a)(6) - Documentation requirements
- INA 212(a)(9) - Prior removal/unlawful presence

---

### Q16: Can I sponsor my spouse?
**Topic:** family_sponsorship | **Subtopic:** marriage | **Risk:** medium

**Primary Sources:**
- INA § 204 - Petition process
- INA § 245 - Adjustment for immediate relatives
- 8 CFR § 204.1 - Petition requirements
- 8 CFR § 204.2 - Marriage-based petitions

**Secondary Sources:**
- USCIS Policy Manual Vol. 10, Part A - Family-Based
- USCIS Form I-130 Instructions
- USCIS Policy Manual Vol. 12, Part G - Conditional Residence

**Key Citations to Ingest:**
- INA 204(a)(1)(A) - Citizen petitioning spouse
- INA 204(a)(1)(B) - LPR petitioning spouse
- 8 CFR 204.2(a)(1)(i) - Marriage documentation
- INA 245(a) - Adjustment eligibility

---

### Q17: What is public charge?
**Topic:** public_charge | **Subtopic:** inadmissibility | **Risk:** high

**Primary Sources:**
- INA § 212(a)(4) - Public charge ground
- 8 CFR § 212.20 - Public charge definitions
- 8 CFR § 212.21 - Public benefits definitions

**Secondary Sources:**
- USCIS Policy Manual Vol. 8, Part C - Public Charge
- Federal Register: Public Charge Final Rule (2022)
- DOS 9 FAM 302.8

**Key Citations to Ingest:**
- INA 212(a)(4)(A) - Public charge inadmissibility
- 8 CFR 212.20 - Totality of circumstances
- 8 CFR 212.21(b) - Defined public benefits
- USCIS PM Vol.8 Pt.C - Adjudication framework

---

### Q18: What should I do if ICE comes to my door?
**Topic:** ice_encounter | **Subtopic:** rights | **Risk:** critical

**Primary Sources:**
- 8 CFR § 287.8 - Officer authority and limitations
- 8 CFR § 287.10 - Warrant requirements
- INA § 287 - Powers of immigration officers

**Secondary Sources:**
- DOJ EOIR Know Your Rights materials
- DHS/ICE Enforcement Guidelines
- ACLU Immigrant Rights (for plain-language guidance)

**Key Citations to Ingest:**
- 8 CFR 287.8(a) - Officer authority
- 8 CFR 287.10(b) - Warrant types (judicial vs. administrative)
- INA 287(a)(3) - Warrantless arrest authority
- ICE/ERO Operational Guidance (2021)

**Note:** This answer requires careful balance of legal citations + practical safety guidance. Include strong attorney referral.

---

### Q19: What is TPS?
**Topic:** tps | **Subtopic:** definitions | **Risk:** low

**Primary Sources:**
- INA § 244 - Temporary Protected Status
- 8 CFR § 244.1 - TPS definitions
- 8 CFR § 244.2 - Eligibility requirements

**Secondary Sources:**
- USCIS Policy Manual Vol. 6, Part L - TPS
- Federal Register: TPS Country Designations
- USCIS Form I-821 Instructions

**Key Citations to Ingest:**
- INA 244(a)(1) - TPS authority
- INA 244(c)(1) - Continuous residence requirement
- 8 CFR 244.2 - Filing requirements
- 8 CFR 244.13 - Employment authorization

---

### Q20: How do I check my USCIS case status?
**Topic:** case_status | **Subtopic:** procedures | **Risk:** low

**Primary Sources:**
- 8 CFR § 103.2(b) - USCIS decisions and notifications
- USCIS Case Status Online (official tool reference)
- INA § 292 - Right to counsel (for status inquiries)

**Secondary Sources:**
- USCIS.gov Case Status page
- USCIS Form Receipt Notice Instructions
- USCIS e-Request (Case Inquiry) procedures

**Key Citations to Ingest:**
- 8 CFR 103.2(b)(1) - Decision notices
- 8 CFR 103.2(b)(10) - Case inquiry procedures
- USCIS.gov official case status URL and process

---

## Ingestion Priority Matrix

### Phase 2 (First Source - eCFR Title 8)
**Sections to ingest first:**
- 8 CFR § 208.7 - Asylum employment authorization
- 8 CFR § 208.4 - Asylum filing deadline
- 8 CFR § 245.1-245.2 - Adjustment of status
- 8 CFR § 274a.12-274a.13 - Employment authorization
- 8 CFR § 214.2(f) - F-1 student provisions
- 8 CFR § 212.20-212.21 - Public charge
- 8 CFR § 223.1 - Advance parole
- 8 CFR § 239.1 - Notice to Appear
- 8 CFR § 287.8-287.10 - ICE officer authority

### Phase 4 (USCIS Policy Manual)
**Volumes/Pages to prioritize:**
- Vol. 5, Part B - Asylum (Ch.2, Ch.4)
- Vol. 7, Part A - Adjustment (Ch.5 - Travel)
- Vol. 8, Part B - Unlawful Presence (Ch.2, Ch.3)
- Vol. 8, Part C - Public Charge
- Vol. 8, Part E - NTA Issuance
- Vol. 10, Part A - Family-Based
- Vol. 12, Part D - Naturalization (Continuous Residence)

### Phase 5 (INA / U.S. Code Title 8)
**Sections to prioritize:**
- INA § 101 - Definitions
- INA § 208 - Asylum
- INA § 212 - Inadmissibility (all subsections)
- INA § 237 - Deportability
- INA § 239 - Notice to Appear
- INA § 244 - TPS
- INA § 245 - Adjustment of status
- INA § 274A - Employment verification
- INA § 316 - Naturalization requirements
- INA § 319 - Naturalization (marriage-based)

---

## Risk Level Classification

| Risk Level | Questions | Handling |
|------------|-----------|----------|
| **Critical** | Q18 (ICE encounter) | Mandatory attorney referral, safety-first language |
| **High** | Q2, Q3, Q8, Q9, Q13, Q14, Q15, Q17 | Strong attorney referral, explicit warnings |
| **Medium** | Q1, Q7, Q10, Q12, Q16 | Standard disclaimer, mention consultation |
| **Low** | Q4, Q5, Q6, Q11, Q19, Q20 | Basic disclaimer, informational only |

---

## Next Steps

1. **Database Schema** - Create tables to support source tracking, chunking, and versioning
2. **eCFR Scraper** - Build parser for Title 8 CFR sections listed above
3. **USCIS Scraper** - Build HTML parser for Policy Manual volumes
4. **INA Fetcher** - Build GovInfo API client for U.S. Code Title 8
5. **Chunking Strategy** - Define chunk size (500-1000 tokens), overlap (50-100 tokens)
6. **Embedding Model** - Select model (nomic-embed-text for local, text-embedding-3-small for API)
7. **Retrieval Testing** - Test each question retrieves correct sections

---

## Document Metadata

- **Total Questions:** 20
- **Primary Sources Required:** 5 (eCFR, USCIS PM, INA, BIA, Federal Register)
- **eCFR Sections:** ~30 sections across 10 topic areas
- **USCIS PM Chapters:** ~15 chapters across 7 volumes
- **INA Sections:** ~10 core sections
- **Risk Distribution:** 1 Critical, 8 High, 5 Medium, 6 Low
