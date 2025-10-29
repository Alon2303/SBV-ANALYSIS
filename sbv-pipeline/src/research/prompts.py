"""Prompt templates for LLM-based analysis."""

RESEARCH_SYSTEM_PROMPT = """You are an expert analyst specializing in early-stage technology companies, particularly in climate tech, materials science, and advanced manufacturing.

Your role is to:
1. Extract factual information from web content
2. Identify specific technical claims with supporting evidence
3. Assess readiness levels based on industry standards (TRL 1-9, etc.)
4. Identify strategic bottlenecks that could prevent scale-up
5. Rate evidence quality, theoretical grounding, and social proof

Be skeptical and evidence-based. Distinguish between company claims and independently verified facts.
Always cite sources and quantify claims when possible."""

BOTTLENECK_ANALYSIS_PROMPT = """Analyze the following company and identify strategic bottlenecks that could prevent successful scale-up.

**IMPORTANT: Respond with valid JSON format only.**

Company: {company_name}
Description: {description}
Technology: {technology}
Stage: {stage}
Key Claims: {claims}

Identify 3-7 bottlenecks across these categories:
- technical: Core R&D or engineering challenges
- market: Customer adoption, anchor customers
- regulatory: Certifications, approvals, compliance
- economics: Unit economics, cost structure
- capital: Funding needs
- integration: Manufacturing line integration
- EHS/process: Environmental, health, safety issues

For each bottleneck, provide:
{{
    "bottlenecks": [
        {{
            "id": "B1",
            "type": "technical|market|regulatory|economics|capital|integration|EHS/process",
            "location": "brief location description",
            "severity_raw": 1-5 (5=critical),
            "severity_adj": 1-5,
            "verified": "verified|partial|unverified",
            "owner": "who needs to solve this",
            "timeframe": "estimated timeframe like 0-24m",
            "evidence_strength": 1-3,
            "citations": ["URL1", "URL2"]
        }}
    ]
}}

Base severity on:
- 5: Critical blocker, no workaround
- 4: Major challenge, significant resources needed
- 3: Moderate challenge, standard for the stage
- 2: Minor challenge, well-understood solution
- 1: Low risk, easily addressable
"""

READINESS_SCORING_PROMPT = """Score the readiness levels for this company:

Company: {company_name}
Description: {description}
Technology: {technology}
Stage: {stage}
Key Claims: {claims}

Provide scores (1-9) for:

**TRL (Technology Readiness Level):**
1-2: Basic research
3-4: Proof of concept
5-6: Lab/pilot validation
7-8: Demonstration in operational environment
9: Proven in production

**IRL (Integration Readiness Level):**
1-3: Component testing
4-6: Integration testing
7-9: System validation in operational environment

**ORL (Operations Readiness Level):**
1-3: Concept development
4-6: Operational planning & testing
7-9: Full operational capability

**RCL (Regulatory/Compliance Level):**
1-3: Awareness of requirements
4-6: Testing & documentation underway
7-9: Certified & approved

Return JSON:
{{
    "TRL": 5.0,
    "IRL": 3.5,
    "ORL": 3.0,
    "RCL": 1.5,
    "reasoning": "Brief explanation of scores"
}}
"""

LIKELY_LOVELY_SCORING_PROMPT = """Score the Likely & Lovely metrics for this company's main claims:

Company: {company_name}
Description: {description}
Technical Claims: {technical_claims}
Social Proof: {social_proof}
Evidence Sources: {evidence_sources}

Provide scores (1-5) for:

**E (Evidence):**
1: No public evidence, only company claims
2: Company claims + ecosystem mentions
3: Third-party mentions, no independent validation
4: Some independent validation (e.g., grant reports, pilot mentions)
5: Strong independent validation (peer-reviewed data, production results)

**T (Theory):**
1: No theoretical basis, purely empirical claims
2: Some physics/chemistry basis, not well-established
3: Solid theoretical foundation, plausible mechanism
4: Strong theory backed by literature, some precedent
5: Well-established theory, clear precedent, peer-reviewed

**SP (Social Proof):**
1: No credible validation
2: Early-stage accelerator or minor grant
3: Reputable accelerator, grants, or institutional support
4: Multiple grants, partnerships, pilot customers
5: Major customers, significant funding, strong advisory board

**LV (Lovely - Desirability/Impact if true):**
1: Marginal improvement
2: Useful improvement
3: Significant improvement, good value
4: Major impact, strong decarbonization or cost benefits
5: Transformative impact, game-changing for industry

Return JSON:
{{
    "E": 2,
    "T": 4,
    "SP": 3,
    "LV": 4,
    "reasoning": "Brief explanation of each score"
}}
"""

