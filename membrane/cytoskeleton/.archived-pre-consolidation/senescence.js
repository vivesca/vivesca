#!/usr/bin/env node
// UserPromptSubmit hook — detect session wind-down signals and nudge /wrap or /daily
// Only fires when the user's message looks like they're wrapping up, not every response.

const input = require('fs').readFileSync('/dev/stdin', 'utf8').trim();
let data;
try {
  data = JSON.parse(input);
} catch {
  process.exit(0);
}

const prompt = (data.prompt || '').toLowerCase().trim();

// Only act on short messages — wind-down signals are brief
if (prompt.length > 80) process.exit(0);

const windDownPhrases = [
  "that's all", "thats all",
  "that's it", "thats it",
  "nothing else",
  "good for now",
  "all done",
  "done for today", "done for now",
  "signing off",
  "nothing more",
  "we're done", "were done",
  "i'm done", "im done",
  "all good",
  "no more",
  "bye",
  "ok bye",
  "thanks bye",
  // Reflective/meta questions that often close a session
  "any good way to avoid forgetting",
  "anything else i should",
  "anything we missed",
  "did we miss anything",
  "what else should we",
  "are we done",
  "is that everything",
  "that covers it",
  "wrap up",
  "wrap this up",
  "before we finish",
  "before i go",
  "last thing",
  "one last",
];

const isWindDown = windDownPhrases.some(phrase => prompt.includes(phrase))
  || /^(thanks|thank you|cheers|ok|okay|cool|great|perfect|got it|sounds good|looks good|follow your advice|lets do it|makes sense|fair enough|noted)[\s.!]*$/.test(prompt);

if (!isWindDown) process.exit(0);

const hour = new Date().toLocaleString('en-US', {
  timeZone: 'Asia/Hong_Kong',
  hour: 'numeric',
  hour12: false,
});

const hourNum = parseInt(hour, 10);

const msg = hourNum >= 21 || hourNum < 5
  ? "Session winding down — any loose ends before closing? Consider /daily to log the day."
  : "Session winding down — any loose ends before closing? Consider /wrap to capture open threads.";

console.log(msg);        // → system-reminder (Claude sees it)
console.error(msg);      // → terminal (Terry sees it)
