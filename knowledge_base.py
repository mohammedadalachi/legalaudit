"""
38 legal rules across employment and tenancy contracts.

employment (20 rules): employment act 1955, epf act 1991, socso act 1969,
  minimum wages order 2022, hrdf act 2001, contracts act 1950
tenancy (18 rules): contracts act 1950, stamp act 1949, national land code 1965

each rule dict has: id, doc_type, name, statute, description, keywords,
check_type ("presence" = flag if missing, "risk_keyword" = flag if present),
risk, priority (for conflict resolution), recommendation
"""

RULES = [

    # ══════════════════════════════════════════════════════════════════
    # EMPLOYMENT CONTRACT RULES (20)
    # ══════════════════════════════════════════════════════════════════

    {
        "id": "E001",
        "doc_type": "employment",
        "name": "Notice Period for Termination",
        "statute": "Employment Act 1955, Section 12",
        "description": (
            "The contract must specify a notice period for termination. "
            "Minimum: 4 weeks (< 2 years service), 6 weeks (2–5 years), "
            "8 weeks (> 5 years)."
        ),
        "keywords": ["notice period", "notice of termination", "weeks notice",
                     "days notice", "month notice", "termination notice",
                     "written notice", "weeks' notice", "month's notice",
                     "days' notice", "notice in writing"],
        "check_type": "presence",
        "risk": "HIGH",
        "priority": 10,
        "recommendation": (
            "Add a notice period clause. Section 12 requires minimum 4 weeks "
            "(< 2 years), 6 weeks (2–5 years), or 8 weeks (> 5 years) service."
        )
    },
    {
        "id": "E002",
        "doc_type": "employment",
        "name": "Annual Leave Entitlement",
        "statute": "Employment Act 1955, Section 60E",
        "description": (
            "Employees must receive paid annual leave: 8 days (< 2 years), "
            "12 days (2–5 years), 16 days (> 5 years)."
        ),
        "keywords": ["annual leave", "yearly leave", "vacation leave",
                     "leave entitlement", "days leave", "days of leave",
                     "paid leave", "days' leave", "leave per year"],
        "check_type": "presence",
        "risk": "HIGH",
        "priority": 10,
        "recommendation": (
            "Include annual leave. Section 60E requires minimum 8 days "
            "(< 2 years), 12 days (2–5 years), 16 days (> 5 years)."
        )
    },
    {
        "id": "E003",
        "doc_type": "employment",
        "name": "Sick Leave Entitlement",
        "statute": "Employment Act 1955, Section 60F",
        "description": (
            "Employees are entitled to paid sick leave: 14 days (< 2 years), "
            "18 days (2–5 years), 22 days (> 5 years), plus 60 days "
            "if hospitalisation is required."
        ),
        "keywords": ["sick leave", "medical leave", "hospitalisation leave",
                     "medical certificate", "illness leave", "mc leave",
                     "sick day", "medical benefit", "paid sick",
                     "certified sick"],
        "check_type": "presence",
        "risk": "HIGH",
        "priority": 10,
        "recommendation": (
            "Include sick leave. Section 60F requires 14 days (< 2 years), "
            "18 days (2–5 years), 22 days (> 5 years) plus 60 days "
            "hospitalisation leave."
        )
    },
    {
        "id": "E004",
        "doc_type": "employment",
        "name": "Maternity Leave",
        "statute": "Employment Act 1955, Section 37 (amended 2022)",
        "description": (
            "Female employees are entitled to 98 consecutive days of paid "
            "maternity leave under the 2022 amendment, up from 60 days."
        ),
        "keywords": ["maternity", "maternity leave", "confinement",
                     "pregnancy leave", "paternity", "parental leave",
                     "maternity benefit", "post natal", "child birth"],
        "check_type": "presence",
        "risk": "MEDIUM",
        "priority": 8,
        "recommendation": (
            "Include maternity leave. Section 37 (2022 amendment) entitles "
            "female employees to 98 consecutive days of paid maternity leave."
        )
    },
    {
        "id": "E005",
        "doc_type": "employment",
        "name": "Working Hours Limit",
        "statute": "Employment Act 1955, Section 60A (amended 2023)",
        "description": (
            "Working hours must not exceed 8 hours per day or 45 hours per week "
            "(amended January 2023). No more than 5 consecutive hours without "
            "a rest break."
        ),
        "keywords": ["working hours", "hours of work", "work hours",
                     "hours per day", "hours per week", "working time", "shift",
                     "normal working", "business hours", "eight hours"],
        "check_type": "presence",
        "risk": "MEDIUM",
        "priority": 8,
        "recommendation": (
            "Specify working hours. Section 60A (amended 2023) limits work to "
            "8 hours/day and 45 hours/week, with no more than 5 consecutive "
            "hours without a rest break."
        )
    },
    {
        "id": "E006",
        "doc_type": "employment",
        "name": "Overtime Compensation",
        "statute": "Employment Act 1955, Section 60A(3)",
        "description": (
            "Overtime must be paid at minimum 1.5x the hourly rate for work "
            "beyond normal hours on a regular working day."
        ),
        "keywords": ["overtime", "over time", "ot pay", "overtime rate",
                     "overtime compensation", "extra hours", "overtime pay",
                     "extended hours", "beyond normal hours"],
        "check_type": "presence",
        "risk": "HIGH",
        "priority": 10,
        "recommendation": (
            "Include an overtime clause. Section 60A(3) requires overtime pay "
            "at minimum 1.5x the normal hourly rate on a working day."
        )
    },
    {
        "id": "E007",
        "doc_type": "employment",
        "name": "Rest Day Entitlement",
        "statute": "Employment Act 1955, Section 59",
        "description": (
            "Every employee is entitled to one rest day per week. Work on a "
            "rest day must be compensated at 2x the hourly rate."
        ),
        "keywords": ["rest day", "day off", "weekly rest", "off day",
                     "rest period", "non-working day", "days off", "off days"],
        "check_type": "presence",
        "risk": "MEDIUM",
        "priority": 8,
        "recommendation": (
            "Include a rest day clause. Section 59 entitles employees to at "
            "least one rest day per week, with rest-day work paid at 2x hourly rate."
        )
    },
    {
        "id": "E008",
        "doc_type": "employment",
        "name": "Public Holidays Entitlement",
        "statute": "Employment Act 1955, Section 60D",
        "description": (
            "Employees are entitled to at least 11 gazetted Malaysian public "
            "holidays per year including Hari Merdeka and Malaysia Day."
        ),
        "keywords": ["public holiday", "gazetted holiday", "national holiday",
                     "statutory holiday", "holiday entitlement",
                     "public holidays", "cuti umum", "federal holiday"],
        "check_type": "presence",
        "risk": "MEDIUM",
        "priority": 8,
        "recommendation": (
            "Include a public holidays clause. Section 60D requires minimum "
            "11 gazetted public holidays including Hari Merdeka and Malaysia Day."
        )
    },
    {
        "id": "E009",
        "doc_type": "employment",
        "name": "Salary Payment Timing",
        "statute": "Employment Act 1955, Section 18",
        "description": (
            "Wages must be paid no later than the 7th day after the last day "
            "of the wage period. Late payment is an offence under the Act."
        ),
        "keywords": ["salary", "wages", "payment date", "pay date", "payroll",
                     "salary payment", "wage period", "remuneration",
                     "monthly salary"],
        "check_type": "presence",
        "risk": "MEDIUM",
        "priority": 8,
        "recommendation": (
            "Specify salary payment timing. Section 18 requires wages to be "
            "paid within 7 days after the end of each wage period."
        )
    },
    {
        "id": "E010",
        "doc_type": "employment",
        "name": "Unlawful Salary Deductions",
        "statute": "Employment Act 1955, Section 24",
        "description": (
            "Total deductions from wages must not exceed 50% of wages in any "
            "one wage period, except for deductions authorised by court order."
        ),
        "keywords": ["deduction", "salary deduction", "wage deduction",
                     "withhold", "clawback", "recovery of loan", "advance"],
        "check_type": "risk_keyword",
        "risk": "MEDIUM",
        "priority": 8,
        "recommendation": (
            "Review deduction clauses. Section 24 caps total deductions at "
            "50% of wages per period. List all authorised deduction types explicitly."
        )
    },
    {
        "id": "E011",
        "doc_type": "employment",
        "name": "Probation Period",
        "statute": "Employment Act 1955, General Principles",
        "description": (
            "Probation periods beyond 6 months may be challenged as "
            "circumventing statutory employment protections. Employees on "
            "probation retain all statutory rights."
        ),
        "keywords": ["probation", "probationary period", "probationary",
                     "confirmation", "confirmed employee"],
        "check_type": "presence",
        "risk": "LOW",
        "priority": 5,
        "recommendation": (
            "Ensure probation is reasonable (3–6 months). Employees on "
            "probation retain full statutory rights under the Employment Act 1955."
        )
    },
    {
        "id": "E012",
        "doc_type": "employment",
        "name": "Non-Compete / Restraint of Trade",
        "statute": "Contracts Act 1950, Section 28",
        "description": (
            "Any agreement restraining a person from a lawful profession, "
            "trade, or business is void under Section 28, unless reasonable "
            "in scope, geographic area, and duration."
        ),
        "keywords": ["non-compete", "non compete", "restraint of trade",
                     "non-solicitation", "competing business",
                     "restrictive covenant", "competitor"],
        "check_type": "risk_keyword",
        "risk": "HIGH",
        "priority": 10,
        "recommendation": (
            "Non-compete clauses are void under Section 28 of the Contracts "
            "Act 1950 unless narrowly scoped. Limit to a reasonable geographic "
            "area, duration (typically ≤ 12 months), and specific activity."
        )
    },
    {
        "id": "E013",
        "doc_type": "employment",
        "name": "Sexual Harassment Policy",
        "statute": "Employment Act 1955, Section 81B",
        "description": (
            "Employers are legally required to address sexual harassment "
            "complaints. A reference to the company's policy is strongly "
            "recommended to demonstrate compliance."
        ),
        "keywords": ["sexual harassment", "harassment policy", "code of conduct",
                     "workplace harassment", "anti-harassment",
                     "workplace conduct", "workplace policy"],
        "check_type": "presence",
        "risk": "MEDIUM",
        "priority": 7,
        "recommendation": (
            "Reference or attach a sexual harassment policy. Section 81B "
            "obliges employers to inquire into all sexual harassment complaints."
        )
    },
    {
        "id": "E014",
        "doc_type": "employment",
        "name": "Governing Law and Jurisdiction",
        "statute": "Contracts Act 1950, General Principles",
        "description": (
            "The contract should specify that Malaysian law governs the "
            "agreement and identify the appropriate jurisdiction for disputes."
        ),
        "keywords": ["governing law", "jurisdiction", "laws of malaysia",
                     "malaysian law", "applicable law", "dispute resolution",
                     "arbitration"],
        "check_type": "presence",
        "risk": "LOW",
        "priority": 5,
        "recommendation": (
            "Add a governing law clause specifying Malaysian law and "
            "jurisdiction to ensure enforceability under the Contracts Act 1950."
        )
    },
    {
        "id": "E015",
        "doc_type": "employment",
        "name": "Confidentiality / NDA",
        "statute": "Contracts Act 1950, General Principles",
        "description": (
            "Confidentiality obligations must be reasonable in scope and "
            "duration. Unlimited post-employment confidentiality clauses "
            "may be unenforceable."
        ),
        "keywords": ["confidential", "confidentiality", "nda",
                     "non-disclosure", "trade secret", "proprietary information",
                     "sensitive information"],
        "check_type": "risk_keyword",
        "risk": "LOW",
        "priority": 5,
        "recommendation": (
            "Ensure the confidentiality clause specifies what information is "
            "covered, the duration of the obligation, and is limited to "
            "genuinely sensitive business information."
        )
    },

    # STATUTORY CONTRIBUTIONS AND COMPLIANCE
    {
        "id": "E016",
        "doc_type": "employment",
        "name": "EPF (KWSP) Contributions",
        "statute": "Employees Provident Fund Act 1991, Section 43",
        "description": (
            "Employers are legally required to contribute to the EPF "
            "(KWSP) for all eligible employees. The current employer "
            "contribution rate is 13% (wages ≤ RM 5,000) or 12% "
            "(wages > RM 5,000). Employee contribution is 11%."
        ),
        "keywords": ["epf", "kwsp", "employees provident fund",
                     "provident fund", "epf contribution",
                     "kwsp contribution", "retirement fund",
                     "mandatory contribution", "kumpulan wang"],
        "check_type": "presence",
        "risk": "HIGH",
        "priority": 10,
        "recommendation": (
            "Include an EPF clause. Section 43 of the EPF Act 1991 mandates "
            "employer contributions at 13% (salary ≤ RM 5,000) or 12% "
            "(salary > RM 5,000). Failure to contribute is a criminal offence."
        )
    },
    {
        "id": "E017",
        "doc_type": "employment",
        "name": "SOCSO (PERKESO) Coverage",
        "statute": "Employees' Social Security Act 1969, Section 5",
        "description": (
            "Employers must register eligible employees with SOCSO (PERKESO) "
            "and contribute to the Employment Injury Scheme and Invalidity "
            "Scheme. Applicable to employees earning RM 5,000 and below "
            "per month."
        ),
        "keywords": ["socso", "perkeso", "social security", "eis",
                     "employment insurance", "invalidity scheme",
                     "employment injury", "socso contribution",
                     "social security contribution", "perkeso contribution"],
        "check_type": "presence",
        "risk": "HIGH",
        "priority": 10,
        "recommendation": (
            "Include a SOCSO clause. Section 5 of the Employees' Social "
            "Security Act 1969 requires employers to register and contribute "
            "for all eligible employees. Non-compliance carries criminal liability."
        )
    },
    {
        "id": "E018",
        "doc_type": "employment",
        "name": "Minimum Wage Compliance",
        "statute": "Minimum Wages Order 2022, Section 3",
        "description": (
            "The national minimum wage in Malaysia is RM 1,700 per month "
            "(effective May 2023 for all employers). Any salary below this "
            "threshold is unlawful regardless of agreement between parties."
        ),
        "keywords": ["minimum wage", "minimum salary", "rm 1700", "rm1700",
                     "1,700", "minimum pay", "basic wage"],
        "check_type": "presence",
        "risk": "HIGH",
        "priority": 10,
        "recommendation": (
            "Confirm the stated salary meets the national minimum wage of "
            "RM 1,700/month under the Minimum Wages Order 2022. Any lower "
            "amount is void and unenforceable regardless of employee consent."
        )
    },
    {
        "id": "E019",
        "doc_type": "employment",
        "name": "HRDF / HRD Corp Levy",
        "statute": "Human Resources Development Act 2001, Section 14",
        "description": (
            "Employers with 10 or more employees in specified industries are "
            "required to register with HRD Corp and contribute a levy of 1% "
            "of each employee's monthly wages for training and development."
        ),
        "keywords": ["hrdf", "hrd corp", "human resource development",
                     "training levy", "hrdcorp", "hrdf levy",
                     "training fund"],
        "check_type": "presence",
        "risk": "LOW",
        "priority": 5,
        "recommendation": (
            "Reference HRD Corp obligations if the company has 10+ employees "
            "in a specified industry. Section 14 requires a 1% monthly levy "
            "on wages to fund employee training and upskilling."
        )
    },
    {
        "id": "E020",
        "doc_type": "employment",
        "name": "Employment Injury / Workmen Compensation",
        "statute": "Employees' Social Security Act 1969, Section 8; "
                   "Workmen's Compensation Act 1952",
        "description": (
            "The contract should address employer liability for workplace "
            "injuries. SOCSO coverage provides statutory protection, but "
            "the contract should not attempt to waive or limit this liability."
        ),
        "keywords": ["workplace injury", "work injury", "accident at work",
                     "occupational injury", "workmen compensation",
                     "industrial accident", "liability for injury",
                     "employer liability", "personal accident"],
        "check_type": "presence",
        "risk": "MEDIUM",
        "priority": 7,
        "recommendation": (
            "Reference employer liability for workplace injuries. Employees "
            "are protected under the SOCSO Employment Injury Scheme. The "
            "contract must not attempt to limit or waive this statutory right."
        )
    },

    # ══════════════════════════════════════════════════════════════════
    # RESIDENTIAL TENANCY AGREEMENT RULES (18)
    # ══════════════════════════════════════════════════════════════════

    {
        "id": "T001",
        "doc_type": "tenancy",
        "name": "Tenancy Duration and Term",
        "statute": "Contracts Act 1950, Section 2; National Land Code 1965",
        "description": (
            "The tenancy agreement must clearly state the start date, end "
            "date, and total duration. Ambiguous term provisions may render "
            "the agreement unenforceable."
        ),
        "keywords": ["tenancy period", "term of tenancy", "duration",
                     "commencement date", "expiry date", "start date",
                     "end date", "lease period", "tenancy term",
                     "tenancy shall commence", "period of tenancy"],
        "check_type": "presence",
        "risk": "HIGH",
        "priority": 10,
        "recommendation": (
            "Clearly state the start date, end date, and total duration. "
            "Ambiguous term provisions may be challenged under Section 2 "
            "of the Contracts Act 1950."
        )
    },
    {
        "id": "T002",
        "doc_type": "tenancy",
        "name": "Monthly Rental Amount",
        "statute": "Contracts Act 1950, Section 2",
        "description": (
            "The monthly rental amount must be explicitly stated in figures. "
            "Without a defined rental amount, the agreement may be void for "
            "uncertainty."
        ),
        "keywords": ["monthly rental", "rental amount", "rent of rm",
                     "monthly rent", "rental rate", "rental fee",
                     "rental sum", "monthly payment",
                     "rent per month", "monthly fee"],
        "check_type": "presence",
        "risk": "HIGH",
        "priority": 10,
        "recommendation": (
            "Explicitly state the monthly rental amount in both figures and "
            "words. An undefined rental amount renders the contract void for "
            "uncertainty under the Contracts Act 1950."
        )
    },
    {
        "id": "T003",
        "doc_type": "tenancy",
        "name": "Security Deposit Terms",
        "statute": "Contracts Act 1950, General Principles",
        "description": (
            "The agreement should specify the security deposit amount, "
            "permissible deduction conditions, and the timeline for "
            "return after tenancy ends."
        ),
        "keywords": ["security deposit", "deposit", "refundable deposit",
                     "two months deposit", "three months deposit",
                     "damage deposit"],
        "check_type": "presence",
        "risk": "HIGH",
        "priority": 9,
        "recommendation": (
            "Include a security deposit clause specifying: the amount, "
            "permissible deduction conditions, and the return timeline "
            "(typically 14–30 days after tenancy ends)."
        )
    },
    {
        "id": "T004",
        "doc_type": "tenancy",
        "name": "Utility Deposit",
        "statute": "Contracts Act 1950, General Principles",
        "description": (
            "A utility deposit is commonly collected to cover unpaid utility "
            "bills. The amount and refund conditions should be stated."
        ),
        "keywords": ["utility deposit", "utilities deposit", "water deposit",
                     "electricity deposit", "utility bill",
                     "half month deposit"],
        "check_type": "presence",
        "risk": "LOW",
        "priority": 4,
        "recommendation": (
            "Specify the utility deposit amount and refund conditions to "
            "avoid disputes over unpaid utility bills at end of tenancy."
        )
    },
    {
        "id": "T005",
        "doc_type": "tenancy",
        "name": "Rental Payment Due Date",
        "statute": "Contracts Act 1950, Section 2",
        "description": (
            "The agreement must specify when monthly rental is due and "
            "consequences of late payment to avoid disputes."
        ),
        "keywords": ["due date", "payment due", "rental due", "payable on",
                     "payable by", "rent due", "paid on the",
                     "payment date", "payable in advance",
                     "first of the month"],
        "check_type": "presence",
        "risk": "MEDIUM",
        "priority": 7,
        "recommendation": (
            "Specify the rental due date each month and late payment "
            "consequences (e.g., late charges or notice of termination)."
        )
    },
    {
        "id": "T006",
        "doc_type": "tenancy",
        "name": "Stamp Duty Obligation",
        "statute": "Stamp Act 1949",
        "description": (
            "Tenancy agreements must be stamped by LHDN to be legally "
            "admissible as evidence in court. The party responsible for "
            "payment should be clearly identified."
        ),
        "keywords": ["stamp duty", "lhdn", "inland revenue", "stamping",
                     "stamp act", "duly stamped", "stamped agreement",
                     "be stamped", "cukai setem"],
        "check_type": "presence",
        "risk": "HIGH",
        "priority": 10,
        "recommendation": (
            "Include a stamp duty clause. Under the Stamp Act 1949, tenancy "
            "agreements must be stamped by LHDN within 30 days of execution. "
            "An unstamped agreement is inadmissible as evidence in court."
        )
    },
    {
        "id": "T007",
        "doc_type": "tenancy",
        "name": "Termination Notice Period",
        "statute": "Contracts Act 1950, Section 2",
        "description": (
            "The agreement must specify the notice period required for "
            "either party to terminate before expiry, typically 2–3 months."
        ),
        "keywords": ["notice period", "termination notice", "notice of termination",
                     "month notice", "notice to vacate", "quit notice",
                     "month's notice", "months' notice", "written notice",
                     "two months notice", "three months notice"],
        "check_type": "presence",
        "risk": "HIGH",
        "priority": 9,
        "recommendation": (
            "Include a termination notice period (typically 2–3 months). "
            "Without this, either party may vacate or reclaim the property "
            "without adequate notice."
        )
    },
    {
        "id": "T008",
        "doc_type": "tenancy",
        "name": "Maintenance and Repairs Responsibility",
        "statute": "Contracts Act 1950, General Principles",
        "description": (
            "The agreement should clearly allocate responsibility for "
            "maintenance and repairs between landlord and tenant."
        ),
        "keywords": ["maintenance", "repair", "repairs", "landlord responsibility",
                     "tenant responsibility", "wear and tear", "fair wear"],
        "check_type": "presence",
        "risk": "MEDIUM",
        "priority": 7,
        "recommendation": (
            "Specify who is responsible for maintenance and repairs. "
            "Best practice: landlord handles structural repairs; tenant "
            "handles minor repairs below a defined threshold (e.g., RM 150)."
        )
    },
    {
        "id": "T009",
        "doc_type": "tenancy",
        "name": "Subletting Restriction",
        "statute": "Contracts Act 1950; National Land Code 1965, Section 221",
        "description": (
            "The agreement should state whether subletting is permitted. "
            "Subletting without landlord consent may breach the National "
            "Land Code."
        ),
        "keywords": ["sublet", "subletting", "sub-let", "sublease", "assign",
                     "not permitted to sublet", "consent to sublet"],
        "check_type": "presence",
        "risk": "MEDIUM",
        "priority": 7,
        "recommendation": (
            "Include a subletting clause. Section 221 of the National Land "
            "Code requires landlord consent for subletting. Specify clearly "
            "whether subletting is permitted and under what conditions."
        )
    },
    {
        "id": "T010",
        "doc_type": "tenancy",
        "name": "Landlord Access and Inspection Rights",
        "statute": "Contracts Act 1950, General Principles",
        "description": (
            "The landlord's right to inspect should be limited to reasonable "
            "advance notice (24–48 hours) to protect tenant privacy rights."
        ),
        "keywords": ["inspection", "right to inspect", "access to property",
                     "landlord access", "enter the premises", "right of entry",
                     "inspect the property", "prior notice", "advance notice"],
        "check_type": "presence",
        "risk": "MEDIUM",
        "priority": 6,
        "recommendation": (
            "Include an access clause specifying that the landlord must give "
            "at least 24 hours advance notice before entering the property, "
            "except in emergencies."
        )
    },
    {
        "id": "T011",
        "doc_type": "tenancy",
        "name": "Permitted Use of Property",
        "statute": "National Land Code 1965; Contracts Act 1950",
        "description": (
            "The agreement should restrict use of the property to residential "
            "purposes only, prohibiting commercial or illegal activities."
        ),
        "keywords": ["residential use", "permitted use", "residential purposes",
                     "not use for business", "domestic use", "no commercial",
                     "residential only", "for dwelling"],
        "check_type": "presence",
        "risk": "MEDIUM",
        "priority": 6,
        "recommendation": (
            "Specify that the property is for residential use only. Using a "
            "residential property for commercial purposes may breach local "
            "authority regulations and the National Land Code."
        )
    },
    {
        "id": "T012",
        "doc_type": "tenancy",
        "name": "Forfeiture / Early Termination Penalty",
        "statute": "Contracts Act 1950, Section 75",
        "description": (
            "If an early termination penalty exists, it must be a genuine "
            "pre-estimate of loss, not a penalty. Section 75 voids excessive "
            "penalty clauses."
        ),
        "keywords": ["forfeiture", "early termination", "forfeit deposit",
                     "break clause", "penalty", "liquidated damages",
                     "compensation for early"],
        "check_type": "risk_keyword",
        "risk": "MEDIUM",
        "priority": 7,
        "recommendation": (
            "Review forfeiture clauses. Section 75 of the Contracts Act 1950 "
            "voids penalty clauses that are not a genuine pre-estimate of "
            "loss. Ensure the penalty amount is proportionate and reasonable."
        )
    },
    {
        "id": "T013",
        "doc_type": "tenancy",
        "name": "Renewal Option",
        "statute": "Contracts Act 1950, General Principles",
        "description": (
            "If a renewal option is offered, the terms , including rental "
            "rate adjustment and notice period to exercise , should be "
            "clearly defined."
        ),
        "keywords": ["renewal", "renew", "option to renew",
                     "extension of tenancy", "renewed", "renewal term",
                     "extend the tenancy"],
        "check_type": "presence",
        "risk": "LOW",
        "priority": 4,
        "recommendation": (
            "If a renewal option is intended, state the notice period to "
            "exercise it (e.g., 2 months before expiry), any rental "
            "adjustment terms, and whether renewal is automatic or requires "
            "written agreement."
        )
    },
    {
        "id": "T014",
        "doc_type": "tenancy",
        "name": "Governing Law and Jurisdiction",
        "statute": "Contracts Act 1950, General Principles",
        "description": (
            "The agreement should specify Malaysian law as the governing "
            "law and identify the appropriate court jurisdiction for disputes."
        ),
        "keywords": ["governing law", "jurisdiction", "laws of malaysia",
                     "malaysian law", "applicable law", "dispute resolution"],
        "check_type": "presence",
        "risk": "LOW",
        "priority": 4,
        "recommendation": (
            "Add a governing law clause specifying Malaysian law and the "
            "jurisdiction for dispute resolution."
        )
    },
    {
        "id": "T015",
        "doc_type": "tenancy",
        "name": "Inventory and Handover List",
        "statute": "Contracts Act 1950, General Principles",
        "description": (
            "A signed list of furniture and fixtures should be attached to "
            "the tenancy to avoid disputes over damage or missing items "
            "at end of tenancy."
        ),
        "keywords": ["inventory", "inventory list", "fixture", "fitting",
                     "furniture list", "handover", "schedule of condition",
                     "items provided", "furnished"],
        "check_type": "presence",
        "risk": "LOW",
        "priority": 4,
        "recommendation": (
            "Attach a signed inventory list as a schedule. This protects "
            "both landlord and tenant from disputes over damage or missing "
            "items when the tenancy ends."
        )
    },

    # ADDITIONAL TENANCY RULES
    {
        "id": "T016",
        "doc_type": "tenancy",
        "name": "Late Payment Charges",
        "statute": "Contracts Act 1950, Section 75",
        "description": (
            "The agreement should specify a late payment charge for overdue "
            "rental to deter late payment. The charge must be a genuine "
            "pre-estimate of loss and not an excessive penalty."
        ),
        "keywords": ["late payment", "late charge", "overdue", "interest on late",
                     "penalty for late", "late fee", "interest rate"],
        "check_type": "presence",
        "risk": "LOW",
        "priority": 4,
        "recommendation": (
            "Include a late payment clause specifying a reasonable late "
            "charge (e.g., RM 50 per day or 8% per annum on the overdue "
            "amount). Section 75 requires the charge be a genuine pre-estimate "
            "of loss and not a disproportionate penalty."
        )
    },
    {
        "id": "T017",
        "doc_type": "tenancy",
        "name": "Pet Policy",
        "statute": "Contracts Act 1950, General Principles",
        "description": (
            "Whether pets are permitted should be clearly stated. If pets "
            "are allowed, conditions such as additional deposit or approved "
            "species should be specified to avoid disputes."
        ),
        "keywords": ["pet", "pets", "animal", "dog", "cat", "no pets",
                     "pets allowed", "pet deposit"],
        "check_type": "presence",
        "risk": "LOW",
        "priority": 3,
        "recommendation": (
            "Include a pet policy clause stating whether pets are permitted, "
            "and if so, the conditions (e.g., approved species, additional "
            "deposit for potential damage)."
        )
    },
    {
        "id": "T018",
        "doc_type": "tenancy",
        "name": "Handover Condition of Property",
        "statute": "Contracts Act 1950, General Principles",
        "description": (
            "The condition in which the property must be returned at the "
            "end of tenancy should be defined. Fair wear and tear is "
            "typically excluded from tenant liability."
        ),
        "keywords": ["handover condition", "vacant possession", "condition of property",
                     "return the property", "end of tenancy", "vacate",
                     "move out", "yield up", "upon expiry", "surrender the"],
        "check_type": "presence",
        "risk": "MEDIUM",
        "priority": 6,
        "recommendation": (
            "Specify the required condition of the property at end of "
            "tenancy, excluding fair wear and tear. This protects both "
            "parties and provides a clear basis for deposit deductions."
        )
    },
]


def get_rules_for_doc_type(doc_type: str) -> list:
    """Return only rules applicable to the given document type."""
    return [r for r in RULES if r["doc_type"] == doc_type]