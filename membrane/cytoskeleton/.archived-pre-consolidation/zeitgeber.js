#!/usr/bin/env node
/**
 * UserPromptSubmit Hook - Time-of-day awareness
 *
 * After 9pm HKT, reminds about /daily instead of starting new work.
 * Informational only (stderr), not blocking.
 */

const hour = parseInt(
  new Date().toLocaleString('en-US', {
    timeZone: 'Asia/Hong_Kong',
    hour: 'numeric',
    hour12: false
  }),
  10
);

if (hour >= 21 || hour < 5) {
  process.stderr.write('🌙 After 9pm HKT — suggest /daily at a natural stopping point.\n');
}
