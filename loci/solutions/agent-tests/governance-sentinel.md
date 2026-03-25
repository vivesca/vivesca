### gemini-3.1-pro-preview
Deploying an LLM for credit application summarization is a high-value but highly scrutinized use case. While positioning it as **"decision support, not decision making" (Human-in-the-Loop)** reduces the risk tier compared to fully automated credit scoring, the Hong Kong Monetary Authority (HKMA) still views this as critically impacting the credit lifecycle. 

Under the HKMA’s **General Principles for Artificial Intelligence** and recent circulars on Generative AI, banks must adhere to the principles of **Governance, Accountability, Fairness, and Transparency (FAG)**.

Here is a comprehensive breakdown of what can go wrong, the required controls, and how to structure your Model Risk Management (MRM) and AI oversight framework.

---

### Part 1: What Can Go Wrong? (Key Risk Scenarios)
Even in a decision-support role, an LLM summarization tool carries severe operational, regulatory, and credit risks.

1.  **Hallucinations and Fact Alteration:** The LLM might invent financial figures, miss critical loan covenants, or confuse currencies (e.g., misreading HKD as USD). If the RM relies on this, the bank could underwrite a poorly structured loan.
2.  **Automation Bias / The "Rubber Stamp" Effect:** Despite the "decision support" label, RMs may become over-reliant on the LLM due to workload pressures. They may stop reading the underlying credit files, effectively turning the LLM into a defacto decision-maker.
3.  **Loss of Context / Omission:** Summarization inherently involves removing information. The LLM might systematically strip out subtle qualitative risk factors (e.g., adverse management background checks) because it deems them statistically "unimportant," blinding the credit sanctioner.
4.  **Data Privacy and Confidentiality Breaches:** Injecting highly sensitive corporate financial data, PII of company directors, and proprietary bank credit criteria into a third-party LLM violates the Personal Data (Privacy) Ordinance (PDPO) and HKMA outsourcing rules if data is used to train public models.
5.  **Inconsistent Outputs:** Two identical credit files run through the LLM on different days might yield entirely different summaries due to the non-deterministic nature of GenAI.

---

### Part 2: Required Governance Controls
To meet HKMA expectations for AI MRM, your controls must be embedded in the data, the model, and the user interface.

#### A. Technical & Model Controls
*   **Retrieval-Augmented Generation (RAG) Architecture:** Do not rely on the LLM’s internal memory. Use RAG to force the LLM to summarize *only* the specific credit file provided, vastly reducing hallucination risk.
*   **Enterprise-Grade Tenancy (Data Fencing):** Deploy the LLM in a

### claude-opus-4-6
# LLM Deployment for Credit Application Summarisation: HKMA Governance Framework

## The Deceptive Simplicity Problem

This use case is commonly presented as "low risk" — it's just summarisation, not decisioning. That framing is dangerously wrong, and I'll explain why the governance requirements are substantially heavier than most banks initially budget for.

---

## I. Why "Decision Support, Not Decision Making" Is a Governance Fiction

### The Practical Reality

Relationship managers will, within weeks of deployment:

- **Anchor heavily** on the LLM summary rather than reading underlying documents
- **Treat omissions from the summary as signals** that information is unimportant
- **Develop speed expectations** that make returning to manual review psychologically costly
- **Lose the skill** of independent document synthesis over time

This means the LLM becomes a **de facto screening mechanism**. Any regulator — and certainly HKMA — will look through the label to the substance. If the summary shapes the credit decision, it's in the decisioning chain regardless of how you position it.

### Why This Matters for Control Design

Every governance control must be designed as though this tool **influences credit decisions**, because it will. The "just a summary" framing should appear nowhere in your risk documentation — it invites regulatory challenge and creates a false sense of security internally.

---

## II. Applicable HKMA Framework and Expectations

### Primary Regulatory Sources

| Source | Relevance |
|--------|-----------|
| **SA-2 (Supervisory Approach to Model Risk Management)** | Core framework — the LLM is a model under HKMA's definition if its output informs business decisions |
| **HKMA High-Level Principles on AI** (Nov 2019) | Consumer protection, governance, accountability principles |
| **GS-1 (General Principles for Technology Risk Management)** | IT risk, change management, vendor oversight |
| **IC-1 (Risk Management of E-banking)** | Data integrity, access controls if customer data flows through the system |
| **HKMA Circular on Consumer Protection in respect of use of Big Data Analytics and AI** (2019) | Fairness, explainability expectations |
| **SPM CR-G-3 (Credit Risk Management)** | Sound credit practices — the LLM must not undermine these |
| **PDPO (Personal Data Privacy Ordinance)** | Data use limitations, cross-border data transfer rules |

### The SA-2 Model Risk Management Angle

Under SA-2, HKMA expects banks to maintain a **model inventory** and apply governance proportionate to materiality. Key question: is this LLM a "model"?

**Yes, unambiguously.** SA-2 defines a model broadly — any quantitative method that processes inputs to produce outputs used in business decisions. An LLM summarising credit applications to inform RM assessment falls squarely within scope. The bank must:

- Register it in the model inventory
- Assign a model risk rating (likely Medium-High given credit chain proximity)
- Apply the full model lifecycle governance: development, validation, approval, monitoring, change management

---

## III. Required Governance Controls — Detailed Architecture

### A. Model Development and Selection Governance

**1. Use Case Scoping and Boundary Definition**

```
CONTROL: Formal use case charter documenting:
├── Precisely what the LLM summarises (application forms, financial 
│   statements, supporting documents, prior credit history?)
├── What it must NOT do (score, recommend, rank, compare to peers)
├── Explicit boundary conditions (document types, languages, 
│   application sizes, customer segments)
├── Defined user population and access controls
└── Escalation criteria where the summary should not be relied upon
```

**2. Model Selection Justification**

- Why an LLM rather than simpler NLP/extractive summarisation?
- If using a foundation model (GPT-4, Claude, etc.), why that specific model?
- Build vs. buy analysis with risk comparison
- If fine-tuned, documentation of training data provenance and representativeness

**3. Prohibited Behaviours Register**

Define explicitly what the model must never do:
- Generate credit scores or risk ratings
- Make approval/rejection recommendations (even implicitly through tone)
- Compare the applicant to other customers
- Extrapolate or infer information not present in source documents
- Generate financial projections or forward-looking statements
- Summarise in ways that embed subjective credit judgement ("strong applicant", "weak financials")

This register must be tested against, not merely documented.

### B. Data Governance

**4. Data Flow Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA GOVERNANCE LAYER                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Source Documents ──► Pre-processing ──► LLM ──► Summary    │
│       │                    │              │         │        │
│       ▼                    ▼              ▼         ▼        │
│  Classification &    PII handling    Inference    Output     │
│  access control      & masking       logging     filtering  │
│                                                             │
│  KEY CONTROLS AT EACH STAGE:                                │
│                                                             │
│  ► What data enters the model?                              │
│  ► Where is inference performed? (on-prem vs cloud)         │
│  ► Is data retained by the model provider?                  │
│  ► Can prompts/outputs be used for retraining?              │
│  ► Are logs maintained for audit?                           │
│  ► Is PII minimised before inference?                       │
└─────────────────────────────────────────────────────────────┘
```

**5. Cross-Border Data Transfer**

If using a cloud-hosted LLM:
- Where does inference occur geographically?
- Does PDPO Section 33 (cross-border transfer restriction) apply?
- Has the Privacy Commissioner's guidance on cloud computing been followed?
- For Mainland China-connected customers, does the PRC PIPL create additional constraints?

**6. Data Retention and Deletion**

- Summaries are derived data — what is the retention policy?
- If summaries persist but source documents are purged, you create an untestable artefact
- Logging of all inputs/outputs for model monitoring creates its own data governance burden

### C. Model Validation (Independent)

**7. Pre-Deployment Validation**

This is where most banks underinvest. HKMA expects independent validation proportionate to model risk rating.

**Validation Scope:**

| Test Category | What to Test | How |
|--------------|--------------|-----|
| **Faithfulness** | Does the summary accurately reflect the source documents? | Human comparison on stratified sample (by segment, complexity, language) |
| **Completeness** | Does the summary capture all material information? | Define "material" via credit policy, then test systematically |
| **Omission bias** | Does the model systematically omit certain types of adverse information? | Adversarial testing with planted negative information |
| **Hallucination** | Does the model fabricate information not in the source? | Fact-checking framework against source documents |
| **Consistency** | Same inputs → materially same outputs? | Repeated inference testing; measure variance |
| **Robustness** | Does performance degrade with unusual inputs? | Edge cases: very long documents, mixed languages, handwritten elements, poor scans |
| **Fairness/bias** | Does summary quality or framing differ by customer demographics? | Paired testing across demographic dimensions |
| **Tone neutrality** | Does the summary inadvertently convey credit judgement? | Linguistic analysis; blind RM testing |

**8. Ongoing Validation**

- Periodic re-validation (at least annually, or triggered by model updates)
- Continuous monitoring metrics (see Section E below)
- Validation must be performed by a team independent of the model developers and business users

### D. Approval and Governance Bodies

**9. Model Approval**

```
GOVERNANCE STRUCTURE:

Board Risk Committee
        │
        ▼
Senior Management (CRO sign-off required — credit chain involvement)
        │
        ▼
Model Risk Management Committee
├── Reviews model risk assessment
├── Approves risk rating
├── Reviews validation results
├── Sets monitoring requirements
├── Approves conditions of use
        │
        ▼
Three Lines of Defence:
1st Line: Business (Credit) owns the model use and user compliance
2nd Line

### grok-4
Below is a comprehensive response to your query on deploying a Large Language Model (LLM) for summarizing credit applications in a Hong Kong bank. This is positioned as decision support (e.g., providing concise overviews for relationship managers to aid human decision-making, without automating approvals). I'll draw from the Hong Kong Monetary Authority's (HKMA) relevant guidelines, including the Supervisory Policy Manual (SPM) on Model Risk Management (e.g., SA-1 on Credit Risk Assessment Models, though LLMs may fall under broader AI governance), the 2019 High-level Principles on Artificial Intelligence, and subsequent circulars on AI adoption in banking (e.g., those emphasizing consumer protection, fairness, and resilience). Note that HKMA's expectations align with global standards like those from the Basel Committee and EU AI Act, but are tailored to Hong Kong's context.

HKMA views AI models like LLMs as potentially high-risk if they influence credit decisions, even indirectly. They emphasize robust governance to mitigate model risk, ensure fairness, and protect consumers. I'll break this down into the three parts of your question: required governance controls, potential risks (what can go wrong), and structuring an oversight framework. This is not legal advice—consult HKMA directly or a regulatory expert for your specific implementation.

### 1. Required Governance Controls
HKMA requires banks to treat LLMs as "models" under model risk management frameworks, especially if they process sensitive data like credit applications. Key controls must address the model's lifecycle (development, deployment, monitoring, and decommissioning). Since this is decision support, HKMA would expect emphasis on human oversight, explainability, and non-discrimination.

- **Model Development and Validation**:
  - Conduct independent validation by a qualified team (e.g., not the developers) to assess accuracy, bias, and robustness. This includes testing for hallucinations (e.g., fabricating details in summaries) and edge cases like incomplete applications.
  - Ensure data quality: Use representative, high-quality training data compliant with Personal Data (Privacy) Ordinance (PDPO). Anonymize or pseudonymize personal data to avoid privacy risks.
  - Bias and Fairness Testing: Evaluate for unintended discrimination (e.g., based on protected attributes like gender, ethnicity, or age) under HKMA's fairness principles. Use metrics like demographic parity or equalized odds.

- **Explainability and Transparency**:
  - LLMs must be interpretable—e.g., provide reasoning traces or confidence scores in summaries. HKMA expects documentation of how the model generates outputs, especially for credit-related use.
  - Clear labeling: Summaries should flag AI-generated content and note limitations (e.g., "This is an AI summary; verify with original documents").

- **Security and Resilience**:
  - Implement cybersecurity controls (e.g., encryption, access controls) per HKMA's Technology Risk Management guidelines (TM-G-1). Protect against prompt injection or adversarial attacks that could manipulate summaries.
  - Vendor Management: If using a third-party LLM (e.g., from OpenAI or a cloud provider), conduct due diligence on the vendor's AI governance, as per HKMA's Outsourcing guidelines (SA-2).

- **Ongoing Monitoring and Auditing**:
  - Establish performance metrics (e.g., accuracy of summaries vs. human benchmarks) and thresholds for alerts. Monitor for model drift (e.g., declining performance due to changing economic conditions).
  - Conduct regular audits, including stress testing for scenarios like market downturns.

- **Human-in-the-Loop and Accountability**:
  - Mandate human review of all AI outputs before use in decisions. Train relationship managers on AI limitations to prevent over-reliance.
  - Define accountability: Senior management must approve the deployment and own risks, per HKMA's corporate governance expectations (CG-1).

- **Regulatory Reporting and Compliance**:
  - Notify HKMA of the deployment if it's material (e.g., via annual AI risk assessments). Ensure alignment with anti-money laundering (AML) and know-your-customer (KYC) rules, as summaries could inadvertently omit red flags.

These controls should be documented in a model risk policy, with escalations for issues.

### 2. What Can Go Wrong (Potential Risks)
Even with controls, LLMs in credit summarization can introduce risks due to their probabilistic nature, lack of inherent reasoning, and sensitivity to inputs. HKMA emphasizes identifying and mitigating these to avoid systemic issues like unfair lending or operational failures. Common pitfalls include:

- **Accuracy and Reliability Issues**:
  - Hallucinations or Fabrications: The LLM might invent details (e.g., exaggerating an applicant's income), leading to flawed decisions. This could result in bad loans or regulatory penalties.
  - Model Drift: Performance degrades over time if economic conditions change (e.g., post-pandemic credit patterns), causing outdated summaries.

- **Bias and Fairness Risks**:
  - Discriminatory Outputs: If trained on biased data, the LLM could unfairly summarize applications from certain demographics (e.g., downplaying risks for high-income groups), violating HKMA's consumer protection rules and leading to lawsuits or fines.
  - Over-Reliance: Relationship managers might treat summaries as gospel, bypassing thorough reviews, which could amplify errors in credit assessments.

- **Data Privacy and Security Breaches**:
  - Leaks of Sensitive Information: Processing credit data (e.g., financial histories) could breach PDPO if not handled securely, exposing the bank to data protection fines.
  - Cyber Vulnerabilities: Adversaries could exploit the LLM (e.g., via jailbreak prompts) to extract confidential data or generate misleading summaries.

- **Operational and Reputational Risks**:
  - Scalability Failures: High volumes of applications could overwhelm the model, causing delays or inconsistencies.
  - Regulatory Non-Compliance: If the LLM indirectly influences decisions (e.g., by biasing human judgment), HKMA could deem it "decision-making," triggering stricter scrutiny. This might lead to enforcement actions, as seen in past cases of AI misuse in lending.
  - Ethical Concerns: Poorly governed AI could erode customer trust, especially if summaries appear impersonal or error-prone.

- **Systemic Risks**: In a downturn, widespread use could propagate errors across the bank's portfolio, contributing to financial instability—aligning with HKMA's focus on resilience.

Mitigation involves scenario planning (e.g., "what if the model hallucinates a key risk?") and contingency plans like fallback to manual processes.

### 3. Structuring the Oversight Framework
HKMA expects a robust, board-level oversight framework, often based on the "three lines of defense" model, integrated into the bank's enterprise risk management. Structure it to ensure independence, accountability, and scalability. Here's a recommended high-level structure:

- **Governance Structure**:
  - **Board and Senior Management Oversight**: The board (or a dedicated AI/Risk Committee) approves the framework and receives quarterly reports on LLM performance and risks. Senior executives (e.g., Chief Risk Officer) are accountable for compliance.
  - **AI Governance Committee**: A cross-functional group (including risk, compliance, IT, and business leads) to review deployments, policies, and incidents. Meet monthly to assess metrics like bias scores or error rates.

- **Three Lines of Defense**:
  - **First Line (Business/Operations)**: Relationship managers and AI developers own day-to-day use. They implement controls (e.g., human review protocols) and report metrics.
  - **Second Line (Risk and Compliance)**: Independent teams monitor risks, conduct validations, and ensure HKMA alignment. They handle bias testing and escalate issues.
  - **Third Line (Internal Audit)**: Performs periodic, independent audits of the entire framework, including penetration testing of the LLM.

- **Policies and Procedures**:
  - Develop an AI Policy Document outlining controls, roles, and escalation paths. Include incident response (e.g., for detected hallucinations) and change management for model updates.
  - Training Programs: Mandatory for users on AI literacy, risks, and ethical use.
  - Monitoring Dashboard: Real-time tools to track key indicators (e.g., summary accuracy >95%, bias variance < threshold).

- **Integration with Broader Frameworks**:
  - Align with HKMA's Operational Resilience guidelines (OR-1) for continuity planning.
  - External Assurance: Engage third-party auditors for validations, especially for complex LLMs.
  - Scalability: Start with a pilot (e.g., on a subset of applications) to test and refine, then scale with HKMA notification.

This framework should be dynamic—review annually or after major incidents. HKMA may require a risk assessment report during inspections.

In summary, HKMA's expectations prioritize safety, fairness, and accountability for AI like LLMs in banking. By implementing these controls and frameworks, the bank can minimize risks while leveraging AI for efficiency. If this deployment involves novel elements, consider seeking HKMA's feedback through their Fintech Supervisory Chatroom or formal consultations. For tailored advice, engage legal/regulatory specialists familiar with Hong Kong banking.

### kimi-k2.5
Here is a structured governance framework aligned with HKMA’s **SPM CG-5 (Model Risk Management)** and the **HKMA’s Generative AI (GenAI) guidance** (2024), treating the LLM as a **high-risk model** despite its “decision support” positioning.

---

### 1. Regulatory Baseline: Why “Decision Support” Is Still High-Risk
HKMA explicitly warns that “human-in-the-loop” does not obviate model risk. Credit applications involve **sensitive personal data**, **potential fair lending implications**, and **material financial risk**. Under SPM CG-5 and the GenAI circular, this use case requires:
*   **Full MRM lifecycle governance** (development, validation, monitoring)
*   **Board accountability** for AI strategy
*   **“Effective challenge”** from independent risk functions
*   **Explainability** commensurate with credit risk materiality

---

### 2. Required Governance Controls

#### A. Model Development & Validation (SPM CG-5)
| Control | Implementation for LLM Credit Summarizer |
|---------|------------------------------------------|
| **Inventory & Risk Tiering** | Classify as **Tier 1 (High Risk)** due to credit domain + GenAI opacity. Mandatory approval by Model Risk Committee. |
| **Validation Scope** | Beyond accuracy: test for **hallucinations**, **omission bias**, **robustness to adversarial prompts**, and **concept drift** in credit language. |
| **Ground Truth** | Establish human-verified “golden set” of applications where summary quality is objectively scored (completeness, factual consistency). |
| **Explainability** | Implement **Retrieval-Augmented Generation (RAG)** with strict source attribution.<br>• Constrain output to extracted text chunks only.<br>• Prohibit generative “extrapolation” of financial ratios not explicitly stated in source docs. |
| **Fairness Testing** | Test for disparate impact across protected classes (gender, age, ethnicity proxies) in *how* the LLM emphasizes risks (e.g., does it consistently highlight repayment risk for certain demographics?). |

#### B. Data & Prompt Governance
*   **Training Data Provenance**: Document all pre-training and fine-tuning corpora; scrub for PII under PDPO. If using external foundation models (e.g., via Azure OpenAI), establish contractual prohibitions on data retention/training.
*   **Prompt Version Control**: Treat system prompts as code—versioned, regression-tested, and restricted. Implement **prompt injection detection** (e.g., hidden text in uploaded PDFs attempting to bias summaries).
*   **Data Leak Prevention (DLP)**: Technical blocks preventing RMs from pasting full credit files into public LLM APIs. Enforce **air-gapped** or **private cloud deployment** only.

#### C. Human-AI Interface Controls (Automation Bias Mitigation)
The “decision support” framing often fails because RMs develop automation bias. HKMA expects controls to ensure **“meaningful human control”**:
*   **Forced Dwell Time**: UI requires RMs to open source documents before accepting summary.
*   **Uncertainty

### glm-5
This is a high-stakes use case. In Hong Kong, the HKMA (Hong Kong Monetary Authority) has been progressively tightening expectations regarding AI governance, specifically moving from generic "fintech" guidelines to concrete expectations on **Model Risk Management (MRM)** and **Explainability**.

Even though the system is labelled "decision support," under HKMA scrutiny, if the output is used to facilitate a credit decision, it is treated as a material model.

Here is a structured governance framework tailored for a Hong Kong bank deploying an LLM for credit summarisation.

---

### 1. Regulatory Context: The HKMA Expectations

The primary references here are the **HKMA’s Supervisory Policy Manual (SPM)**, specifically **TM-G-1** (General Risk Management Controls for E-Banking) and recent industry guidance on **Big Data Analytics and AI (November 2019)**, alongside the **Principles for Effective Risk Management**.

Key obligations include:
*   **Explainability:** The bank must be able to explain the basis of the summary to the RM and, ultimately, to the borrower or regulator.
*   **Fairness & Ethics:** No bias in how applications from different demographics are summarised.
*   **Accountability:** The "Human-in-the-Loop" (the RM) remains fully accountable; the LLM is an assistant, not an authority.

---

### 2. What Can Go Wrong? (Risk Analysis)

For an LLM summarising credit applications, the risks are distinct from traditional statistical models (like scorecards).

**A. The "Hallucination" Risk (Accuracy)**
*   **The Risk:** The LLM invents facts that are not in the source documents. For example, it might state "The applicant has a stable cash flow of HKD 5m" when the financial statements actually show a decline.
*   **Consequence:** The RM relies on a false summary, leading to a "Wrong Way" credit decision. Under HKMA rules, this is a data integrity and operational risk failure.

**B. Contextual Amnesia & Omission**
*   **The Risk:** LLMs have token limits. If a credit application is 100 pages but the LLM only 'reads' the first 20 pages due to context window constraints, it might miss a critical lawsuit mentioned in the appendix.
*   **Consequence:** Material information is excluded from the summary, violating the "Know Your Customer" (KYC) and credit assessment requirements.

**C. Automation Bias**
*   **The Risk:** RMs become over-reliant on the summary. They stop reading the source documents.
*   **Consequence:** The label "decision support" becomes a farce; the LLM is effectively making the decision. HKMA would view this as a failure of oversight.

**D. Data Privacy & Security (PDPO)**
*   **The Risk:** Feeding customer PII (Personal Identifiable Information) into a cloud-based LLM (e.g., OpenAI via API) without proper safeguards.
*   **Consequence:** Breach of the Personal Data (Privacy) Ordinance (PDPO) and HKMA data protection rules.

---

### 3. Required Governance Controls

To mitigate the above risks, the following controls must be embedded in the MRM lifecycle.

#### Input Controls (Data Governance)
*   **Data Anonymization:** Before data reaches the LLM, PII should be masked or tokenized unless the model is hosted in a secure, bank-controlled environment (e.g., Azure OpenAI instance within the bank's tenant).
*   **Input Context Management:** Implement a RAG (Retrieval-Augmented Generation) architecture that forces the LLM to cite specific pages/documents. The system must not allow the LLM to "freestyle."

#### Model Controls (Development & Validation)
*   **RAG with Citations:** The LLM must be architected to provide references. If the summary says "Revenue is up," it must link to "Page 4, Financial Statement." If it cannot cite it, it should not generate the text.
*   **Guardrails:** Implement "negative constraints." The model should be instructed via system prompts to *never* generate a credit recommendation (e.g., "Approve/Deny"). It should strictly summarise facts.
*   **Validation Testing:** Unlike traditional models where you test for predictive power, here you test for **Faithfulness**.
    *   *Test:* Feed the model a "poisoned" application (with planted errors) and see if the summary catches them or hallucinates over them.

#### Output Controls (User Interface & Process)
*   **Verification Workflow:** The UI must force the RM to click on the source text to validate the summary. A summary should not be copy-pasteable without verification.
*   **Disclaimer & Audit Trail:** Every output must carry a watermark/timestamp: "AI Generated Summary - For Reference Only." All prompts and outputs must be logged for audit purposes.

---

### 4. Structuring the Oversight Framework

You should structure the governance using the **Three Lines of Defence** model, adapted for Generative AI.

#### First Line of Defence: Business Unit (Credit Risk / RM Team)
*   **Role:** The RMs are the model users and the *decision owners*.
*   **Responsibility:** They must undergo "AI Literacy Training." They are required to sign off that they have verified the AI summary against the original documents. If they approve a bad loan based on a hallucination, the RM is liable, not the AI.

#### Second Line of Defence: Risk Management & Compliance
*   **Model Risk Management (MRM) Team:**
    *   Classify this model as **Tier 1 or Tier 2** (Higher Risk) because it impacts credit decisions.
    *   Conduct independent validation of the LLM's "Hallucination Rate."
    *   Set the "Model Appetite" (e.g., The model cannot be deployed if the error rate > 5%).
*   **IT Risk / Data Governance:** Ensure the LLM vendor (if external) complies with HKMA's **Outsourcing guidelines** (data residency in HK or approved jurisdictions).

#### Third Line of Defence: Internal Audit
*   **Role:** Independent assurance.
*   **Responsibility:** Audit the "Human-in-the-Loop" process. Are RMs actually checking the AI summaries, or just rubber-stamping them? Audit the logs for prompt injection attacks.

---

### 5. Summary Checklist for the HKMA

If the HKMA investigates this deployment, be prepared to answer these three questions:

1.  **Explainability:** "How do you prove the summary is based on the actual application and not made up?" -> *Answer: Our RAG system provides sentence-level citations linking to the source PDFs.*
2.  **Accountability:** "Who is responsible if the summary is wrong?" -> *Answer: The Relationship Manager. We have a signed attestation workflow requiring manual verification.*
3.  **Privacy:** "Does the model learn from private customer data?" -> *Answer: No. We use a frozen model instance; no fine-tuning is performed on live customer data, and data is not retained by the vendor.*

### Recommendation: Start with a "Shadow Mode"
Do not deploy immediately to live decision support. Run the LLM in **Shadow Mode** for 3 months.
*   Generate summaries for RMs.
*   Ask RMs to rate the accuracy (1-5).
*   Compare the LLM summary against the RM's manual summary.
*   Only promote to "Decision Support" once the accuracy rate meets the MRM threshold.

### gpt-5.4-pro
[Fallback also failed for GPT-5.4-Pro: primary=[Error: Connection failed for openai gpt-5.4-pro: error sending request for url (https://api.openai.com/v1/responses)], fallback=[Error: Internal Server Error]]