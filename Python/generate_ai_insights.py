"""
People Analytics Command Center — AI HR Insights Generator
------------------------------------------------------------
Takes ALREADY-CALCULATED metrics from the Power BI model (Phases 1-6)
and asks an LLM to interpret them into structured HR insights.

IMPORTANT: the LLM is instructed to interpret ONLY the numbers given.
It must never invent statistics, percentages, or facts not provided.

Setup:
    pip install groq
    Replace YOUR_API_KEY_HERE below with your actual Groq API key
"""

from groq import Groq
import json

# ---------------------------------------------------------
# STEP 1: Your Groq API key
# ---------------------------------------------------------
API_KEY = ""YOUR_GROQ_API_KEY_HERE""  # <-- paste your key here, keep the quotes

client = Groq(api_key=API_KEY)

# ---------------------------------------------------------
# STEP 2: The 4 locked-in findings from your Power BI model
# These are the ONLY facts the AI is allowed to reference.
# ---------------------------------------------------------
FINDINGS = [
    {
        "id": 1,
        "topic": "Performance vs Attrition",
        "facts": "Employees rated 'Fully Meets' have a 28.13% attrition rate, "
                  "the highest of any performance category. Employees on a "
                  "Performance Improvement Plan (PIP) have only a 2.36% "
                  "attrition rate, the lowest of any category. Company-wide, "
                  "88 of 104 total exits (85%) were voluntary, not for cause."
    },
    {
        "id": 2,
        "topic": "Department Concentration",
        "facts": "The Production department has the highest attrition rate "
                  "of any department at 28.62%. Production also accounts for "
                  "83 of 104 total exits (80% of all exits), despite making "
                  "up 61% of total headcount (126 of 207 active employees). "
                  "Production accounts for $7.61M of $14.63M total workforce "
                  "cost (52%)."
    },
    {
        "id": 3,
        "topic": "Headcount and Attrition Trend",
        "facts": "Active headcount grew from 21 employees in 2010 to a peak "
                  "of 229 in 2015, then declined to 207 by the end of 2018. "
                  "Attrition rate followed a similar pattern, rising from "
                  "4.55% in 2010 to a peak of 9.13% in 2015, before falling "
                  "to 3.52% in 2017."
    },
    {
        "id": 4,
        "topic": "Cost Scenario — Hiring Freeze",
        "facts": "Current total workforce cost is $14.63M across 207 active "
                  "employees (average salary $71,000). A modeled hiring "
                  "freeze scenario, assuming 8 exits per year (matching the "
                  "2017 rate) with no replacement hiring, projects an annual "
                  "cost reduction to approximately $14.07M, a savings of "
                  "roughly $560,000 per year."
    }
]

# ---------------------------------------------------------
# STEP 3: The strict system prompt
# ---------------------------------------------------------
SYSTEM_PROMPT = """You are an HR analytics assistant. You will be given a set of
ALREADY-CALCULATED facts from a company's HR data. Your job is to interpret
these facts into a structured business insight.

STRICT RULES:
- You must NEVER invent, estimate, or add any number, percentage, or statistic
  that is not explicitly given to you in the facts.
- You must NEVER claim predictive or causal certainty (e.g. do not say "X causes Y").
  Use cautious, diagnostic language like "this may suggest" or "this could indicate."
- If you are unsure of a driver or cause, say the underlying reason is unclear
  and recommend further investigation rather than guessing.
- Do not reference any company, industry benchmark, or external statistic that
  was not provided to you.

For each finding, respond in this exact structure:
1. Key Insight: (one sentence, plain language)
2. Supporting Metric: (restate the specific number(s) from the facts given)
3. Potential Driver: (a cautious, non-definitive hypothesis)
4. Risk / Area of Concern: (what this could mean for the business if unaddressed)
5. Recommended Investigation: (a specific, actionable next step for HR to explore)
"""

# ---------------------------------------------------------
# STEP 4: Send each finding to the LLM
# ---------------------------------------------------------
def generate_insight(finding):
    user_prompt = f"""Topic: {finding['topic']}

Facts:
{finding['facts']}

Generate the structured insight following the exact format instructed."""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,  # low temperature = more consistent, less "creative"/embellished
        max_tokens=500
    )
    return response.choices[0].message.content


def main():
    all_insights = []

    for finding in FINDINGS:
        print(f"\n{'='*60}")
        print(f"Generating insight for: {finding['topic']}")
        print('='*60)

        insight_text = generate_insight(finding)
        print(insight_text)

        all_insights.append({
            "id": finding["id"],
            "topic": finding["topic"],
            "insight": insight_text
        })

    # Save all results to a JSON file for reference / re-use in Power BI
    with open("ai_hr_insights_output.json", "w") as f:
        json.dump(all_insights, f, indent=2)

    print(f"\n\nAll insights saved to ai_hr_insights_output.json")


if __name__ == "__main__":
    main()
