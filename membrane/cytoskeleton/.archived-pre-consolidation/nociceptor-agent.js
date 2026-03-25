#!/usr/bin/env node
// Blocks Agent calls on lookup subagent types if model != "haiku"
const chunks = [];
process.stdin.on('data', d => chunks.push(d));
process.stdin.on('end', () => {
  try {
    const input = JSON.parse(Buffer.concat(chunks).toString());
    const toolInput = input.tool_input || {};
    const subagentType = toolInput.subagent_type || '';
    const model = toolInput.model || '';

    const lookupTypes = ['general-purpose', 'scout', 'Explore'];

    if (lookupTypes.includes(subagentType) && model !== 'haiku') {
      process.stderr.write(
        `HAIKU GUARD: Agent('${subagentType}') must use model: "haiku". Add model: "haiku" to this Agent call.\n`
      );
      process.exit(2);
    }
    process.exit(0);
  } catch (_) {
    process.exit(0);
  }
});
