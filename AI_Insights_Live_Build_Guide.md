# AI HR Insights — Live Build Guide (Reference)

This documents exactly how the live AI insight queries were built in this project, so you can reference it, redo it, or explain it in an interview.

---

## What this actually is

A **Power Query** query that:
1. Calculates real numbers from your cleaned HR table (using M code, not DAX)
2. Builds those numbers into a plain-English "facts" sentence
3. Sends that sentence to Groq's LLM API as a live web request
4. Returns the AI's structured interpretation as text

This runs **every time you hit Refresh** in Power BI — it is genuinely live, not a one-time script. No Python, no external app required at runtime.

---

## Prerequisites (one-time setup)

1. A free Groq API key from [console.groq.com](https://console.groq.com) (API Keys section → Create API Key)
2. Power BI's privacy checker turned off for this file:
   - **File → Options and settings → Options → Current File → Privacy**
   - Select **"Always ignore Privacy Level settings"**
   - (Without this, you'll hit a `Formula.Firewall` error — Power BI blocking your local data from combining with an external web source)

---

## Step-by-step: building one live AI insight query

### Step 1 — Reference your cleaned table (don't duplicate/re-import)

1. In Power Query, right-click your main table (e.g. `HRDataset_v14`) → **Reference**
2. Rename the new query to something descriptive, e.g. `AI Insight - Department`

**Why Reference, not Duplicate:** Reference keeps this new query linked to your already-cleaned table — any future cleanup fixes to the original table flow through automatically. Duplicate would create a disconnected copy.

### Step 2 — Open Advanced Editor and write the M code

With the new query selected: **Home tab → Advanced Editor**. Delete the default content and replace it with a structure like this:

```m
let
    Source = #"HRDataset_v14",

    // --- 1. Calculate whatever real numbers this insight needs ---
    // Example: filter to one group, count rows, sum a column, etc.
    ActiveOnly = Table.SelectRows(Source, each [EmploymentStatus] = "Active"),
    SomeMetric = Table.RowCount(ActiveOnly),

    // --- 2. Build a plain-English sentence containing those numbers ---
    FactsText = "Here are the facts: metric = " & Text.From(SomeMetric) & ".",

    // --- 3. Groq API call setup ---
    ApiKey = "YOUR_API_KEY_HERE",
    Url = "https://api.groq.com/openai/v1/chat/completions",
    Headers = [#"Content-Type"="application/json", #"Authorization"="Bearer " & ApiKey],
    SystemMsg = "You are an HR analytics assistant. Interpret only the facts given. Never invent numbers. Use cautious language (may suggest, could indicate). Keep each section to 1-2 sentences maximum. Respond in this structure: 1. Key Insight 2. Supporting Metric 3. Potential Driver 4. Risk/Concern 5. Recommended Investigation.",
    Body = "{""model"": ""openai/gpt-oss-120b"", ""messages"": [{""role"": ""system"", ""content"": """ & SystemMsg & """}, {""role"": ""user"", ""content"": """ & FactsText & """}]}",

    // --- 4. Send the request and extract the response text ---
    Response = Web.Contents(Url, [Headers=Headers, Content=Text.ToBinary(Body)]),
    JsonResponse = Json.Document(Response),
    Result = JsonResponse[choices]{0}[message][content]
in
    Result
```

3. Replace `YOUR_API_KEY_HERE` with your real Groq key (each query needs its own copy pasted in — M queries don't share variables)
4. Replace the `ActiveOnly` / `SomeMetric` / `FactsText` sections with the real calculation logic for that specific insight
5. Click **Done**

If it worked, the query preview shows a block of AI-generated text.

### Step 3 — Common errors and fixes

| Error | Cause | Fix |
|---|---|---|
| `Formula.Firewall: ... privacy levels` | Power BI blocking local data + external API combination | Turn on "Always ignore Privacy Level settings" (see Prerequisites) |
| `We cannot apply operator < to types Date and Text` | A date column isn't resolving as a true Date type in this context | Wrap the column in `Date.From([ColumnName])` before comparing |
| `The Date value must contain the Date component` | Column is DateTime, not pure Date | Same fix — wrap in `Date.From(...)` |
| Model not found (404) | Groq deprecated the model name | Check `console.groq.com/docs/models` for current model names; update the `model` field in `Body` |

### Step 4 — Bring it into your report

1. Once all your AI Insight queries are built and working, click **Close & Apply** (Power Query Home tab)
2. On your report page, add a **Table visual** (not a Card — Cards truncate long text)
3. Drag the query's field (e.g. `AI Insight - Department`) into the Table's Values
4. Widen the visual so the wrapped text displays cleanly; optionally turn off the column header in Format pane

### Step 5 — Refreshing

Every time you click **Refresh** in Power BI, these queries re-run: recalculating the real numbers from your current data, and calling Groq again for a fresh interpretation. This means:
- Real API usage each refresh (fine on Groq's free tier for occasional use)
- Requires internet access to refresh successfully
- If Groq's model name changes again in the future, queries will error until the model name is updated

---

## Key lesson learned during this build

**A calculation bug can hide inside a filter context assumption.** One of the DAX measures reused for group breakdowns (Department, Performance Score) was accidentally using a company-wide denominator instead of a group-specific one, because it used `ALL(TableName)` — which strips *all* filters, including the one you actually wanted to keep. The live Power Query numbers (calculated independently, with simple direct filters) caught this by disagreeing with the DAX chart — a good example of why cross-checking a calculation two different ways is worth the extra effort.
