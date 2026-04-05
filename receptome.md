# Receptome -- 2026-04-05 13:05

Total: **187** skills (146 invocable, 41 reference)
With REFERENCE.md: 3 | With scripts/: 0
Trigger phrases indexed: 102

## By Category

| Category | Count | Skills |
|----------|-------|--------|
| other | 36 | askesis, assay-source, auscultation, autophagy, autopoiesis, certus, conjugation, contract +28 more |
| research | 33 | anam, auceps, cardo, comes, consilium, diagnosis, ecphory, elencho +25 more |
| maintenance | 27 | adytum, amicus, assay, circadian, cron, cytometry, docima, eow +19 more |
| meta | 25 | bouleusis, censor, debridement, derepression, epistula, fasti, gist, grapho +17 more |
| dispatch | 15 | agent-cli, centrosome, heuretes, involution, kindle, legatus, mitogen, opifex +7 more |
| content | 13 | adhesion, agoras, analyze, evaluate-job, exocytosis, message, presentation, python +5 more |
| consulting | 8 | capco-prep, chemoreception, meeting-prep, metabolize, mora, opsonization, secretion, statio |
| comms | 7 | cursus, deltos, endosomal, graphis, horizo, imessage, keryx |
| dev | 7 | etiology, fingo, friction, hypha, lucus, remote-llm, taxis |
| health | 6 | biomorphe, daily, differentiation, mappa, salus, sopor |
| workflow | 6 | dialexis, digest, expression, infradian, melete, weekly |
| finance | 3 | fiscus, praeco, stips |
| calendar | 1 | auspex |

## Size Distribution

- Stubs (<20 lines): 3
- Small (20-99): 107
- Medium (100-299): 74
- Large (300-799): 3
- Bloated (800+): 0

## Most Referenced Skills

- **consilium** (3): gnome, scrutor, transcription-factor
- **sopor** (2): involution, quies
- **kairos** (1): cardo
- **grok** (1): elencho
- **exauro** (1): elencho
- **noesis** (1): elencho
- **stips** (1): elencho
- **nuntius** (1): epistula
- **qmd** (1): gnome
- **judex** (1): gnome

## Full Catalog

### Calendar

- **auspex**: Wake-up brief — weather, calendar, key deadlines today. Run when you wake up. Invoke with /auspex.

### Comms

- **cursus** [ref]: Career communication principles — reference skill consulted by message, meeting-prep, capco-prep. Not user-invocable.
- **deltos**: Send text/code snippets or image files to Telegram. Text → HTML code blocks for mobile copy-paste. Images → sendPhoto wi
- **endosomal**: Triage email — classify, archive noise, extract action items. "email", "inbox
- **graphis** [ref]: Manage Telegram bots — create, delete, list, start-bot via BotFather. Use when creating a new bot, retiring an old one, 
- **horizo**: Appointment scheduling workflow — coordinate time via WhatsApp (keryx) then book to Google Calendar (gog). Use when sche
- **imessage**: Send iMessages via CLI. Use when user wants to text wife or send an iMessage to someone.
- **keryx**: WhatsApp CLI wrapper — contact name resolution, dual-JID conversation merging, daemon-aware send block, sync daemon mana

### Consulting

- **capco-prep**: Capco onboarding readiness — drill, brief, or event-specific prep. 'capco prep', 'capco drill', 'capco brief
- **chemoreception**: AI briefing on demand — refresh stale context before a meeting or decision.
- **meeting-prep**: Drill for upcoming meetings with scenario-based questions. "meeting prep", "prep for meeting", "prep for coffee
- **metabolize**: Process articles through Capco consulting lens — extract, write insight cards.
- **mora**: Surface productive low-energy tasks when you have downtime. Use when energy is low, between meetings, or during idle mom
- **opsonization**: Drill for upcoming meetings or interviews with scenario practice. "meeting prep
- **secretion**: Package and release a consulting deliverable — quality-gate, format, ship.
- **statio**: Start-of-work brief — priorities, gates, inbox triage, Capco prep, GARP nudge. Run when you sit down at the desk. Invoke

### Content

- **adhesion**: Evaluate LinkedIn job postings for fit — job URL or "evaluate this role".
- **agoras**: Draft LinkedIn comments and posts. Use when user shares a LinkedIn URL to comment on, says "linkedin comment", "linkedin
- **analyze**: Classify content, extract insights, and save a structured vault note. Use when user shares content (article, job posting
- **evaluate-job**: Evaluate LinkedIn job postings for fit. Triggers on job URLs or "evaluate this role".
- **exocytosis**: Publish to terryli.hm garden. Secretome (chromatin) -> Astro -> deploy. CLI: ~/germline/effectors/publish. Posts: ~/epig
- **message**: Draft responses to recruiter and networking messages (LinkedIn DMs, WhatsApp intros, cold outreach). NOT for email (use 
- **presentation**: Reference for visual communication patterns in presentations and data storytelling. Consult when creating slides, Linked
- **python**: Python development — new script/package scaffold, uv workflow, PyPI publish checklist. Use when starting or publishing P
- **redarguo**: One-line adversarial challenge via a different LLM. Use PROACTIVELY before committing to decisions, sending client deliv
- **rust**: Rust CLI development — new project scaffold, daily dev workflow, pre-publish checklist. Use when starting or publishing 
- **speculor**: Daily LinkedIn job alert collector and AI triage tool. Use when checking job alerts, running triage, or troubleshooting 
- **stilus**: Gmail operations via gog CLI — inbox triage, send/reply, archive, batch modify, drafts. Use for email actions. NOT for C
- **theoros**: LinkedIn daily feed digest. Run manually or check today's digest. Use when asking about recent LinkedIn activity, job le

### Dev

- **etiology**: Root-cause diagnosis for bugs and process failures. "broken", "debug
- **fingo**: Rust CLI for AI image generation and editing via Gemini. Use when generating or editing images from the terminal.
- **friction**: Capture friction moments during work. Use when the user says "friction", types "/friction", or explicitly flags frustrat
- **hypha**: Obsidian vault link graph traversal — navigate outgoing/incoming links from a note, explore to depth N, find shortest pa
- **lucus** [ref]: Git worktree manager for parallel AI agent sessions. Use when starting a new feature/fix that needs isolation from other
- **remote-llm**: Craft prompts for local/work LLMs when code can't be shared directly (e.g. proprietary code).
- **taxis**: Architecture of the Claude Code enforcement and knowledge system. Consult when adding hooks, rules, or deciding where kn

### Dispatch

- **agent-cli** [ref]: Design patterns for CLIs intended to be used by AI agents rather than humans. Consult when building a new CLI that Claud
- **centrosome**: RETIRED — merged into /mitogen. Use /mitogen for all dispatch.
- **heuretes**: Agent research org — run a hierarchical team of AI agents on open-ended research or exploration tasks. Chief orchestrato
- **involution**: Evening wind-down — brain dump, queue overnight tasks, gate screens-off. (calls: sporulation, sopor)
- **kindle**: Extract Kindle books to markdown via screenshots + Gemini vision. Single book or queue mode.
- **legatus**: Session-independent AI agent dispatcher — list tasks, dispatch immediately, cancel, view results. Use for any background
- **mitogen**: Dispatch ribosome for any build task — bulk campaigns or single features. "build", "implement", "dispatch", "go build", 
- **opifex** [ref]: AI agent orchestrator — delegates coding tasks to free tools (Gemini/Codex/OpenCode) with auto-routing, fallback chains,
- **overnight**: Check async queue results and manage tasks. 'overnight', 'overnight results', 'queue status', 'what ran
- **polarization**: Agent teams or single-task async dispatch. "overnight", "run tonight
- **quies**: Evening wind-down ritual — brain dump, overnight queue, screens-off gate. NOT for work closure (use eow) or daily reflec (calls: sched, sopor)
- **rector** [ref]: RETIRED -- merged into /mitogen. Use /mitogen for all dispatch.
- **solutions** [ref]: Search docs/solutions/ for past learnings before starting work. Use proactively before implementing fixes, filling forms
- **specification**: RETIRED — use /centrosome. Write specs, dispatch, review.
- **transcription**: Collaborative design before building — one question at a time. "let's build

### Finance

- **fiscus**: Monthly credit card and bank statement review. Parses PDF statements, checks recurring charges against baseline, flags a
- **praeco**: Monitor HK financial regulatory circulars (HKMA + SFC + IA). Use when checking for new circulars, running praeco, or to
- **stips**: Check OpenRouter credits and usage. Use when user says "stips", "openrouter credits", "or credits", or consilium returns

### Health

- **biomorphe**: Cell biology as agent design manual — 20 heuristics mined from immune, endocrine, metabolic, and ecosystem specimens. Co
- **daily**: Bedtime daily close (last thing before sleep). Full-day reflection and tomorrow preview. Use when user says "daily", "en
- **differentiation**: Coach a live gym session — prescribe sets, track reps, log workout. "gym
- **mappa** [ref]: Life areas diagnostic — maps Terry's key domains, healthy indicators, and neglect signals. Consulted by kairos, daily, e
- **salus**: Manulife health insurance claims checker CLI. Use when checking claim status, reimbursement amounts, or claim history. C
- **sopor** [ref]: Unified sleep health CLI — Oura Ring + EightSleep data in one DuckDB. Use when checking sleep data, running sync, asking

### Maintenance

- **adytum**: 1Password vault management CLI — migrate, save, hygiene, get, list items in the Agents vault. Use when managing 1Passwor
- **amicus**: Personal CRM CLI — relationship intelligence from Gmail + Calendar. Rust binary. Use when checking stale contacts, looki
- **assay** [ref]: Check for running experiments and probe their state
- **circadian**: Daily rhythm — morning brief, midday check, evening wrap. Auto-routes by time.
- **cron**: List all scheduled automation (LaunchAgents). Use when checking what's running automatically.
- **cytometry**: Classify subsystems as self-governing vs human-gated. "autonomy audit
- **docima** [ref]: AI agent memory benchmark — compare 10 backends on storage, retrieval, and drift. For benchmarking/analysis only, not ge
- **eow**: End-of-work checkpoint. Synthesise the work day, capture mood, note unfinished threads. NOT for session end (legatum) or
- **examen** [ref]: Premise audit — surface and test load-bearing assumptions before acting. Consult before delegating a large task, commit
- **histology**: Map organism structure, find gaps and anomalies. "architecture review", "system audit
- **hybridization**: Stress-test bio naming — find gaps where the analogy breaks down. "naming audit
- **kairos**: Any-time situational snapshot — what's actionable right now. Use when user says 'kairos', 'what now', 'what should I do'
- **legatum**: Session state transfer — bequeath volatile context to durable storage before session death. Learning capture, TODO sweep
- **mitosis**: Monthly review — parallel audits + cross-domain synthesis. "monthly
- **monthly**: Monthly maintenance — content digests, skill review, AI deep review, vault hygiene. Run on first Friday or anytime in th
- **pondus**: AI model benchmark aggregator CLI. Use when comparing models, checking benchmark scores, or looking up leaderboard ranki
- **priming** [ref]: Context-triggered reminders — check at session start and when entering matching context. Internal agent procedure, not u
- **prospective** [ref]: Context-triggered reminders — check at session start and when entering matching context. Internal agent procedure, not u
- **receptor**: Check goal readiness — find weakest categories, run drills. "drill", "readiness
- **scrutor**: Code audit using Codex, OpenCode, or consilium. Use when reviewing code for bugs, security issues, or logic errors. (calls: mitogen, consilium)
- **skill-review**: Monthly review of skills for staleness, drift, and gaps. Use on first Friday of month or when skills feel out of sync.
- **splicing**: Trim always-loaded context files for signal dilution. "genome trim", "coaching trim", "context audit
- **sporulation**: Save session checkpoint with codename for instant resume later. "checkpoint
- **theoria**: Automated AI landscape synthesis pipeline (LangGraph + Opus). Use when checking landscape run status, running manual rev
- **todo**: Manage TODO.md in the vault with time-based scheduling. Use when user says "todo", "add todo", "check todo", "done with"
- **usage**: Check Claude Code Max plan usage stats and token consumption. "usage
- **usus** [ref]: Check exact Claude Code Max plan usage limits (session %, weekly %, Sonnet %). Use when asked about usage, weekly limits

### Meta

- **bouleusis**: Planning theory reference — goal clarity, simulation depth, failure modes, when to stop. Consulted by planning workflows
- **censor** [ref]: Review client-facing deliverables (SOWs, proposals, decks, reports) against quality criteria before sending. NOT for cod
- **debridement**: Sweep skill names for violations and stale references. "naming sweep
- **derepression**: Extract tacit LLM knowledge into permanent reference skills. "mine knowledge
- **epistula**: Guided inbox triage — review Gmail with Terry, prioritise action items, archive noise. (calls: nuntius)
- **fasti**: Google Calendar CLI wrapper — list, move, create, delete events via fasti instead of raw gog commands
- **gist**: Create, update, and manage secret GitHub gists. Use when sharing code/text for mobile copy-paste, or when user says "gis
- **grapho** [ref]: Manage MEMORY.md — add entries, demote over-budget entries to overflow, promote back, review overflow, scaffold solution
- **kritike**: Key considerations when evaluating — metric selection, Goodhart traps, vanity vs diagnostic, LLM eval patterns. Reference
- **limen**: Generate Midjourney images from the terminal. Use when user wants to create images with Midjourney.
- **mandatum**: Key considerations when delegating — spec quality, decomposition depth, when ambiguity helps vs hurts. Reference skill c
- **maturation** [ref]: Review and edit a SKILL.md for quality — description, structure, triggers.
- **meiosis**: Quarterly review — direction, finances, career. Mar/Jun/Sep/Dec. "quarterly
- **morphogenesis**: Generate images via Gemini models. "generate image", "draw", "create image
- **obsidian-markdown**: Create and edit Obsidian Flavored Markdown with wikilinks, embeds, callouts, properties, and other Obsidian-specific syn
- **ontogenesis** [ref]: Design a new reusable skill from an ad-hoc solution. "create a skill
- **organogenesis**: Guide for designing skills (functional organs). Use when noticing a recurring pattern, wondering if something deserves a (has REFERENCE.md)
- **parsimonia**: Essential vs accidental complexity, premature abstraction, when removal is safe. Reference skill for code review, refact
- **peirasmos** [ref]: Theory of experimentation for AI/LLM engineering — question design, confound detection, dual-purpose runs, evaluation. R
- **photos**: Access iCloud Photos from Claude Code sessions. Reference skill — not user-invocable.
- **proliferation**: Overproduce skill variants for a domain; let selection pick. "proliferate
- **sched**: Schedule events and manage Due reminders via pacemaker CLI. Use for ANY Due or calendar operation: "schedule", "remind m
- **scrinium** [ref]: Route captured knowledge to the right storage layer — MEMORY.md, CLAUDE.md, docs/solutions/, vault, or skill. Consult be
- **synaxis**: Sync AI tool config across Claude Code, OpenCode, Codex, and Gemini CLI — skills, MCP, CE, from ~/officina/ as source of
- **tecton** [ref]: Reference for vault note structure — atomicity, interlinking, hub vs. detail, when to split, where notes live. Not user-

### Other

- **askesis**: Growth-mode sessions — ask Terry's view before offering mine, across any domain. Use when Terry explicitly wants to stay
- **assay-source**: Evaluate which web scraping tool works best for a new content source. Runs Jina/Defuddle/Firecrawl comparison on signal/
- **auscultation**: Passive log listening — spot error patterns and timing anomalies.
- **autophagy**: Coach mode — Terry states position, I push back. "/autophagy", "coach me
- **autopoiesis** [ref]: Self-repair loop — detect organism gaps, fix, learn from the fix. "self-repair
- **certus**: Accountability gate before high-stakes submission — self-critique under simulated rejection. Use before declaring delive
- **conjugation**: Borrow patterns from one system to improve another. "conjugation", "borrow
- **contract**: Manage session contracts — upfront acceptance criteria enforced before session ends. Use when starting non-trivial tasks
- **custodia**: Reference for persistence layer decisions — when to save, where, how many layers. Consult from wrap Step 4, scrinium, or
- **cytokinesis**: Capture session learnings before context is lost. "wrap up", "end of session
- **deleo**: Safe deletion CLI — validates paths and performs deletion with confirmation. Replaces safe_rm.py.
- **endosymbiosis**: Integrate an external tool as a first-class organelle. "absorb
- **evaluate-ai-repo**: Evaluate AI tooling repos (configs, MCP servers, agent frameworks) for adoption into existing setup.
- **gnome**: Capture structured decisions with past-decision surfacing (bouncer pattern). Use when user says "gnome", "/gnome", "I ne (calls: qmd, judex, consilium)
- **hemostasis**: Emergency stop — halt bleeding, don't fix root cause. "stop the bleeding
- **hkicpa**: Reference for HKICPA portal access and CPD compliance. Use when working with CPD submissions or HKICPA portal tasks.
- **hygroreception**: HK Observatory one-line weather CLI. Use when user asks about weather, temperature, typhoon, or rain in HK. "weather", "
- **iter**: HK bus stop navigator — tracks stops on unfamiliar routes with alerts. Also does Google Maps transit directions. NOT for
- **judex** [ref]: Empirical validation over theoretical debate — when two approaches are plausible and measurable, run the experiment inst
- **lacuna** [ref]: Demo CLI for Lacuna regulatory gap analysis platform. Use when working on Lacuna demos, Railway deployment, or CLI wrap
- **lararium**: Vault-resident personalities CLI — persistent AI characters that live in the Obsidian vault, read notes, develop opinion
- **libra**: Run and manage the Libra AI use case tier classifier. Use when demoing to Simon, updating tiering rules, or running local
- **manus**: Reference for macOS UI automation via Peekaboo CLI. Not user-invocable — consult when automating app interactions, click
- **methylation**: Crystallize repair lessons into permanent probes and patterns. "crystallize
- **modification**: Refine artifact — multi-model or solo cooling. "refine", "polish", "anneal
- **phagocytosis**: Classify content, extract insights, save as chromatin note. URL or pasted text.
- **poros** [ref]: Query MTR (Hong Kong subway) point-to-point journey times. Use when asked how long the MTR takes between any two station
- **praecepta** [ref]: Heuristic library — simple action rules replacing per-case reasoning. Consult when deciding, advising, or a known patter
- **quorum**: Multi-model deliberation for judgment calls. "council", "ask llms (has REFERENCE.md)
- **taobao** [ref]: Reference for accessing Taobao/Tmall product pages and analysing products. Consult when user shares Taobao links.
- **tessera**: Authenticate a website for headless agent access — routes to headed login, porta (cookie bridge), or nodriver (stealth C
- **topica** [ref]: Mental models catalog — situational thinking lenses for decisions, evaluation, systems, and people. Consult from consili
- **transcription-factor**: Log structured decisions with bouncer pattern — surfaces past similar ones. (calls: consilium)
- **vectura**: Import Apple Passwords CSV exports into 1Password via the op CLI. Use when migrating passwords or catching new items save
- **verify** [ref]: Hard gate: run verification before claiming completion. Evidence before assertions. Applied automatically — not user-inv
- **video-digest** [ref]: Video/podcast URL to full transcript + structured digest. Bilibili, YouTube, Xiaoyuzhou, Apple Podcasts, X, direct audio

### Research

- **anam**: Search past chat history and AI coding memories. Use when recalling what was discussed, finding past decisions, or looki
- **auceps** [ref]: Smart wrapper for the bird X/Twitter CLI. Use instead of bare bird — auto-routes URLs, handles, and search; adds --vault
- **cardo**: Midday reflection — scan morning sessions for shipped work and loose ends, then set afternoon priorities. Use when user  (calls: kairos)
- **comes** [ref]: Personal AI life coach CLI (crate: phron). Health monitoring, morning brief, overnight research, proactive nudges. `come
- **consilium**: Multi-model deliberation for judgment calls — auto-routes by difficulty. Use for decisions, trade-offs, naming, strategy (has REFERENCE.md)
- **diagnosis**: Debugging as hypothesis-driven search — observation hierarchy, hypothesis discipline, when to abandon a theory. Reference
- **ecphory**: Recall prior-session data and decisions by cue. Not for new research.
- **elencho** [ref]: Parallel AI research — runs query through all search tools (Grok, Exa, noesis), synthesises agreements and disagreements (calls: grok, exauro, noesis, stips)
- **evolvo**: Scan Claude Code session JSONL to extract wrap outputs, compute multi-wrap rate, and sample output quality for monthly s
- **exauro**: Exa search API CLI — neural/semantic web search, find-similar, content extraction, AI answers. Use when WebSearch is too
- **indago** [ref]: Reference for searching information online — tool selection, search strategies, when to go deep vs quick, non-English se
- **integrin**: Scan CLI binaries and skills for breakage or dormancy. "health check
- **iris**: Email verification link relay — polls Gmail for verification emails, extracts the link, opens it in an agent-browser tab
- **linkedin-profile**: Manage Terry's LinkedIn profile — Featured links, About section, headline, announcements, job updates. NOT for researchi
- **linkedin-research** [ref]: Research OTHER people on LinkedIn — profile lookup, team mapping, org research. NOT for managing your own profile (use l
- **nauta** [ref]: Web browser automation — 3-tier escalation from headless to AppleScript. Covers agent-browser, cookie bridge, LinkedIn, 
- **nexis**: Obsidian vault link health — scan, triage broken links, surface orphans. Use when running nexis CLI or triaging vault li
- **nexum**: LinkedIn org research CLI — search people, extract profiles, traverse network graph. Use when researching org structures
- **nuntius**: Cora CLI — AI email assistant. Reading briefs, managing email todos, chatting with Cora, or searching email via the Cora
- **obsidian-cli**: Interact with Obsidian vaults using the Obsidian CLI to read, create, search, and manage notes, tasks, properties, and m
- **oghma**: oghma memory tool — search memories, check status, manage daemon. Use when user mentions oghma, memory search, or session
- **palpation**: Deep-probe a single component by hand — deeper than integrin scan. "deep probe
- **peira**: Autonomous experiment-optimize loop for any measurable target. Use when prompt engineering, habit tuning, performance be
- **pinocytosis** [ref]: Fetch web content with smart routing and fallback chain. "browse", "fetch URL
- **porta**: Bridge browser cookies (Chrome, Firefox, Arc) into agent-browser profile (solves Google OAuth block)
- **qianli**: Search Chinese content platforms (WeChat, 36kr, Zhihu, XHS) from the terminal. Use when searching for Chinese-language c
- **qmd** [ref]: Semantic search over the vault using QMD. For conceptual queries beyond literal grep.
- **specula**: Extract transferable patterns from competitors and peers. "peer scan
- **stealth-browser**: Last-resort Cloudflare bypass via Chrome cookies + playwright-extra stealth. Invoke after peruro fails or when authentic
- **summarize**: Fetch and summarize content from a URL, podcast, or local file. For "summarize this" queries. NOT for vault cataloguing 
- **trutina** [ref]: Conflicting evidence reconciliation — when sources disagree, reason about which to trust. Consult when research returns 
- **waking-up**: Waking Up meditation transcripts — catalog, transcribe, search, enrich. "waking up", "wu", "transcribe meditation
- **wechat-article** [ref]: Fetch and read WeChat public article content (mp.weixin.qq.com URLs). Use when needing to extract text from a WeChat art

### Workflow

- **dialexis**: Weekly and monthly AI landscape review for consulting conversations. Use when user says "ai review", "ai landscape", "wh
- **digest**: Monthly content digest — extract insights from YouTube channels and other sources. "digest", "monthly digest
- **expression**: Weekly consulting IP production — turn sparks into deliverable assets.
- **infradian**: Weekend review + plan — reflect on the week, plan the next. "weekly", "weekly review
- **melete**: Daily consulting readiness drill — scenarios, reading prompts, observation logging. "consulting prep", "prep drill", "co
- **weekly**: Weekly synthesis and review. Use when user says "weekly", "weekly review", "week in review", or on Fridays.

## Issues (74)

- auscultation: invocable but no trigger phrases or 'Use when' in description
- auspex: invocable but no trigger phrases or 'Use when' in description
- biomorphe: invocable but no trigger phrases or 'Use when' in description
- bouleusis: invocable but no trigger phrases or 'Use when' in description
- capco-prep: invocable but no trigger phrases or 'Use when' in description
- centrosome: invocable but no trigger phrases or 'Use when' in description
- chemoreception: invocable but no trigger phrases or 'Use when' in description
- circadian: invocable but no trigger phrases or 'Use when' in description
- consilium: invocable but no trigger phrases or 'Use when' in description
- custodia: invocable but no trigger phrases or 'Use when' in description
- cytometry: invocable but no trigger phrases or 'Use when' in description
- debridement: invocable but no trigger phrases or 'Use when' in description
- deleo: invocable but no trigger phrases or 'Use when' in description
- deltos: invocable but no trigger phrases or 'Use when' in description
- derepression: invocable but no trigger phrases or 'Use when' in description
- diagnosis: invocable but no trigger phrases or 'Use when' in description
- differentiation: invocable but no trigger phrases or 'Use when' in description
- ecphory: invocable but no trigger phrases or 'Use when' in description
- endosymbiosis: invocable but no trigger phrases or 'Use when' in description
- eow: invocable but no trigger phrases or 'Use when' in description
- epistula: invocable but no trigger phrases or 'Use when' in description
- evaluate-ai-repo: invocable but no trigger phrases or 'Use when' in description
- evolvo: invocable but no trigger phrases or 'Use when' in description
- exocytosis: invocable but no trigger phrases or 'Use when' in description
- expression: invocable but no trigger phrases or 'Use when' in description
- fasti: invocable but no trigger phrases or 'Use when' in description
- fiscus: invocable but no trigger phrases or 'Use when' in description
- hemostasis: invocable but no trigger phrases or 'Use when' in description
- hybridization: invocable but no trigger phrases or 'Use when' in description
- hypha: invocable but no trigger phrases or 'Use when' in description
- integrin: invocable but no trigger phrases or 'Use when' in description
- involution: invocable but no trigger phrases or 'Use when' in description
- iris: invocable but no trigger phrases or 'Use when' in description
- iter: invocable but no trigger phrases or 'Use when' in description
- keryx: invocable but no trigger phrases or 'Use when' in description
- kindle: invocable but no trigger phrases or 'Use when' in description
- kritike: invocable but no trigger phrases or 'Use when' in description
- legatus: invocable but no trigger phrases or 'Use when' in description
- linkedin-profile: invocable but no trigger phrases or 'Use when' in description
- mandatum: invocable but no trigger phrases or 'Use when' in description
- manus: invocable but no trigger phrases or 'Use when' in description
- meiosis: invocable but no trigger phrases or 'Use when' in description
- message: invocable but no trigger phrases or 'Use when' in description
- metabolize: invocable but no trigger phrases or 'Use when' in description
- methylation: invocable but no trigger phrases or 'Use when' in description
- mitosis: invocable but no trigger phrases or 'Use when' in description
- monthly: invocable but no trigger phrases or 'Use when' in description
- nuntius: invocable but no trigger phrases or 'Use when' in description
- opsonization: invocable but no trigger phrases or 'Use when' in description
- overnight: invocable but no trigger phrases or 'Use when' in description
- palpation: invocable but no trigger phrases or 'Use when' in description
- parsimonia: invocable but no trigger phrases or 'Use when' in description
- phagocytosis: invocable but no trigger phrases or 'Use when' in description
- photos: invocable but no trigger phrases or 'Use when' in description
- porta: invocable but no trigger phrases or 'Use when' in description
- presentation: invocable but no trigger phrases or 'Use when' in description
- proliferation: invocable but no trigger phrases or 'Use when' in description
- quies: invocable but no trigger phrases or 'Use when' in description
- redarguo: invocable but no trigger phrases or 'Use when' in description
- remote-llm: invocable but no trigger phrases or 'Use when' in description
- secretion: invocable but no trigger phrases or 'Use when' in description
- skill-review: invocable but no trigger phrases or 'Use when' in description
- specification: invocable but no trigger phrases or 'Use when' in description
- specula: invocable but no trigger phrases or 'Use when' in description
- sporulation: invocable but no trigger phrases or 'Use when' in description
- statio: invocable but no trigger phrases or 'Use when' in description
- stealth-browser: invocable but no trigger phrases or 'Use when' in description
- stilus: invocable but no trigger phrases or 'Use when' in description
- synaxis: invocable but no trigger phrases or 'Use when' in description
- taxis: invocable but no trigger phrases or 'Use when' in description
- tessera: invocable but no trigger phrases or 'Use when' in description
- transcription-factor: invocable but no trigger phrases or 'Use when' in description
- transcription: invocable but no trigger phrases or 'Use when' in description
- usage: invocable but no trigger phrases or 'Use when' in description

