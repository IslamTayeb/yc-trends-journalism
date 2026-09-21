# Full-stack AI classification rubric

Every YC company from Winter 2019 onward is read once against Jared Friedman's definition below and given exactly one
category. The rubric is the whole instruction the classifier gets; nothing else about the company is used beyond the
fields in the chunk file (name, batch, one-liner, long description, YC industry/subindustry/tags as of the 2026-09-06
directory snapshot).

## The definition (Jared Friedman, YC, "Full-stack AI Companies", Summer 2025 Requests for Startups; quoted verbatim)

> At YC, I would like to fund more founders working on full-stack AI companies. What is a full-stack AI company, you
> ask? Let me give an example.
>
> Suppose you believe that LLMs are now able to automate a lot of legal work. There are two things you might do with
> that idea. You could build an AI agent and sell it to law firms. That's what most people do.
>
> Or, you could start your own law firm, staff it with AI agents, and compete with the existing law firms.
>
> That, my friends, is going full-stack. You could do this for any industry, especially one dominated by slow-moving
> incumbents. Instead of selling to the dinosaurs, you could make them extinct.

## Categories (pick exactly one)

| category | meaning |
|---|---|
| `full_stack_ai` | The company **is** the service provider: it delivers the end service to customers itself (it is the law firm, accounting or tax firm, clinic, insurance agency, brokerage, recruiter, property manager, freight forwarder, customs broker, lender, call centre, design studio, etc.) and AI (LLMs, agents, or robots) does the core work. It competes with the industry's incumbents instead of selling software to them. |
| `sells_ai_to_industry` | Sells AI software, agents, copilots or "AI employees" to businesses or professionals who keep delivering the service themselves. The "build an agent and sell it to law firms" case. Includes horizontal AI tools sold to companies (sales, support, coding agents sold to dev teams, etc.). |
| `ai_infra` | Models, inference, training, GPUs, data labelling, evals, observability, agent frameworks, vector DBs: AI for people building AI. |
| `ai_other` | AI is central but the company fits none of the above: consumer AI apps, AI companions, AI hardware or robots sold as products, AI-first marketplaces that only match parties. |
| `full_stack_non_ai` | Operates the end service itself and competes with incumbents (a tech-enabled clinic, bank, brokerage, law firm, logistics operator), but AI is not what does the core work, or the description does not say it is. |
| `not_ai` | No meaningful AI component and not a full-stack service company: ordinary SaaS, fintech, marketplaces, hardware, biotech, consumer apps. |
| `unclear` | The description is missing or too thin to decide. |

## Rules

- Judge by what the company does for its customers, not by the words "AI" or "full-stack" in the copy. Many
  descriptions call an integration "full-stack"; that is not this definition.
- `full_stack_ai` needs both halves: the company delivers the service **and** AI/agents/robots do the core work.
  "AI-native law firm", "we are an accounting firm run by agents", "we operate the clinic; agents handle intake,
  coding and billing", "we are the freight forwarder" all qualify. "AI agent for law firms" does not.
- A company that sells to the same incumbents it could replace is `sells_ai_to_industry`, even if it also runs a small
  managed service on the side. Go by the primary business.
- A marketplace or platform that matches customers with human providers is not full stack unless it employs or
  operates the providers.
- Robotics that the company operates as a service (a robot-run warehouse, a robotic construction contractor) is
  `full_stack_ai`; robots sold as products are `ai_other`.
- Descriptions are YC's current text, so a company may describe a pivot; classify the current description.
- Confidence: `high` when the description states the model plainly, `medium` when inferred, `low` when guessed.

## Output

One JSON object per input line, same order, fields: `id` (copied), `category`, `confidence`, `reason` (one clause,
at most 20 words, quoting the deciding phrase where possible).
