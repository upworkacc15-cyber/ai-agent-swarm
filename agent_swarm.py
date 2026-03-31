import json
import time
import os
from google import genai

# API key loaded from GitHub Secrets
API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)


def call_gemini(prompt: str) -> str:
    time.sleep(35)
    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=prompt
    )
    return response.text


class GeneratorAgent:
    def generate(self, prompt: str) -> str:
        full_prompt = f"""You are an expert copywriter specializing in sales emails.
        Generate a professional, compelling sales email based on the user's prompt.
        The email should be concise, engaging, and include a clear call-to-action.

        Email Prompt: {prompt}"""
        return call_gemini(full_prompt)


class EvaluatorAgent:
    def evaluate(self, email: str) -> dict:
        evaluation_prompt = f"""Evaluate the following sales email on three dimensions:
1. Clarity (1-10): How clear and easy to understand is the message?
2. CTA (1-10): How effective is the call-to-action?
3. Tone (1-10): How appropriate and professional is the tone?

Email:
{email}

Respond in JSON format only, no extra text, no markdown, just raw JSON like this:
{{"clarity": 8, "cta": 7, "tone": 9, "overall_score": 8, "feedback": "your feedback here"}}"""

        response_text = call_gemini(evaluation_prompt)
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            json_str = response_text[start_idx:end_idx]
            return json.loads(json_str)
        except:
            return {"clarity": 5, "cta": 5, "tone": 5, "overall_score": 5, "feedback": response_text}


class SelectorAgent:
    def select_best(self, candidates: list, evaluations: list) -> tuple:
        selection_prompt = "You are an expert email reviewer. Based on the scores below, select the best email.\n\nCandidates:\n"

        for i, (email, eval_score) in enumerate(zip(candidates, evaluations)):
            selection_prompt += f"\n--- Candidate {i+1} ---\n"
            selection_prompt += f"Overall Score: {eval_score.get('overall_score', 0)}\n"
            selection_prompt += f"Clarity: {eval_score.get('clarity', 0)}, CTA: {eval_score.get('cta', 0)}, Tone: {eval_score.get('tone', 0)}\n"
            selection_prompt += f"Feedback: {eval_score.get('feedback', '')}\n"

        selection_prompt += '\nRespond in JSON format only, no extra text, no markdown, just raw JSON like this: {"best_candidate": 1, "rationale": "reason here"}'

        response_text = call_gemini(selection_prompt)
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            json_str = response_text[start_idx:end_idx]
            result = json.loads(json_str)
            return int(result.get('best_candidate', 1)) - 1, result.get('rationale', '')
        except:
            return 0, response_text


class FormatterAgent:
    def format(self, email: str) -> str:
        formatting_prompt = f"""Polish and format the following sales email for final delivery.
Ensure it has:
- A suggested subject line at the top
- Correct grammar and punctuation
- Professional formatting with proper line breaks
- A compelling closing

Email:
{email}"""
        return call_gemini(formatting_prompt)


class EmailAgentSwarm:
    def __init__(self):
        self.generator = GeneratorAgent()
        self.evaluator = EvaluatorAgent()
        self.selector = SelectorAgent()
        self.formatter = FormatterAgent()

    def generate_email(self, prompt: str) -> dict:
        print("=" * 60)
        print("🤖 Email Agent Swarm Pipeline")
        print("=" * 60)
        print(f"\n📝 Prompt: {prompt}\n")
        print("⚠️ Note: 35 second delay between calls to respect free tier limits")
        print("⏱️ Estimated time: ~5 minutes. Please don't interrupt!\n")

        # Stage 1: Generate 3 versions
        print("Stage 1: GENERATOR 🎯")
        print("-" * 40)
        candidates = []
        for i in range(3):
            print(f"Generating version {i+1}/3... (waiting 35s)")
            candidates.append(self.generator.generate(prompt))
            print(f"✅ Version {i+1} done")
        print("✅ Generated 3 email versions\n")

        # Stage 2: Evaluate each version
        print("Stage 2: EVALUATOR ⭐")
        print("-" * 40)
        evaluations = []
        for i, email in enumerate(candidates):
            print(f"Evaluating version {i+1}/3... (waiting 35s)")
            scores = self.evaluator.evaluate(email)
            evaluations.append(scores)
            print(f"  ✅ Score: {scores.get('overall_score', 'N/A')}/10")
        print("✅ Evaluation complete\n")

        # Stage 3: Select the best
        print("Stage 3: SELECTOR 🏆")
        print("-" * 40)
        print("Selecting best version... (waiting 35s)")
        best_idx, rationale = self.selector.select_best(candidates, evaluations)
        print(f"✅ Selected version {best_idx + 1}")
        print(f"Rationale: {rationale}\n")

        # Stage 4: Format the final email
        print("Stage 4: FORMATTER ✨")
        print("-" * 40)
        print("Formatting final email... (waiting 35s)")
        final_email = self.formatter.format(candidates[best_idx])
        print("✅ Formatting complete\n")

        print("=" * 60)
        print("📧 FINAL EMAIL OUTPUT")
        print("=" * 60)
        print(final_email)

        return {
            "original_prompt": prompt,
            "candidates": candidates,
            "evaluations": evaluations,
            "best_index": best_idx,
            "selection_rationale": rationale,
            "final_email": final_email
        }


# ---- RUN IT ----
example_prompt = """
Write a sales email for a B2B SaaS company selling a project management tool.
Target audience: Small business owners and startup founders.
Key benefits: Increased team productivity, reduced project delays, affordable pricing.
"""

swarm = EmailAgentSwarm()
result = swarm.generate_email(example_prompt)
