#!/usr/bin/env node
/**
 * TERM-001 — Terminology Gate  (R5: Turkish morphology fix)
 *
 * Forbidden Turkish process name: "Nokta Kaynak" and all grammatical variants
 * Required  Turkish process name: "Punta Kaynak"
 * Required  English process name: "Spot Welding"
 *
 * Usage (from frontend/):
 *   node scripts/term-check.mjs
 *
 * Exit 0 = TERM_001_GATE=PASS   (zero violations)
 * Exit 1 = TERM_001_GATE=FAIL   (violations found, missing root, or scanner error)
 */

import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join, extname, resolve, relative } from 'node:path'

// ── Cross-platform __dirname ─────────────────────────────────────────────────
// import.meta.url is a file URL (file:///D:/… on Windows).
// fileURLToPath converts it to a native OS path: D:\… on Windows, /… on POSIX.
// DO NOT use new URL(…).pathname — on Windows that keeps a leading slash.
const __filename = fileURLToPath(import.meta.url)
const __dirname  = dirname(__filename)

// Scan root is frontend/src — one level up from scripts/, then into src/
const root = resolve(__dirname, '..', 'src')

// ── Configuration ────────────────────────────────────────────────────────────
const FORBIDDEN = [
  /nokta\s+kaynak/gi,   // base form + consonant-preserving suffixes (kaynakta, kaynaklar…)
  /nokta\s+kaynağ/gi,   // vowel-initial suffix forms (k→ğ mutation): kaynağı, kaynağın, kaynağa…
]

const SCAN_EXTS = new Set(['.ts', '.tsx', '.js', '.jsx', '.html'])
const SKIP_DIRS = new Set(['node_modules', 'dist', '.git', 'coverage'])

// ── Filesystem walker ────────────────────────────────────────────────────────
function walk(dir, files = []) {
  let entries
  try {
    entries = readdirSync(dir)
  } catch (err) {
    // Unreadable directory — treat as scanner error, exit 1
    console.error(`TERM_001_ERROR: cannot read directory: ${dir}`)
    console.error(String(err))
    process.exit(1)
  }
  for (const entry of entries) {
    if (SKIP_DIRS.has(entry)) continue
    const full = join(dir, entry)
    let st
    try {
      st = statSync(full)
    } catch (err) {
      console.error(`TERM_001_ERROR: cannot stat: ${full}`)
      console.error(String(err))
      process.exit(1)
    }
    if (st.isDirectory()) walk(full, files)
    else if (SCAN_EXTS.has(extname(entry))) files.push(full)
  }
  return files
}

// ── Main ─────────────────────────────────────────────────────────────────────
try {
  // Guard: scan root must exist
  if (!existsSync(root)) {
    console.error(`TERM_001_ERROR: scan root not found: ${root}`)
    console.error('TERM_001_GATE=FAIL')
    process.exit(1)
  }

  const files = walk(root)
  let violations = 0
  const report = []

  for (const file of files) {
    let text
    try {
      text = readFileSync(file, 'utf8')
    } catch (err) {
      console.error(`TERM_001_ERROR: cannot read file: ${file}`)
      console.error(String(err))
      process.exit(1)
    }
    const lines = text.split('\n')
    lines.forEach((line, idx) => {
      for (const pat of FORBIDDEN) {
        pat.lastIndex = 0
        if (pat.test(line)) {
          violations++
          report.push({
            file: relative(resolve(__dirname, '..'), file),  // relative to frontend/
            line: idx + 1,
            text: line.trim(),
          })
        }
      }
    })
  }

  if (violations === 0) {
    console.log(`TERM_001_VIOLATIONS=0`)
    console.log(`TERM_001_GATE=PASS`)
    console.log(`TERM_001_FILES_SCANNED=${files.length}`)
    process.exit(0)
  } else {
    console.error(`TERM_001_VIOLATIONS=${violations}`)
    console.error(`TERM_001_GATE=FAIL`)
    console.error('')
    console.error('Violations (file:line → offending text):')
    for (const v of report) {
      console.error(`  ${v.file}:${v.line}  →  ${v.text}`)
    }
    process.exit(1)
  }

} catch (err) {
  // Unexpected scanner error — always exit 1, never swallow
  console.error('TERM_001_ERROR: unexpected scanner error')
  console.error(String(err))
  console.error('TERM_001_GATE=FAIL')
  process.exit(1)
}
