# Literature Review

Target: finalised taxonomy + lit review by end of Phase 1 
## Core sources to read first

1. **Brignull, H. — "Dark Patterns" (darkpatterns.org / deceptive.design)**
   The original taxonomy. Start here — everything else cites or extends this.

2. **Mathur, A., Acar, G., et al. (Princeton) — "Dark Patterns at Scale:
   Findings from a Crawl of 11K Shopping Websites" (2019)**
   Large-scale empirical crawl + classification of dark patterns on
   e-commerce sites. Likely your closest prior-work comparison for the
   scraping + detection methodology.

3. **UIGuard dataset / paper**
   Check what categories it actually covers and how patterns are labelled
   (image-based? DOM-based? text-based?) — this determines whether it's
   usable as-is for training or needs supplementing.

4. **Gray, C. M., et al. — "The Dark (Patterns) Side of UX Design" (2018)**
   HCI framing of dark patterns; useful for the UX/ethics angle in
   objectives 6 and the HCI learning-outcome alignment.

5. **Di Geronimo, L., et al. — "UI Dark Patterns and Where to Find Them:
   A Study on Mobile Applications and User Perception" (2020)**
   Mobile-focused, but useful for detection methodology comparisons.

## Questions to answer while reading

- [ ] What categories does Brignull define, and which are realistically
      detectable from HTML/CSS/text alone (vs. requiring human judgment
      of intent)?
- [ ] How did Mathur et al. label their training data — manually,
      crowdsourced, or rule-based?
- [ ] What features did prior detection tools use — DOM structure, visible
      text, computed CSS styles (e.g. font-size of "decline" vs "accept"
      buttons), or a combination?
- [ ] What's the reported accuracy/precision/recall of prior automated
      detectors? This sets a realistic bar for your own evaluation.
- [ ] Are there 4–6 categories that are (a) well-documented in the
      literature, (b) detectable from static page content, and
      (c) distinct enough from each other to classify reliably? This
      becomes your refined taxonomy (Objective 2).

## Working taxonomy (draft — revise after reading above)

| Category | Definition | Detectable signal |
|---|---|---|
| Misdirection | Visual emphasis steers user toward one choice | Button styling/contrast, layout position |
| Hidden costs | Costs revealed only late in a flow | Form/checkout structure, price text changes |
| Confirmshaming | Guilt-based language on decline options | Text content of opt-out/cancel buttons |
| Disguised ads | Ads styled to look like content/navigation | DOM class names, ad-network script tags |
| Forced continuity | Hard-to-find cancel; auto-renewal | Form structure, cancellation flow depth |
| Urgency/scarcity | Fake countdowns, "X left in stock" | Text pattern match, timer-like DOM elements |

## Citation tracking

Keep a running BibTeX or Zotero library from the start — retrofitting
citations at write-up time (Phase 5) wastes time you won't have in
September.
