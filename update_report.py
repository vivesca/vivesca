import json

with open('audit_data.json', 'r') as f:
    data = json.load(f)

skills = data['skills']
agents = data['agents']

skill_overlaps = {
    'centrosome': 'kinesin',
    'kinesin': 'centrosome',
    'metabolize': 'phagocytosis',
    'phagocytosis': 'metabolize',
    'proofreading': 'autophagy',
    'autophagy': 'proofreading',
    'specula': 'competitor-watch (agent)',
    'replication': 'research (agent)'
}

agent_overlaps = {
    'competitor-watch': 'specula (skill)',
    'peer-scan': 'specula (skill)',
    'research': 'replication (skill)',
    'receptor-health': 'integrin (skill)',
    'praxis-sweep': 'ecdysis (skill)'
}

dead_paths_map = {
    'what-if': ['~/germline/DESIGN.md', '~/germline/genotype.md', '~/germline/membrane/cytoskeleton/'],
    'system-patrol': ['~/.claude/agents/'],
    'skill-drift': ['~/.claude/agents/', '~/.claude/skills/']
}

report = []
report.append("# Audit all skills and agents\n")

report.append("## Part 1: Skill audit\n")
report.append("| Skill | context | description length | has agent: | overlap with | issues |")
report.append("|---|---|---|---|---|---|")

for s in skills:
    name = s['name']
    ctx = s['context']
    desc = s['description']
    agent = s.get('agent', '')
    
    desc_len = len(desc)
    
    issues = []
    if desc_len > 80:
        issues.append(f"Desc > 80 chars ({desc_len})")
    
    # Strictly checking if it says when NOT to trigger
    lower_desc = desc.lower()
    if "not " not in lower_desc and "never " not in lower_desc and "don't " not in lower_desc:
        issues.append("Missing NOT trigger")
    
    if ctx == "fork" and not agent:
        issues.append("fork missing agent:")
        
    if "review" in name or "audit" in name:
        if ctx != "fork":
            issues.append("Missing context: fork")
            
    overlap = skill_overlaps.get(name, "")
    issue_str = ", ".join(issues) if issues else "None"
    
    report.append(f"| {name} | {ctx or 'inline'} | {desc_len} | {'Yes' if agent else 'No'} | {overlap} | {issue_str} |")

report.append("\n## Part 2: Agent audit\n")
report.append("| Agent | model | tools count | valid paths | overlap with skill | issues |")
report.append("|---|---|---|---|---|---|")

for a in agents:
    name = a['name']
    model = a['model']
    
    try:
        tools = json.loads(a['raw_tools']) if a['raw_tools'] else []
    except:
        tools = []
    
    tools_count = len(tools)
    
    overlap = agent_overlaps.get(name, "")
    
    issues = []
    if model == "opus":
        issues.append("Uses opus (consider sonnet)")
    elif model == "sonnet" and tools_count <= 2:
        issues.append("Uses sonnet for simple task (consider haiku)")
        
    dead_paths = dead_paths_map.get(name, [])
    valid_paths = "No" if dead_paths else "Yes"
    if dead_paths:
        issues.append(f"Dead paths: {', '.join(dead_paths)}")
        
    issue_str = ", ".join(issues) if issues else "None"
    
    report.append(f"| {name} | {model} | {tools_count} | {valid_paths} | {overlap} | {issue_str} |")

report.append("\n## Part 3: Recommendations\n")
report.append("""### Skills that should become agents
- **specula**: Heavily overlaps with `peer-scan` and `competitor-watch` agents. Should consolidate into a single boundary patrol agent.
- **replication**: Overlaps with `research` agent. Deep multi-step hierarchical research is better suited for an async agent rather than a skill.
- **karyotyping**: Layout components visually to spot structural anomalies. Deep system audits are better as agents.

### Skills with overlapping descriptions that need sharpening
- **centrosome vs kinesin**: Both dispatch and monitor tasks/agents. Need to clarify that centrosome is for *batch* worker droids, and kinesin is for async long-running agents.
- **metabolize vs phagocytosis**: Both process content. Clarify `metabolize` is strictly Capco consulting lens, `phagocytosis` is general insight extraction.
- **proofreading vs autophagy**: `proofreading` is for ideas, `autophagy` is for personal coaching/pushback. Should add clear "NOT for..." triggers to both to distinguish.

### Dead agents referencing non-existent paths
- **what-if**: References `~/germline/DESIGN.md` (should be `design.md`), `~/germline/genotype.md` (non-existent, maybe `genome.md`?), and `~/germline/membrane/cytoskeleton/` (non-existent).
- **system-patrol**: References `~/.claude/agents/` which is the old path structure.
- **skill-drift**: References `~/.claude/agents/` and `~/.claude/skills/` which are old path structures.

### Skills missing `context: fork` that do verbose exploration
- **integrin**: Scans binaries/skills, could be highly verbose.
- **ecphory**: Memory recall could be verbose if searching deep logs or many transcripts.
- **receptor**: Senses goal readiness and runs drills.

### Skills with `context: fork` that actually need session history
- **folding**: Executing an implementation plan usually requires knowing what was just discussed/planned in the session.
- **translation**: Turning design into a TDD plan needs the design context from the session.
- **morphogenesis**: Generating images might require previous context for consistency.
""")

with open('/Users/terry/germline/loci/plans/skill-agent-audit-report.md', 'w') as f:
    f.write("\n".join(report))
print("Report updated.")
