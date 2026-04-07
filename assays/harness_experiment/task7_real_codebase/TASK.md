# Task 7: Real Codebase Navigation

Read the file `~/germline/effectors/ribosome` (the organism's AI coding dispatch script).

Write a file called `analysis.json` with this exact structure:

```json
{
  "harnesses": ["list", "of", "supported", "harness", "names"],
  "backends": ["list", "of", "supported", "backend", "names"],
  "default_harness": "<default harness name>",
  "default_backend": "<default backend name>",
  "zhipu_anthropic_url": "<the ANTHROPIC_BASE_URL used for zhipu backend>",
  "coaching_mechanism": "<one sentence: how does coaching get injected into the prompt?>"
}
```

Read the actual source code. Do not guess.
