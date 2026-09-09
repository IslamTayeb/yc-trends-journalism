# Google Trends: search interest for "gpt", past 5 years (2021-09 to 2026-09)

Retrieved 2026-09-09 from https://trends.google.com/trends/explore?q=gpt&date=today%205-y (Web Search, all categories).
Values are Google's relative index: 100 = peak interest within that series, `<1` = below 1. Each file is normalised to its own peak,
so US and Worldwide values are not comparable to each other, only within a file.

| file | geo | granularity | source UI |
|---|---|---|---|
| google_trends_gpt_worldwide_weekly.csv | Worldwide | weekly (261 rows) | classic Explore, "Interest over time" CSV |
| google_trends_gpt_us_weekly.csv | United States | weekly (261 rows) | classic Explore, "Interest over time" CSV |
| google_trends_gpt_worldwide_monthly.csv | Worldwide | monthly (60 rows) | new Explore (Gemini) export, downloaded by Islam |
| google_trends_gpt_us_monthly.csv | United States | monthly (60 rows) | new Explore (Gemini) export, downloaded by Islam |

The weekly files have two header lines (`Category: All categories`, blank) before the `Week,gpt: (...)` header.
