# Google Trends: search interest for "gpt", "ai" and "llm"

Retrieved 2026-09-09 from https://trends.google.com/trends/explore (Web Search, all categories), "Interest over time" CSV export.
Values are Google's relative index: 100 = peak interest **within that file**, `<1` = below 1. Each file is normalised to its own
peak, so levels are not comparable across files (US vs Worldwide, or one term vs another); only shapes are.

| granularity | range | files |
|---|---|---|
| `monthly_2004` | Jan 2004 – Sep 2026, 273 months (Google's longest range, `date=all`) | gpt / ai / llm × us / worldwide (6 files) |
| `weekly_5y` | Sep 2021 – Sep 2026, 261 weeks (`date=today 5-y`) | gpt / ai / llm × us / worldwide (6 files) |
| `monthly` (60 rows) | Sep 2021 – Sep 2026 | gpt × us / worldwide, from the new Gemini Explore export, downloaded by Islam |

Format: two header lines (`Category: All categories`, blank) then `Month,<term>: (<geo>)` or `Week,...`. The 60-row "new Explore"
files have a plain `"Time","gpt"` header instead.

Caveats: "gpt" before 2018 also captures unrelated meanings (GUID partition table); "ai" is a common substring in many languages
and Google's term matching is not exact; "llm" before 2022 is mostly the law degree. The pre-2022 baselines are therefore noisy floors,
not zero.
