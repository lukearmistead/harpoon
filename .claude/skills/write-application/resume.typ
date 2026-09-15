// Typst styling for rendered applications. pandoc's typst writer imports `conf`
// from here and wraps the document body in it, so this file owns layout and the
// markdown owns content.
//
// Two families with a clean split: Inter carries the skeleton (header
// caps, role titles, dates, the contact line) and Charter carries the name
// and the body. Inter is a neo-grotesque and Charter a humanist serif, so
// the pairing is a contrast, not a match. What makes it hold is that both
// are low contrast with a large x-height, and that Inter is used only in
// small sizes where its neutrality reads as structure. Note the family is
// "Inter", not "Inter Display": the display cut is spaced for headlines and
// falls apart at 8.5pt. Dates share the spine label's face so both ends of
// a header line read as one thing.
//
// The vertical rhythm is deliberate: lines inside a bullet sit tighter than
// the gap between bullets, which sits tighter than the gap before a role
// header. Flattening those three distances back to one number is what made an
// earlier version read as a wall of gray.
//
// `spine`, `appendix`, `entry` and `contact` are called from raw Typst that
// render-application.sh injects when it splits dates out of headings and role
// lines. They take strings, not content, so the script never has to escape
// markup.
//
// The `..args` sink is deliberate. pandoc passes title, date, lang and a dozen
// other named arguments whether or not they are set, and swallowing them keeps
// this signature from breaking when pandoc adds another.

#let ink = rgb("#111111")
#let quiet = rgb("#404040")
#let rule = rgb("#9a9a9a")
#let faint = luma(105)
#let dim = luma(135)
#let serif = ("Charter", "Georgia", "Times New Roman")
#let sans = ("Inter", "Helvetica Neue", "Helvetica")

// Small metadata: the fallback dates line under a fallback heading.
#let meta(body) = text(font: sans, size: 8pt, fill: quiet, body)

// The date that rides a spine rule, in the spine label's own face so both ends
// of that line read as one thing: 8.5pt, weight 500, black. Inter ships a true
// 500, so the weight is exact, not rounded like Charter's.
//
// It briefly wore the role dates' clothes instead, 9pt weight 300 in the same
// grey, on the theory that matching them stacks the date column into one tone.
// That reads backwards. The company span is the line the reader navigates by,
// and dropping it to the role dates' grey left the top of the block with
// nothing holding it down. Grey is the role dates' job. Black is this one's.
//
// Tracking is 0em, not the 0.9pt the caps beside it carry: letterspacing opens
// up a word and pulls a number apart, and a date is read as one object.
// Figures are tabular, so every digit takes the same advance and the right edge
// of this date lands on the right edge of the role dates below it whatever the
// digits happen to be.
#let dateline(body) = text(font: sans, size: 8.5pt, weight: 500, tracking: 0em,
  number-width: "tabular", body)

// Two header levels. `spine` carries the employers, the dated blocks that make
// the case. `appendix` carries the categories that close the page, Education
// and Outside, which have no dates and no claim on the reader until the spine
// has been read.
//
// Which level a heading gets is decided by whether it carries dates, in
// render-application.sh. That keeps layout syntax out of the markdown, which
// the candidate edits by hand, at one cost worth knowing: a dated category or a
// dateless employer silently lands at the wrong level. Give an employer its
// years and keep dates off a category.

// Employer header: letterspaced caps, a hairline, and the company's span of
// years on the right margin. Both date columns are right-aligned, the company
// span here and the role dates below, so the two ends of every header line
// stack into one edge down the page. What keeps the span from reading as a
// repeat of the role date under it is the weight: same face and size, one
// cut lighter.
//
// Horizon alignment happens to center the rule on Inter's caps exactly,
// measured at 0.00pt off centre on a 600ppi render, the same as it landed for
// Seravek; Charter needed a 1.3pt drop, so re-measure that way if the header
// face ever changes again.
#let spine(name, dates) = block(width: 100%, above: 1.4em, below: 0.6em, breakable: false, sticky: true,
  grid(
    columns: (auto, 1fr, auto),
    column-gutter: 0.6em,
    align: horizon,
    text(font: sans, size: 8.5pt, weight: 500, tracking: 0.9pt, upper(name)),
    line(length: 100%, stroke: 0.6pt + rule),
    dateline(dates),
  ))

// Category header: the spine's caps and tracking, a size down and a shade
// lighter, with no rule and no dates, so it cannot be mistaken for another
// employer. The space above it is the point, and it is wider than the spine
// gets: what the reader should feel there is the start of the back matter, not
// the next item in the list.
#let appendix(name) = block(width: 100%, above: 1.9em, below: 0.6em, breakable: false, sticky: true,
  text(font: sans, size: 8pt, weight: 500, tracking: 0.9pt, fill: faint, upper(name)))

// Role line: title left, dates on the right margin. The dates keep the title's
// face and give up a size, a weight, and most of their ink, which is what keeps
// the title leading.
//
// The size is 8.5pt because that is what the spine date on the rule above is,
// not because of anything on this line. Same size, same face, same 0em
// tracking, same tabular figures: the four date strings in the block are then
// within 0.04pt of one another in width, so the column squares off at both
// edges instead of stepping in on the left the way a 9pt date under an 8.5pt
// one does. Horizon alignment holds the smaller date against its title, within
// about a fifth of a point of a shared baseline.
//
// `dim` is the width of that gap and it was widened once, from luma(100) to
// luma(135), to put more air between these dates and the near-black one on the
// rule above them. It was set from this side because the spine date was already
// at the page's darkest ink and had nowhere to go.
//
// Tabular figures again, and year-only ranges in the markdown, so every role
// date is the same nine characters wide. The three of them stack into a
// rectangle with the company's span directly above, and the column reads as one
// block instead of as three ragged strings.
#let entry(title, dates) = block(width: 100%, above: 1em, below: 0.45em, breakable: false, sticky: true,
  text(font: sans, size: 9pt,
    grid(
      columns: (1fr, auto),
      align: (left + horizon, right + horizon),
      text(weight: 500, title),
      text(size: 8.5pt, weight: 400, fill: dim, number-width: "tabular", dates),
    )))

// The contact line, centred under the name. The block needs its full width
// spelled out: an auto-width block shrinks to its content, leaving align
// nothing to center within. Inter Regular in ink, sized up instead of weighted
// up:
// this line has to survive print, and grey kept losing to the paper, but
// every heavier weight shouted. Size is capped by the one-line fit, which is
// why Inter sits a point below the 9.5pt Seravek used to hold: Inter is the
// wider face, and the current line runs 499pt of the 518pt measure at 8.5pt
// against 514pt at 8.75pt. The point comes off the size, not off the page:
// x-height measures 4.80pt here against Seravek's 4.68pt at 9.5pt, and this
// line is nearly all lowercase, so it reads no smaller. Caps do lose a little,
// 6.24pt against 6.57pt, which only shows in the CA. Re-measure with
// `measure()` before raising this, and keep the slack: a variant with a longer
// handle has to fit too.
#let contact(line) = block(width: 100%, below: 1.1em,
  align(center, par(justify: false, text(font: sans, size: 8.5pt, weight: 400, fill: ink, line))))

#let conf(..args, doc) = {
  set page(
    paper: "us-letter",
    margin: (x: 0.65in, top: 0.45in, bottom: 0.45in),
    numbering: none,
  )

  set text(
    font: serif,
    size: 9.5pt,
    fill: ink,
    hyphenate: false,
  )

  // Ragged right, not justified. Justification at this measure opened rivers of
  // white space inside the long bullets, and an even word space costs less than
  // an even right edge buys.
  set par(justify: false, leading: 0.5em, spacing: 0.8em)

  // Name. Charter by inheritance, and deliberately: the name was set in Inter
  // to match the skeleton and it read as another label rather than as the
  // person. The serif is the one thing on the page at display size, so it is
  // the one thing that should not look structural. `below` sits between the
  // spine header's 0.6em and the contact line's 1.1em; the old 0.35em pinned
  // the contact line against the name's descenders.
  show heading.where(level: 1): it => block(width: 100%, above: 0em, below: 0.7em)[
    #set align(center)
    #set text(size: 19pt, weight: 400, tracking: 0.3pt)
    #it.body
  ]

  // Fallback for markdown that skips the render script's heading transforms:
  // a level-2 heading becomes a category header, matching the rule that a
  // heading without dates is not an employer, and a level-3 heading the dates
  // line under it.
  show heading.where(level: 2): it => appendix(it.body)
  show heading.where(level: 3): it => block(above: 0em, below: 0.6em, meta(it.body))

  // A bold lead-in names an entry; keep it plainly bold.
  show strong: set text(weight: 700)

  set list(indent: 0.5em, body-indent: 0.45em, marker: [•], spacing: 0.55em)
  show list: set block(above: 0.45em, below: 0.85em)

  show link: set text(fill: ink)
  show raw: set text(font: ("Menlo", "Courier New"), size: 0.88em)

  doc
}
