#!/usr/bin/env python3
"""Epistemics linkage analyzer - maps skills to epistemics and reports titer data."""

import argparse
import re
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional

EPISTEMICS_DIR = Path.home() / "epigenome" / "chromatin" / "euchromatin" / "epistemics"
SKILLS_DIR = Path.home() / "germline" / "membrane" / "receptors"

def parse_frontmatter(content: str) -> Dict:
    """Parse YAML frontmatter from content using regex (no pyyaml dependency)."""
    frontmatter = {}
    # Look for situations: [tag1, tag2, ...] or situations: - tag1 ...
    # Initialize empty set
    frontmatter['situations'] = set()
    # First check for bracket format: situations: [a, b, c]
    match = re.search(r'situations\s*:\s*\[([^]]+)\]', content, re.IGNORECASE)
    if match:
        tags_str = match.group(1).strip()
        # Handle comma-separated in brackets
        tags = [t.strip().strip('"\'-') for t in tags_str.split(',') if t.strip()]
        for t in tags:
            frontmatter['situations'].add(t)
    else:
        # Check for any bullet points (format can be anything with - tag)
        bullet_matches = re.findall(r'^\s*-\s*(\w+)', content, re.MULTILINE)
        for tag in bullet_matches:
            frontmatter['situations'].add(tag.strip())
    
    # Look for titer-hits
    match = re.search(r'titer-hits\s*:\s*(\d+)', content, re.IGNORECASE)
    if match:
        frontmatter['titer-hits'] = int(match.group(1))
    else:
        frontmatter['titer-hits'] = 0
    
    # Look for titer-last-seen
    match = re.search(r'titer-last-seen\s*:\s*([\d-]+)', content, re.IGNORECASE)
    if match:
        frontmatter['titer-last-seen'] = match.group(1).strip()
    else:
        frontmatter['titer-last-seen'] = None
    
    return frontmatter

def extract_keywords(text: str) -> Set[str]:
    """Extract keywords from text by splitting on non-alphanumeric characters."""
    words = re.findall(r'[a-zA-Z]+', text.lower())
    return {word for word in words if len(word) > 3}

def load_epistemics() -> List[Dict]:
    """Load all epistemics from directory."""
    epistemics = []
    if not EPISTEMICS_DIR.exists():
        return epistemics
    
    for file_path in EPISTEMICS_DIR.glob('*.md'):
        content = file_path.read_text()
        frontmatter = parse_frontmatter(content)
        stem = file_path.stem
        stem_keywords = set(stem.lower().split('-'))
        frontmatter['file_path'] = file_path
        frontmatter['filename'] = file_path.name
        frontmatter['stem'] = stem
        frontmatter['stem_keywords'] = stem_keywords
        frontmatter['all_keywords'] = frontmatter['situations'].union(stem_keywords)
        epistemics.append(frontmatter)
    
    return epistemics

def load_skills() -> List[Dict]:
    """Load all skills from receptors directory."""
    skills = []
    if not SKILLS_DIR.exists():
        return skills
    
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / 'SKILL.md'
        if not skill_file.exists():
            continue
        
        content = skill_file.read_text()
        skill_name = skill_dir.name
        keywords = extract_keywords(skill_name)
        
        # Extract first heading
        first_heading = re.search(r'^#\s*(.+)$', content, re.MULTILINE)
        description = ''
        if first_heading:
            description = first_heading.group(1)
            keywords.update(extract_keywords(description))
        
        # Look for situations in skill frontmatter
        frontmatter = parse_frontmatter(content)
        if frontmatter['situations']:
            keywords.update(frontmatter['situations'])
        
        # Look for epistemics: tag
        match = re.search(r'epistemics\s*:\s*\[?(.*?)\]?\n', content, re.IGNORECASE)
        if match:
            eps = [t.strip().strip('"\'-') for t in match.group(1).split(',') if t.strip()]
            for ep in eps:
                keywords.add(ep.lower())
        
        # Add keywords from first paragraph
        first_para = re.split(r'\n\n+', content.lstrip(), maxsplit=1)
        if len(first_para) > 1:
            keywords.update(extract_keywords(first_para[1]))
        
        skills.append({
            'name': skill_name,
            'path': skill_file,
            'keywords': keywords,
            'situations': frontmatter['situations']
        })
    
    return skills

def match_skills_to_epistemics(skills: List[Dict], epistemics: List[Dict]) -> Dict[str, List[Tuple[Dict, int]]]:
    """Match skills to epistemics based on overlapping keywords."""
    matches = defaultdict(list)
    
    for skill in skills:
        skill_matches = []
        for epi in epistemics:
            score = 0
            # Check if any skill keyword is in epistemic situations
            overlap = skill['keywords'].intersection(epi['situations'])
            if overlap:
                score += len(overlap)
            
            # Check if any epistemic stem keyword is in skill keywords
            stem_overlap = epi['stem_keywords'].intersection(skill['keywords'])
            if stem_overlap:
                score += len(stem_overlap)
            
            if score > 0:
                skill_matches.append((epi, score))
        
        # Sort by score descending
        skill_matches.sort(key=lambda x: x[1], reverse=True)
        matches[skill['name']] = skill_matches
    
    return matches

def output_table(header: List[str], rows: List[List[str]]) -> None:
    """Print a simple formatted table."""
    # Calculate column widths
    widths = [max(len(str(cell)) for cell in col) for col in zip(header, *rows)]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*header))
    print(fmt.format(*['=' * w for w in widths]))
    for row in rows:
        print(fmt.format(*row))

def cmd_map(args: argparse.Namespace) -> None:
    """Generate static linkage map."""
    epistemics = load_epistemics()
    skills = load_skills()
    matches = match_skills_to_epistemics(skills, epistemics)
    
    header = ['Skill', 'Matched Epistemics (score)']
    rows = []
    
    for skill_name in sorted(matches.keys()):
        skill_matches = matches[skill_name]
        if skill_matches:
            epi_list = ', '.join(f"{epi['stem']} ({score})" for epi, score in skill_matches)
            rows.append([skill_name, epi_list])
    
    if not rows:
        print("No matches found.")
        return
    
    print("Skill → Epistemics Linkage Map\n")
    output_table(header, rows)

def cmd_orphans(args: argparse.Namespace) -> None:
    """Find orphan epistemics with no linkage."""
    epistemics = load_epistemics()
    skills = load_skills()
    matches = match_skills_to_epistemics(skills, epistemics)
    
    # Find all epistemics that are matched to at least one skill
    matched_epistemics = set()
    for skill_matches in matches.values():
        for epi, _ in skill_matches:
            matched_epistemics.add(epi['filename'])
    
    # Orphan categories
    no_linkage = []
    zero_titer = []
    
    for epi in epistemics:
        if epi['filename'] not in matched_epistemics:
            no_linkage.append(epi['filename'])
        if epi['titer-hits'] == 0:
            zero_titer.append(epi['filename'])
    
    skills_no_match = []
    for skill_name, skill_matches in matches.items():
        if not skill_matches:
            skills_no_match.append(skill_name)
    
    print("Orphan Report\n")
    
    print(f"\nEpistemics with no skill linkage ({len(no_linkage)}):")
    if no_linkage:
        for f in sorted(no_linkage):
            print(f"  - {f}")
    else:
        print("  None")
    
    print(f"\nEpistemics with zero titer hits ({len(zero_titer)}):")
    if zero_titer:
        for f in sorted(zero_titer):
            print(f"  - {f}")
    else:
        print("  None")
    
    print(f"\nSkills with no matching epistemics ({len(skills_no_match)}):")
    if skills_no_match:
        for s in sorted(skills_no_match):
            print(f"  - {s}")
    else:
        print("  None")

def cmd_titer(args: argparse.Namespace) -> None:
    """Report titer heat map."""
    epistemics = load_epistemics()
    today = datetime.now().date()
    threshold_days = 30
    
    # Sort by titer-hits descending
    sorted_epis = sorted(epistemics, key=lambda x: x['titer-hits'], reverse=True)
    
    header = ['Epistemic', 'Titer Hits', 'Last Seen', 'Status']
    rows = []
    
    for epi in sorted_epis:
        status = []
        if epi['titer-hits'] == 0:
            status.append('COLD')
        
        days_ago = None
        if epi['titer-last-seen']:
            try:
                last_seen = datetime.strptime(epi['titer-last-seen'], '%Y-%m-%d').date()
                days_ago = (today - last_seen).days
                if days_ago > threshold_days:
                    status.append(f'SALE ({days_ago}d)')
                else:
                    status.append(f'FRESH ({days_ago}d)')
            except ValueError:
                status.append('INVALID_DATE')
        else:
            last_seen = None
        
        row = [
            epi['filename'],
            str(epi['titer-hits']),
            epi['titer-last-seen'] or 'NEVER',
            ' / '.join(status) or 'OK'
        ]
        rows.append(row)
    
    print("Titer Report (sorted by hits descending)\n")
    output_table(header, rows)

def cmd_report(args: argparse.Namespace) -> None:
    """Generate combined report."""
    import sys
    original_stdout = sys.stdout
    
    if args.output:
        sys.stdout = open(args.output, 'w')
    
    print("EPISTEMICS LINKAGE ANALYZER COMBINED REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print("\n=== 1. LINKAGE MAP ===")
    cmd_map(args)
    
    print("\n\n=== 2. ORPHANS REPORT ===")
    cmd_orphans(args)
    
    print("\n\n=== 3. TITER REPORT ===")
    cmd_titer(args)
    
    if args.output:
        sys.stdout.close()
        sys.stdout = original_stdout
        print(f"Report written to {args.output}")

def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Epistemics linkage analyzer')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # map command
    map_parser = subparsers.add_parser('map', help='Static linkage analysis')
    
    # orphans command
    orphans_parser = subparsers.add_parser('orphans', help='Find orphan epistemics')
    
    # titer command
    titer_parser = subparsers.add_parser('titer', help='Titer heat map')
    
    # report command
    report_parser = subparsers.add_parser('report', help='Combined report')
    report_parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    if args.command == 'map':
        cmd_map(args)
    elif args.command == 'orphans':
        cmd_orphans(args)
    elif args.command == 'titer':
        cmd_titer(args)
    elif args.command == 'report':
        cmd_report(args)

if __name__ == '__main__':
    main()
