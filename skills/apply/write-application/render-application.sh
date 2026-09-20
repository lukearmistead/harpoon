#!/usr/bin/env bash
# Turn the markdown drafts in apply/<slug>/ into files an applicant
# tracking system will accept. Ashby, Greenhouse and Lever want an upload, and a
# .md file is not one. The PDFs land beside the drafts they came from and are
# gitignored there, so a company directory holds the research, the drafts and
# the uploads together.
#
# Markdown stays the source because the master resume gets cut into a variant per
# company, and that only works if the source diffs cleanly. Typst owns layout,
# in resume.typ beside this script. PDF is the deliverable.
#
# Two things in the drafts are repo bookkeeping and must never reach an
# employer: the sources line every generated file ends with, and the seat
# metadata block. Both live below a <!-- cut --> marker and are stripped here
# rather than kept in a second copy that drifts.
#
# Usage: skills/apply/write-application/render-application.sh acme-health
set -euo pipefail
skill_dir="$(cd "$(dirname "$0")" && pwd)"
cd "$skill_dir/../../.."

# A company slug renders that application's drafts into apply/<slug>/,
# which is what gets uploaded. A path to any single markdown file renders into a
# temp directory, which is how the master resume gets looked at: the master is
# the long-form working document, so its render is a preview, never a sibling
# file that lingers next to the source.
target="${1:-}"
[ -n "$target" ] || { echo "usage: $0 <company-slug> | <path/to/draft.md>"; exit 1; }
for tool in pandoc typst; do
  command -v "$tool" >/dev/null || { echo "$tool not installed: brew install $tool"; exit 1; }
done

if [ -d "apply/$target" ]; then
  sources=("apply/$target/resume.md" "apply/$target/cover-letter.md")
  out="apply/$target"
  # The uploads carry the candidate's name, taken from git identity.
  name="$(git config user.name || true)"
  [ -n "$name" ] || { echo "git config user.name is empty: set it, the PDF filename carries it"; exit 1; }
  prefix="$(printf '%s\n' "$name" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-')"
elif [ -f "$target" ]; then
  sources=("$target")
  out="$(mktemp -d "${TMPDIR:-/tmp}/harpoon-render.XXXXXX")"
  prefix=""
else
  echo "not found: expected a company slug under apply/ or a path to a .md file"
  exit 1
fi
mkdir -p "$out"
written=()

# Drop the bookkeeping, turn range hyphens into en dashes, and drop the
# --- separators, whose job the section rules in resume.typ already do. Then
# three layout moves markdown cannot express:
#   - the contact line, the first non-empty line under the name, becomes
#     #contact(...). Its @ has to be escaped or Typst reads it as a label
#     reference. Whatever separator the markdown uses between the fields comes
#     through untouched, so the source line reads the way the PDF does. A
#     markdown link in it becomes a Typst one, which pandoc would have done had
#     the line not been handed to Typst raw.
#   - a section heading becomes #spine(name, dates) if it carries dates, and
#     #appendix(name) if it does not. Dates come from an immediately following
#     ### line, or from the heading's own trailing ", <year>" segment, and land
#     flush right on the rule line. The presence of dates is the whole test, so
#     an employer without years or a category with them lands at the wrong
#     level. resume.typ explains what the two levels are for.
#   - a bold-only line ending in a year is a role header and becomes
#     #entry(title, dates), title left, dates right.
# The markdown files stay untouched; only the render learns the layout.
prepare() {
  if grep -q '<!-- cut -->' "$1"; then
    sed '/<!-- cut -->/,$d' "$1"
  else
    sed -E '/^\*(Written|Cut) from/,$d' "$1"
  fi | sed -E \
    -e 's/([12][0-9]{3})-([12][0-9]{3})/\1–\2/g' \
    -e 's/([A-Za-z]{3,9} [12][0-9]{3})-([A-Za-z]{3,9} [12][0-9]{3})/\1–\2/g' \
    -e '/^-{3,}$/d' | awk '
    function raw(call) { print "```{=typst}"; print call; print "```"; print "" }
    # The trailing comma segment is dates iff it contains a year.
    function split_dates(line) {
      head = line; tail = ""
      if (match(line, /,[^,]*[12][0-9][0-9][0-9][^,]*$/)) {
        head = substr(line, 1, RSTART - 1)
        tail = substr(line, RSTART + 1)
        sub(/^ +/, "", tail)
        return 1
      }
      return 0
    }
    # [text](url) is markdown pandoc would handle, but the contact line is emitted
    # as raw Typst and skips pandoc, so it converts here. Contact line only: the
    # body links belong to pandoc, and a second pass would double them.
    function mdlinks(s,   out, m, p, txt, url) {
      out = ""
      while (match(s, /\[[^]]*\]\([^)]*\)/)) {
        m = substr(s, RSTART, RLENGTH)
        p = index(m, "](")
        txt = substr(m, 2, p - 2)
        url = substr(m, p + 2, length(m) - p - 2)
        out = out substr(s, 1, RSTART - 1) "#link(\"" url "\")[" txt "]"
        s = substr(s, RSTART + RLENGTH)
      }
      return out s
    }
    function flush_h2(dates) {
      if (dates == "") split_dates(h2)
      else { head = h2; tail = dates }
      if (tail == "") raw("#appendix(\"" head "\")")
      else raw("#spine(\"" head "\", \"" tail "\")")
      h2 = ""
    }
    # pandoc imports only conf from style.typ, so the injected calls below
    # need their own import.
    BEGIN { raw("#import \"style.typ\": spine, appendix, entry, contact") }
    /^# / && stage == 0 { print; stage = 1; next }
    stage == 1 && NF == 0 { print; next }
    stage == 1 && NF > 0 {
      line = $0
      gsub(/@/, "\\@", line)
      raw("#contact[" mdlinks(line) "]")
      stage = 2
      next
    }
    # A section heading waits one line: its dates may follow as an ### line.
    /^## / { if (h2 != "") flush_h2(""); h2 = substr($0, 4); next }
    h2 != "" && NF == 0 { next }
    h2 != "" && /^### / { flush_h2(substr($0, 5)); next }
    h2 != "" { flush_h2("") }
    /^\*\*[^*]+\*\*$/ {
      if (split_dates(substr($0, 3, length($0) - 4))) {
        raw("#entry(\"" head "\", \"" tail "\")")
        next
      }
    }
    { print }
    END { if (h2 != "") flush_h2("") }
  '
}

# Typst resolves an import relative to the file importing it, and pandoc's own
# --pdf-engine=typst compiles in a temp directory where no relative path
# survives. So the styling is copied in beside the generated document and the
# two steps are run separately.
cp "$skill_dir/resume.typ" "$out/style.typ"

for src in "${sources[@]}"; do
  [ -f "$src" ] || continue
  name=$(basename "$src" .md)
  body="$out/$name.src.md"
  prepare "$src" > "$body"
  pandoc "$body" -s -t typst -M template=style.typ -o "$out/$name.build.typ"
  typst compile "$out/$name.build.typ" "$out/$prefix$name.pdf"
  rm "$body" "$out/$name.build.typ"
  written+=("$out/$prefix$name.pdf")
done

rm "$out/style.typ"

# Most directories under apply/ hold research and no drafts yet, so a
# slug with nothing to render is ordinary, not an error.
if [ ${#written[@]} -eq 0 ]; then
  echo "no drafts to render in $out"
  exit 0
fi

echo "wrote:"
printf '  %s\n' "${written[@]}"
