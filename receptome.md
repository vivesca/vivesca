# Receptome -- 2026-04-05 14:00

Total: **188** skills (144 invocable, 44 reference)
With REFERENCE.md: 3 | With scripts/: 0
Trigger phrases indexed: 246

## By Category

| Category | Count | Skills |
|----------|-------|--------|
| other | 39 | askesis, assay-source, autophagy, autopoiesis, certus, conjugation, consilium, contract +31 more |
| research | 31 | anam, auceps, cardo, comes, diagnosis, elencho, evolvo, exauro +23 more |
| maintenance | 30 | adytum, amicus, assay, auscultation, circadian, cron, cytometry, debridement +22 more |
| meta | 22 | bouleusis, censor, derepression, fasti, gist, grapho, kritike, limen +14 more |
| dispatch | 16 | agent-cli, centrosome, heuretes, involution, kindle, legatus, mitogen, motifs +8 more |
| content | 11 | adhesion, agoras, analyze, evaluate-job, exocytosis, message, python, rust +3 more |
| comms | 9 | cursus, deltos, endosomal, epistula, graphis, horizo, imessage, keryx +1 more |
| workflow | 7 | auspex, dialexis, digest, expression, infradian, melete, weekly |
| consulting | 7 | capco-prep, chemoreception, meeting-prep, metabolize, mora, opsonization, secretion |
| dev | 7 | etiology, fingo, friction, hypha, lucus, mandatum, remote-llm |
| health | 6 | biomorphe, daily, differentiation, mappa, salus, sopor |
| finance | 3 | fiscus, praeco, stips |

## Size Distribution

- Stubs (<20 lines): 3
- Small (20-99): 108
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

### Comms

- **cursus** [ref]: Career communication principles — reference skill consulted by message, meeting-prep, capco-prep. Not user-invocable.
- **deltos**: Send text/code snippets or image files to Telegram for mobile copy-paste. Use when relaying content to phone. "send to t
- **endosomal**: Triage email — classify, archive noise, extract action items. "email", "inbox
- **epistula**: Guided inbox triage — review Gmail with Terry, prioritise action items, archive noise. \"email triage\", \"review inbox\ (calls: nuntius)
- **graphis** [ref]: Manage Telegram bots — create, delete, list, start-bot via BotFather. Use when creating a new bot, retiring an old one, 
- **horizo**: Appointment scheduling workflow — coordinate time via WhatsApp (keryx) then book to Google Calendar (gog). Use when sche
- **imessage**: Send iMessages via CLI. Use when user wants to text wife or send an iMessage to someone.
- **keryx**: WhatsApp CLI wrapper — contact name resolution, conversation merging, daemon-aware send. Use when sending or reading Wha
- **nuntius**: Cora CLI — AI email assistant. Reading briefs, managing email todos, chatting with Cora. \"cora\", \"email brief\", \"em

### Consulting

- **capco-prep**: Capco onboarding readiness — drill, brief, or event-specific prep. \"capco prep\", \"capco drill\", \"capco brief\
- **chemoreception**: AI briefing on demand — refresh stale context before a meeting or decision. "what's happening in AI", "AI briefing", "AI
- **meeting-prep**: Drill for upcoming meetings with scenario-based questions. "meeting prep", "prep for meeting", "prep for coffee
- **metabolize**: Process articles through Capco consulting lens — extract, write insight cards. "metabolize", "process articles", "what c
- **mora**: Surface productive low-energy tasks when you have downtime. Use when energy is low, between meetings, or during idle mom
- **opsonization**: Drill for upcoming meetings or interviews with scenario practice. "meeting prep", "prep for meeting", "prep for intervie
- **secretion**: Package and release a consulting deliverable — quality-gate, format, ship. Use when a report, deck, or memo is ready for

### Content

- **adhesion**: Evaluate LinkedIn job postings for fit — job URL or "evaluate this role".
- **agoras**: Draft LinkedIn comments and posts. Use when user shares a LinkedIn URL to comment on, says "linkedin comment", "linkedin
- **analyze**: Classify content, extract insights, and save a structured vault note. Use when user shares content (article, job posting
- **evaluate-job**: Evaluate LinkedIn job postings for fit. Triggers on job URLs or "evaluate this role".
- **exocytosis**: Publish to terryli.hm garden. Secretome -> Astro -> deploy. "garden post", "new post", "publish post", "blog post"
- **message**: Draft responses to recruiter and networking messages (LinkedIn DMs, WhatsApp intros, cold outreach). "reply to recruiter
- **python**: Python development — new script/package scaffold, uv workflow, PyPI publish checklist. Use when starting or publishing P
- **rust**: Rust CLI development — new project scaffold, daily dev workflow, pre-publish checklist. Use when starting or publishing 
- **speculor**: Daily LinkedIn job alert collector and AI triage tool. Use when checking job alerts, running triage, or troubleshooting 
- **stilus**: Gmail operations via gog CLI — inbox triage, send/reply, archive, batch modify, drafts. "send email", "check inbox", "re
- **theoros**: LinkedIn daily feed digest. Run manually or check today's digest. Use when asking about recent LinkedIn activity, job le

### Dev

- **etiology**: Root-cause diagnosis for bugs and process failures. "broken", "debug
- **fingo**: Rust CLI for AI image generation and editing via Gemini. Use when generating or editing images from the terminal.
- **friction**: Capture friction moments during work. Use when the user says "friction", types "/friction", or explicitly flags frustrat
- **hypha**: Obsidian vault link graph traversal — navigate links from a note, explore to depth N, find shortest path. \"trace links\
- **lucus** [ref]: Git worktree manager for parallel AI agent sessions. Use when starting a new feature/fix that needs isolation from other
- **mandatum**: Delegation theory — spec quality, decomposition depth, when ambiguity helps vs hurts. Use when writing delegate specs or
- **remote-llm**: Craft prompts for local/work LLMs when code can't be shared directly. Use when helping with proprietary code via a relay

### Dispatch

- **agent-cli** [ref]: Design patterns for CLIs intended to be used by AI agents rather than humans. Consult when building a new CLI that Claud
- **centrosome** [ref]: RETIRED — merged into /mitogen. Use /mitogen for all dispatch.
- **heuretes**: Agent research org — run a hierarchical team of AI agents on open-ended research or exploration tasks. Chief orchestrato
- **involution**: Evening wind-down — brain dump, queue overnight tasks, gate screens-off. "wind down", "bedtime", "brain dump", "shutdown (calls: sporulation, sopor)
- **kindle**: Extract Kindle books to markdown via screenshots + Gemini vision. "kindle extract", "extract book", "kindle queue
- **legatus**: Session-independent AI agent dispatcher — list, dispatch, cancel, view results. Use when running background AI jobs deta
- **mitogen**: Dispatch ribosome for any build task — bulk campaigns or single features. "build", "implement", "dispatch", "go build", 
- **motifs** [ref]: Shared skill patterns — conserved mechanisms reused across many skills. Consult when building or reviewing skills. "shar
- **opifex** [ref]: AI agent orchestrator — delegates coding tasks to free tools (Gemini/Codex/OpenCode) with auto-routing, fallback chains,
- **overnight**: Check async queue results and manage tasks. \"overnight\", \"overnight results\", \"queue status\", \"what ran\
- **polarization**: Agent teams or single-task async dispatch. "overnight", "run tonight
- **quies**: Evening wind-down ritual — brain dump, overnight queue, screens-off gate. "quies", "wind down", "bedtime", "screens off" (calls: sched, sopor)
- **rector** [ref]: RETIRED -- merged into /mitogen. Use /mitogen for all dispatch.
- **solutions** [ref]: Search docs/solutions/ for past learnings before starting work. Use proactively before implementing fixes, filling forms
- **specification** [ref]: RETIRED — use /centrosome. Write specs, dispatch, review.
- **transcription**: Collaborative design before building — one question at a time. "let's build", "I want to add", "design first

### Finance

- **fiscus**: Monthly credit card and bank statement review. Use when processing statements or checking recurring charges. "check stat
- **praeco**: Monitor HK financial regulatory circulars (HKMA + SFC + IA). Use when checking for new circulars, running praeco, or tro
- **stips**: Check OpenRouter credits and usage. Use when user says "stips", "openrouter credits", "or credits", or consilium returns

### Health

- **biomorphe**: Cell biology as agent design manual — 20 heuristics. Use when designing agent architecture or evaluating system health. 
- **daily**: Bedtime daily close (last thing before sleep). Full-day reflection and tomorrow preview. Use when user says "daily", "en
- **differentiation**: Coach a live gym session — prescribe sets, track reps, log workout. "gym", "workout", "gym session
- **mappa** [ref]: Life areas diagnostic — maps Terry's key domains, healthy indicators, and neglect signals. Consulted by kairos, daily, e
- **salus**: Manulife health insurance claims checker CLI. Use when checking claim status, reimbursement amounts, or claim history. C
- **sopor** [ref]: Unified sleep health CLI — Oura Ring + EightSleep data in one DuckDB. Use when checking sleep data, running sync, asking

### Maintenance

- **adytum**: 1Password vault management CLI — migrate, save, hygiene, get, list items in the Agents vault. Use when managing 1Passwor
- **amicus**: Personal CRM CLI — relationship intelligence from Gmail + Calendar. Rust binary. Use when checking stale contacts, looki
- **assay** [ref]: Check for running experiments and probe their state
- **auscultation**: Passive log listening — spot error patterns and timing anomalies. Use when something feels off but no single error is vi
- **circadian**: Daily rhythm — morning brief, midday check, evening wrap. Auto-routes by time. "what now", "what's next", "morning brief
- **cron**: List all scheduled automation (LaunchAgents). Use when checking what's running automatically.
- **cytometry**: Classify subsystems as self-governing vs human-gated. Use when auditing which components need human approval. "autonomy 
- **debridement**: Sweep skill names for violations and stale references. Use when checking bio naming compliance. "naming sweep", "name au
- **docima** [ref]: AI agent memory benchmark — compare 10 backends on storage, retrieval, and drift. For benchmarking/analysis only, not ge
- **eow**: End-of-work checkpoint. Synthesise the work day, capture mood, note unfinished threads. \"eow\", \"end of work\", \"done
- **examen** [ref]: Premise audit — surface and test load-bearing assumptions before acting. Consult before delegating a large task, committ
- **histology**: Map organism structure, find gaps and anomalies. "architecture review", "system audit
- **hybridization**: Stress-test bio naming — find gaps where the analogy breaks down. Use when checking if a bio name fits its mechanism. "n
- **kairos**: Any-time situational snapshot — what's actionable right now. Use when user says 'kairos', 'what now', 'what should I do'
- **legatum**: Session state transfer — bequeath volatile context to durable storage before session death. Learning capture, TODO sweep
- **mitosis**: Monthly review — parallel audits + cross-domain synthesis. "monthly review", "monthly audit", "mitosis
- **monthly**: Monthly maintenance — content digests, skill review, AI deep review, vault hygiene. "monthly", "monthly maintenance", "r
- **photos**: Access iCloud Photos from Claude Code sessions. Use when checking recent photos, viewing a photo, or exporting images. "
- **pondus**: AI model benchmark aggregator CLI. Use when comparing models, checking benchmark scores, or looking up leaderboard ranki
- **priming** [ref]: Context-triggered reminders — check at session start and when entering matching context. Internal agent procedure, not u
- **prospective** [ref]: Context-triggered reminders — check at session start and when entering matching context. Internal agent procedure, not u
- **receptor**: Check goal readiness — find weakest categories, run drills. "drill", "readiness
- **scrutor**: Code audit using Codex, OpenCode, or consilium. Use when reviewing code for bugs, security issues, or logic errors. (calls: mitogen, consilium)
- **skill-review**: Monthly review of skills for staleness, drift, and gaps. Use when skills feel out of sync or on first Friday of month. "
- **splicing**: Trim always-loaded context files for signal dilution. "genome trim", "coaching trim", "context audit
- **sporulation**: Save session checkpoint with codename for instant resume later. "checkpoint", "save session", "sporulate
- **theoria**: Automated AI landscape synthesis pipeline (LangGraph + Opus). Use when checking landscape run status, running manual rev
- **todo**: Manage TODO.md in the vault with time-based scheduling. Use when user says "todo", "add todo", "check todo", "done with"
- **usage**: Check Claude Code Max plan usage stats and token consumption. "usage", "token usage", "how much have I used", "quota
- **usus** [ref]: Check exact Claude Code Max plan usage limits (session %, weekly %, Sonnet %). Use when asked about usage, weekly limits

### Meta

- **bouleusis**: Planning theory reference — goal clarity, simulation depth, failure modes. Use when designing planning workflows or debu
- **censor** [ref]: Review client-facing deliverables (SOWs, proposals, decks, reports) against quality criteria before sending. NOT for cod
- **derepression**: Extract tacit LLM knowledge into permanent reference skills. Use when capturing implicit model expertise. "mine knowledg
- **fasti**: Google Calendar CLI wrapper — list, move, create, delete events. Use when managing calendar events. "calendar list", "cr
- **gist**: Create, update, and manage secret GitHub gists. Use when sharing code/text for mobile copy-paste, or when user says "gis
- **grapho** [ref]: Manage MEMORY.md — add entries, demote over-budget entries to overflow, promote back, review overflow, scaffold solution
- **kritike**: Evaluation theory — metric selection, Goodhart traps, vanity vs diagnostic. Use when designing metrics or reviewing eval
- **limen**: Generate Midjourney images from the terminal. Use when user wants to create images with Midjourney.
- **maturation** [ref]: Review and edit a SKILL.md for quality — description, structure, triggers.
- **meiosis**: Quarterly review — direction, finances, career. Mar/Jun/Sep/Dec. "quarterly", "quarterly review", "q1 review
- **morphogenesis**: Generate images via Gemini models. "generate image", "draw", "create image
- **obsidian-markdown**: Create and edit Obsidian Flavored Markdown with wikilinks, embeds, callouts, properties, and other Obsidian-specific syn
- **ontogenesis** [ref]: Design a new reusable skill from an ad-hoc solution. "create a skill
- **organogenesis**: Guide for designing skills (functional organs). Use when noticing a recurring pattern, wondering if something deserves a (has REFERENCE.md)
- **parsimonia**: Simplification theory — essential vs accidental complexity, premature abstraction, when removal is safe. Use when refact
- **peirasmos** [ref]: Theory of experimentation for AI/LLM engineering — question design, confound detection, dual-purpose runs, evaluation. R
- **proliferation**: Overproduce skill variants for a domain; let selection pick. Use when entering a new domain and need many skills fast. "
- **sched**: Schedule events and manage Due reminders via pacemaker CLI. Use for ANY Due or calendar operation: "schedule", "remind m
- **scrinium** [ref]: Route captured knowledge to the right storage layer — MEMORY.md, CLAUDE.md, docs/solutions/, vault, or skill. Consult be
- **synaxis**: Sync AI tool config across Claude Code, OpenCode, Codex, and Gemini CLI. Use when config has changed and needs propagati
- **taxis**: Architecture of the Claude Code enforcement and knowledge system. Use when adding hooks, rules, or deciding where knowle
- **tecton** [ref]: Reference for vault note structure — atomicity, interlinking, hub vs. detail, when to split, where notes live. Not user-

### Other

- **askesis**: Growth-mode sessions — ask Terry's view before offering mine, across any domain. Use when Terry explicitly wants to stay
- **assay-source**: Evaluate which web scraping tool works best for a new content source. Runs Jina/Defuddle/Firecrawl comparison on signal/
- **autophagy**: Coach mode — Terry states position, I push back. "/autophagy", "coach me
- **autopoiesis** [ref]: Self-repair loop — detect organism gaps, fix, learn from the fix. "self-repair
- **certus**: Accountability gate before high-stakes submission — self-critique under simulated rejection. Use before declaring delive
- **conjugation**: Borrow patterns from one system to improve another. "conjugation", "borrow
- **consilium**: Multi-model deliberation for judgment calls — auto-routes by difficulty. Use when deciding trade-offs, naming, or strate (has REFERENCE.md)
- **contract**: Manage session contracts — upfront acceptance criteria enforced before session ends. Use when starting non-trivial tasks
- **custodia**: Reference for persistence layer decisions. Use when deciding where to save an insight or how many storage layers to use.
- **cytokinesis**: Capture session learnings before context is lost. "wrap up", "end of session
- **deleo**: Safe deletion CLI — validates paths and performs deletion with confirmation. Use when deleting files or directories safe
- **ecphory**: Recall prior-session data and decisions by cue. Use when looking up past decisions or session history. "we talked about"
- **endosymbiosis**: Integrate an external tool as a first-class organelle. Use when absorbing a new CLI or service into the organism. "absor
- **evaluate-ai-repo**: Evaluate AI tooling repos (configs, MCP servers, agent frameworks) for adoption. Use when deciding "should I adopt this?
- **gnome**: Capture structured decisions with past-decision surfacing (bouncer pattern). Use when user says "gnome", "/gnome", "I ne (calls: qmd, judex, consilium)
- **hemostasis**: Emergency stop — halt bleeding, don't fix root cause. Use when a process is cascading failures or burning resources. "st
- **hkicpa**: Reference for HKICPA portal access and CPD compliance. Use when working with CPD submissions or HKICPA portal tasks.
- **hygroreception**: HK Observatory one-line weather CLI. Use when user asks about weather, temperature, typhoon, or rain in HK. "weather", "
- **iter**: HK bus stop navigator — tracks stops on unfamiliar routes with alerts. Also does transit directions. \"bus route\", \"wh
- **judex** [ref]: Empirical validation over theoretical debate — when two approaches are plausible and measurable, run the experiment inst
- **lacuna** [ref]: Demo CLI for Lacuna regulatory gap analysis platform. Use when working on Lacuna demos, Railway deployment, or CLI wrapp
- **lararium**: Vault-resident personalities CLI — persistent AI characters that live in the Obsidian vault, read notes, develop opinion
- **libra**: Run and manage the Libra AI use case tier classifier. Use when demoing to Simon, updating tiering rules, or running loca
- **manus**: Reference for macOS UI automation via Peekaboo CLI. Use when automating app interactions, clicking UI elements, or takin
- **methylation**: Crystallize repair lessons into permanent probes and patterns. Use when turning recurring fixes into permanent capabilit
- **modification**: Refine artifact — multi-model or solo cooling. "refine", "polish", "anneal
- **phagocytosis**: Classify content, extract insights, save as chromatin note. Use when user shares a URL or text to catalog. "analyze this
- **poros** [ref]: Query MTR (Hong Kong subway) point-to-point journey times. Use when asked how long the MTR takes between any two station
- **praecepta** [ref]: Heuristic library — simple action rules replacing per-case reasoning. Consult when deciding, advising, or a known patter
- **presentation**: Visual communication patterns for presentations and data storytelling. Use when creating slides, infographics, or data v
- **quorum**: Multi-model deliberation for judgment calls. "council", "ask llms (has REFERENCE.md)
- **redarguo**: One-line adversarial challenge via a different LLM. Use when stakes are high and agreement feels too easy. \"challenge t
- **statio**: Start-of-work brief — priorities, gates, inbox triage. Use when sitting down to work. "statio", "start of work", "work b
- **taobao** [ref]: Reference for accessing Taobao/Tmall product pages and analysing products. Consult when user shares Taobao links.
- **topica** [ref]: Mental models catalog — situational thinking lenses for decisions, evaluation, systems, and people. Consult from consili
- **transcription-factor**: Log structured decisions with bouncer pattern — surfaces past similar ones. "I need to decide", "log decision", "gnome (calls: consilium)
- **vectura**: Import Apple Passwords CSV exports into 1Password via the op CLI. Use when migrating passwords or catching new items sav
- **verify** [ref]: Hard gate: run verification before claiming completion. Evidence before assertions. Applied automatically — not user-inv
- **video-digest** [ref]: Video/podcast URL to full transcript + structured digest. Bilibili, YouTube, Xiaoyuzhou, Apple Podcasts, X, direct audio

### Research

- **anam**: Search past chat history and AI coding memories. Use when recalling what was discussed, finding past decisions, or looki
- **auceps** [ref]: Smart wrapper for the bird X/Twitter CLI. Use instead of bare bird — auto-routes URLs, handles, and search; adds --vault
- **cardo**: Midday reflection — scan morning sessions for shipped work and loose ends, then set afternoon priorities. Use when user  (calls: kairos)
- **comes** [ref]: Personal AI life coach CLI (crate: phron). Health monitoring, morning brief, overnight research, proactive nudges. `come
- **diagnosis**: Debugging as hypothesis-driven search — observation hierarchy, hypothesis discipline. Use when debugging gets stuck or r
- **elencho** [ref]: Parallel AI research — runs query through all search tools (Grok, Exa, noesis), synthesises agreements and disagreements (calls: grok, exauro, noesis, stips)
- **evolvo**: Scan Claude Code session JSONL to extract wrap outputs and compute quality stats. Use when reviewing session output qual
- **exauro**: Exa search API CLI — neural/semantic web search, find-similar, content extraction, AI answers. Use when WebSearch is too
- **indago** [ref]: Reference for searching information online — tool selection, search strategies, when to go deep vs quick, non-English se
- **integrin**: Scan CLI binaries and skills for breakage or dormancy. Use when verifying tools still work. "health check", "check skill
- **iris**: Email verification link relay — polls Gmail for verification emails, extracts the link, opens it in agent-browser. Use w
- **linkedin-profile**: Manage Terry's LinkedIn profile — Featured links, About section, headline, announcements. "update my LinkedIn", "LinkedI
- **linkedin-research** [ref]: Research OTHER people on LinkedIn — profile lookup, team mapping, org research. NOT for managing your own profile (use l
- **nauta** [ref]: Web browser automation — 3-tier escalation from headless to AppleScript. Covers agent-browser, cookie bridge, LinkedIn, 
- **nexis**: Obsidian vault link health — scan, triage broken links, surface orphans. Use when running nexis CLI or triaging vault li
- **nexum**: LinkedIn org research CLI — search people, extract profiles, traverse network graph. Use when researching org structures
- **obsidian-cli**: Interact with Obsidian vaults using the Obsidian CLI to read, create, search, and manage notes, tasks, properties, and m
- **oghma**: oghma memory tool — search memories, check status, manage daemon. Use when user mentions oghma, memory search, or sessio
- **palpation**: Deep-probe a single component by hand — deeper than integrin scan. Use when a specific subsystem needs manual investigat
- **peira**: Autonomous experiment-optimize loop for any measurable target. Use when prompt engineering, habit tuning, performance be
- **pinocytosis** [ref]: Fetch web content with smart routing and fallback chain. "browse", "fetch URL
- **porta**: Bridge browser cookies into agent-browser profile (solves Google OAuth block). Use when agent-browser needs authenticate
- **qianli**: Search Chinese content platforms (WeChat, 36kr, Zhihu, XHS) from the terminal. Use when searching for Chinese-language c
- **qmd** [ref]: Semantic search over the vault using QMD. For conceptual queries beyond literal grep.
- **specula**: Extract transferable patterns from competitors and peers. Use when entering a new domain or checking what peers are doin
- **stealth-browser**: Last-resort Cloudflare bypass via Chrome cookies + playwright-extra stealth. Use when peruro fails or authenticated brow
- **summarize**: Fetch and summarize content from a URL, podcast, or local file. For "summarize this" queries. NOT for vault cataloguing 
- **tessera**: Authenticate a website for headless agent access — routes to headed login, porta, or stealth Chrome. "browser login", "s
- **trutina** [ref]: Conflicting evidence reconciliation — when sources disagree, reason about which to trust. Consult when research returns 
- **waking-up**: Waking Up meditation transcripts — catalog, transcribe, search, enrich. "waking up", "wu", "transcribe meditation
- **wechat-article** [ref]: Fetch and read WeChat public article content (mp.weixin.qq.com URLs). Use when needing to extract text from a WeChat art

### Workflow

- **auspex**: Wake-up brief — weather, calendar, key deadlines today. Use when waking up. "morning brief", "wake-up brief", "auspex
- **dialexis**: Weekly and monthly AI landscape review for consulting conversations. Use when user says "ai review", "ai landscape", "wh
- **digest**: Monthly content digest — extract insights from YouTube channels and other sources. "digest", "monthly digest
- **expression**: Weekly consulting IP production — turn sparks into deliverable assets. "weekly IP", "forge", "produce assets
- **infradian**: Weekend review + plan — reflect on the week, plan the next. "weekly", "weekly review
- **melete**: Daily consulting readiness drill — scenarios, reading prompts, observation logging. "consulting prep", "prep drill", "co
- **weekly**: Weekly synthesis and review. Use when user says "weekly", "weekly review", "week in review", or on Fridays.

