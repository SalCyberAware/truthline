# Collecting the first 20 benchmark samples

## Why we do this (in plain words)
A benchmark is a ruler. Before we claim Truthline helps anyone, we measure it on files where we already know the
answer: some real, some faked. Two numbers matter most:

- **Wrongful fabricated rate**: real screenshots that Truthline wrongly calls fake. This must stay at **0**. A tool that
  accuses real people is worse than no tool.
- **Catch rate**: fake screenshots Truthline correctly flags. We report it honestly, however low.

Expect the catch rate to be close to 0% on the first run. The current screenshot checks are all weak evidence, and weak
evidence is not allowed to decide a grade. That is the point of the first run: it is the "before" photo. Every stronger
check we add later is measured against it.

## The never-list (read this first)
Never collect, create, store or share:
- anything sexual involving a minor, in any form (real, edited or AI-made)
- real threats, or anything taken from a live case or investigation
- other people's private messages without their written permission
- anything from someone under 18. All contributors and everyone appearing in a sample must be 18 or older.

If you are ever unsure, don't add the file. Ask first.

## The starter set: 20 samples

| Group | How many | What to make |
| --- | --- | --- |
| **real** | 8 | 2 iPhone Messages light mode, 2 iPhone dark mode, 2 Android Messages, 1 WhatsApp, 1 Instagram DM. Make 2 of the 8 "forwarded" copies (sent through WhatsApp or email and saved again), because real files get recompressed this way. |
| **fabricated** | 8 | 3 made with a public fake-text-message website (iPhone style), 2 from the same kind of site (Android style), 3 made by editing one of your own real screenshots in an image editor (change a word, a name or the time). |
| **ai_generated** | 4 | Ask an AI image tool for "a screenshot of a text message conversation". Use two different tools if you can. Write the tool name and version in `source`. |

Mix full-screen captures with 2 or 3 cropped ones. Real people crop screenshots, and the tool must not treat cropping as proof of fakery.

## How to make the real ones safely
1. Use two adults who agree (you and a friend). Chat about something harmless: "Are we still on for lunch Thursday?"
2. Take the screenshot on the phone itself. iPhone: side button + volume up. Android: power + volume down.
3. Move the original to your computer by USB cable, AirDrop or email to yourself. Avoid sending the original through a
   chat app, because chat apps strip details. (The 2 "forwarded" copies are the exception on purpose.)
4. Both people sign `consent-form.md`. Keep the signed copy somewhere safe, outside the repo. Give it a number such as `CR-001`.

## For each sample (about two minutes)
1. Make the file and get consent (for a fabricated or AI sample, your own consent is enough, since no one else appears).
2. Run, from the `truthline` folder:

       python benchmark/add_sample.py my-file.png --category real --source "iPhone 15, Messages, dark mode" --consent-ref CR-001 --confirm-rules

   The helper checks the rules, copies the file into `benchmark/samples/`, computes its fingerprint (SHA-256) and
   adds one row to `benchmark/manifest.csv`.
3. After the 20th sample, run the benchmark: `python benchmark/run_benchmark.py benchmark/manifest.csv`
4. Commit **only `manifest.csv`**. The sample files themselves are blocked from Git on purpose (see `.gitignore`).
   Only fingerprints and results are ever public.

## Windows tip: keep samples outside OneDrive and Documents
Windows' ransomware shield can block Python from writing into Documents, and OneDrive would sync your sample
images to the cloud. Make a data folder instead, for example `C:\truthline-data`, and add `--benchmark-dir`:

    python benchmark\add_sample.py fake-iphone-01.png --category fabricated --source "site name, iPhone style" --consent-ref CR-001 --confirm-rules --benchmark-dir C:\truthline-data
    python benchmark\run_benchmark.py C:\truthline-data\manifest.csv

When you want the manifest (file names and fingerprints only, never images) in the project, copy
`C:\truthline-data\manifest.csv` over `benchmark\manifest.csv` using File Explorer, then commit it.
See `docs/windows-setup.md` for the full Windows setup.

## Where things live
- The image files stay on your computer under `benchmark/samples/`. Never upload them to GitHub.
- Signed consent forms stay with you, outside the project folder.
- GitHub only gets the manifest: file names, categories, sources, consent numbers and fingerprints.

## Can we get samples from the internet? (asked 19 Oct 2026)
- **Real samples: no.** A screenshot found online has no known answer (it may itself be fake or re-saved), it is
  someone else's private conversation, and copying it usually breaks site terms. Our search also found no public
  labeled dataset of real/fake chat screenshots; the closest open project says the same.
- **Fabricated and AI samples: yes, we make them.** Public fake-text generator sites and AI image tools, with harmless
  text we type and the tool name recorded in `source`.
- **Synthetic samples: unlimited, from our own renderer.** `benchmark/render_synthetic.py` draws phone-sized chat
  screenshots with flaws we plant on purpose (status-bar seam, crooked bubbles, empty status bar, editor tag):

      python benchmark/render_synthetic.py --out benchmark/samples/synthetic --count 12

  They are labeled `synthetic`, kept out of the fabricated catch rate (they would flatter it), and used to prove each
  analyzer check actually fires. Same seed, same image, so anyone can reproduce the set.

## What happens next
Once 20 samples are in, we read the results together. The misses tell us exactly which stronger check to build next:
status-bar layout per phone model, bubble shapes per app, fonts, the clock against the file's timestamp.
