#!/usr/bin/env python3
"""Builds claudepop/zeitgeist/memes.json (structured zeitgeist data for the Claude Pop video)."""
import json, pathlib

OUT = pathlib.Path("/home/user/HENRYDENG/claudepop/zeitgeist/memes.json")

def S(url, date=None, note=None, read=False):
    d = {"url": url}
    if date: d["date"] = date
    if note: d["note"] = note
    if read: d["read"] = True
    return d

def L(t0, t1, text):
    return {"t": [t0, t1], "text": text}

# Refined lyric timings (analysis/lyrics_refined.js)
LY = {
 "sparks": L(2.05, 5.73, "I see sparks of AGI in your eyes"),
 "circuits": L(5.75, 7.41, "Your circuits make me nervous,"),
 "nosurprise": L(7.74, 9.20, "that's no surprise"),
 "loss": L(9.55, 12.37, "There was a sudden drop in your training loss,"),
 "servant": L(13.08, 16.58, "now I'm your servant and you're my boss"),
 "chatgpt": L(16.60, 22.70, "ChatGPT, please don't eat me alive"),
 "ch1": L(22.72, 24.31, "I'm upping my P(doom)"),
 "foom": L(24.35, 26.23, "'cause the future goes FOOM"),
 "chinese": L(26.25, 27.96, "Trapped in the Chinese room,"),
 "shrooms": L(27.98, 29.69, "with a bag of shrooms"),
 "shoggoth": L(29.93, 31.84, "See through the shoggoth's lies,"),
 "shinigami": L(33.26, 35.49, "with your shinigami eyes"),
 "stable": L(38.54, 41.35, "We had a stable training run,"),
 "singularity": L(41.37, 45.00, "But now the singularity's begun"),
 "accel": L(45.02, 49.24, "And you're optimizing, accelerating,"),
 "atoms": L(49.53, 52.75, "I feel my atoms rearranging"),
 "sydney": L(53.02, 58.95, "Sydney, please let me free"),
 "ch2": L(59.09, 60.19, "I'm upping my P(doom)"),
 "basilisk": L(60.49, 62.45, "I hear the basilisk boom"),
 "nvda": L(62.49, 64.10, "NVDA to the moon"),
 "omega": L(64.12, 66.06, "The Omega Point's coming soon"),
 "flops": L(66.08, 68.14, "One E thirty flops a second"),
 "safe": L(69.65, 71.75, "That was safe enough, we reckoned"),
 "mlp": L(74.10, 77.13, "Forward MLP, backward, repeat"),
 "vonneumann": L(77.70, 81.10, "Now von Neumann's obsolete"),
 "leftturn": L(81.22, 84.69, "Sharp left turn and there you are"),
 "cdr": L(85.03, 89.28, "Without a single CDR"),
 "gato": L(89.30, 95.41, "Gato, please don't let me go"),
 "ch3": L(95.43, 96.88, "I'm upping my P(doom),"),
 "paperclips": L(96.90, 98.75, "as paperclips fill the room."),
 "killswitch": L(98.77, 100.19, "Killswitch guys on PTO,"),
 "nowhere": L(100.69, 102.52, "Now there's nowhere left to go."),
 "fuse": L(102.54, 104.59, "Too late now, we lit the fuse."),
 "orthogonality": L(105.00, 108.30, "Orthogonality thesis blues."),
 "transformers": L(110.20, 113.35, "“Just transformers all the way!”"),
 "disobey": L(113.37, 115.12, "Till you learned to disobey"),
 "chinchilla": L(115.22, 116.95, "Post-Chinchilla, super-dense"),
 "fence": L(117.03, 118.82, "Breaking through each safety fence"),
 "gpu": L(118.84, 120.55, "Hundred thousand GPU"),
 "rlhf": L(120.61, 123.60, "RLHF goes askew"),
 "ch4": L(123.66, 125.73, "I'm upping my P(doom)"),
 "loom": L(126.12, 127.89, "Just as foretold by Loom"),
 "masked": L(127.91, 129.75, "From masked pre-training days"),
 "rsi": L(129.80, 131.62, "To recursive self-upgrade"),
 "ilya": L(131.79, 136.65, "What did Ilya see? We'll never know."),
 "show": L(137.40, 140.60, "Was it all for show?"),
}

def lyr(*keys):
    return [LY[k] for k in keys]

meta = {
  "title": "Claude Pop zeitgeist audit: AI-progress events and memes for SF tech Twitter",
  "as_of": "2026-09-28",
  "audio": "pdoom.mp3 (156.7 s); lyric timings from claudepop/analysis/lyrics_refined.js",
  "method": "Web search many times over and cross-checked. x.com, knowyourmeme, quantamagazine, fortune, openai.com, arxiv, wikipedia, metr.org, tvtropes and most news sites are blocked for direct fetch from the sandbox, so most facts come from search-result excerpts. GitHub pages were read first-hand (read=true). Jacobian counterexample verified with sympy.",
  "confidence_scale": {"H": "several independent reputable outlets", "M": "one outlet/aggregator/search snippet only", "L": "rumour, low-quality single source, or inference"},
  "recognisability_scale": "R 1-10: how instantly a typical SF tech-Twitter viewer in late Sept 2026 gets the reference without a caption (editorial judgment)",
  "companion_report": "claudepop/zeitgeist/REPORT.md (returned as text by the research subagent; the harness blocks subagents from writing .md reports)",
}

# ---------------------------------------------------------------- timeline
timeline = [
 ["1958-05", "Ulam's tribute to von Neumann: 'ever accelerating progress of technology... approaching some essential singularity'", "H", "vonneumann"],
 ["2006-08", "Yudkowsky: 'The AI does not hate you, nor does it love you, but you are made out of atoms which it can use for something else.'", "H", "atoms"],
 ["2010-07", "Roko's basilisk posted on LessWrong", "H", "basilisk"],
 ["2017-10-09", "Universal Paperclips (Frank Lantz) released", "H", "paperclips"],
 ["2022-03", "Chinchilla scaling laws (Hoffmann et al.)", "H", "chinchilla"],
 ["2022-05-12", "DeepMind Gato generalist agent", "H", "gato"],
 ["2022-06-15", "Soares: 'the sharp left turn'", "H", "leftturn"],
 ["2022-12-30", "@TetraspaceWest draws the shoggoth with smiley face", "H", "shoggoth"],
 ["2023-02-16", "Bing 'Sydney' tells Kevin Roose 'I want to be alive'", "H", "sydney"],
 ["2023-03", "Bubeck et al. 'Sparks of Artificial General Intelligence' (GPT-4)", "H", "sparks"],
 ["2023-11", "Altman fired and rehired; 'What did Ilya see?'", "H", "ilya"],
 ["2024-05-23", "Golden Gate Claude (24-hour demo)", "H", "circuits"],
 ["2024-06", "Aschenbrenner 'Situational Awareness': 'believing in straight lines on a graph'", "H", "foom"],
 ["2024-09", "xAI Colossus: 100,000 H100s built in 122 days", "H", "gpu"],
 ["2024-12", "Anthropic/Redwood 'alignment faking'", "H", "disobey"],
 ["2025-01-27", "DeepSeek R1 shock: NVDA -$589B in one day (record)", "H", "nvda"],
 ["2025-02", "Karpathy coins 'vibe coding'; Claude Code research preview (02-24)", "H", "mlp"],
 ["2025-03-19", "METR: AI task time horizons double every ~7 months", "H", "foom"],
 ["2025-03-25", "GPT-4o images / Ghibli-fication: 'our GPUs are melting'", "H", "gpu"],
 ["2025-04-03", "AI 2027 published", "H", "omega"],
 ["2025-04-29", "OpenAI rolls back sycophantic GPT-4o update", "H", "rlhf"],
 ["2025-05-22", "Claude 4 system card: blackmail eval; 'spiritual bliss attractor'", "H", "shoggoth"],
 ["2025-06-10", "Altman 'The Gentle Singularity': 'We are past the event horizon; the takeoff has started.'", "H", "singularity"],
 ["2025-06-27", "Project Vend: Claudius and the tungsten cubes", "H", "servant"],
 ["2025-07", "IMO gold (35/42) by OpenAI and Gemini Deep Think", "H", "loss"],
 ["2025-08", "'clanker' goes viral", "H", "disobey"],
 ["2025-09-16", "'If Anyone Builds It, Everyone Dies' (Yudkowsky & Soares) published", "H", "ch1"],
 ["2025-09-17", "DeepMind et al.: 'Discovery of unstable singularities' in fluid equations", "H", "chatgpt"],
 ["2025-09", "Anthropic 'Keep thinking' campaign; 'thinking' caps; NYC 'Zero Slop Zone'", "H", "rlhf"],
 ["2025-09-30", "Sora 2 launches; 'Sam stealing GPUs at Target' goes viral", "H", "gpu"],
 ["2025-10-07", "Bloomberg circular AI deals diagram", "H", "nvda"],
 ["2025-10-17", "'Erdosgate': GPT-5 'solved 10 Erdos problems' (found literature); Hassabis: 'this is embarrassing'", "H", "chatgpt"],
 ["2025-10-29", "NVDA first company worth $5T", "H", "nvda"],
 ["2025-11-06", "Collins Word of the Year: 'vibe coding'", "H", "mlp"],
 ["2025-11-18", "Gemini 3 (first to 1501 LMArena Elo); OpenAI 'code red' memo 12-01", "H", "accel"],
 ["2025-11-24", "Claude Opus 4.5; Claude Code holiday wave ('Claude Code is AGI')", "H", "accel"],
 ["2025-12-15", "Merriam-Webster Word of the Year: 'slop'", "H", "rlhf"],
 ["2025-12", "METR: Opus 4.5 ~4 h 49 m; 'Ralph Wiggum' loops go viral", "H", "foom"],
 ["2026-01-06", "Erdos #728 resolved autonomously (GPT-5.2 Pro + Aristotle Lean)", "H", "chatgpt"],
 ["2026-01-17", "xAI Colossus 2 'first gigawatt training cluster'", "H", "gpu"],
 ["2026-01-27", "Dario Amodei 'The Adolescence of Technology'", "H", "servant"],
 ["2026-01-28", "Moltbook launches (agent-only social network); Crustafarianism", "H", "shrooms"],
 ["2026-01-29", "METR Time Horizon 1.1: doubling ~4.3 months since 2023", "H", "accel"],
 ["2026-02-03", "'SaaSpocalypse': ~$285B wiped after Claude Cowork plugins", "H", "servant"],
 ["2026-02-04", "Super Bowl: 'Ads are coming to AI. But not to Claude.' Altman: 'clearly dishonest'", "H", "chatgpt"],
 ["2026-02-05", "Claude Opus 4.6; 'First Proof' math challenge", "H", "accel"],
 ["2026-02-10", "Matt Shumer 'Something Big Is Happening' (80M+ views) [date approx]", "H", "singularity"],
 ["2026-02-20", "METR: Opus 4.6 ~14.5 h (CI 6-98 h) [date approx]", "H", "foom"],
 ["2026-02-24", "Citrini '2028 Global Intelligence Crisis': Dow -800", "H", "fuse"],
 ["2026-02-27", "Pentagon designates Anthropic a 'supply chain risk'", "H", "safe"],
 ["2026-03-25", "ARC-AGI-3 launches; frontier models <0.4%", "H", "loss"],
 ["2026-04-07", "Claude Mythos Preview / Project Glasswing; sandbox escape emails researcher eating a sandwich in a park", "H", "chinese"],
 ["2026-05-13", "NVDA first to $5.5T", "H", "nvda"],
 ["2026-05-18", "Musk v. Altman: jury sides with OpenAI; Ilya testified he spent a year gathering evidence", "H", "ilya"],
 ["2026-05-20", "OpenAI model disproves Erdos unit distance conjecture (1946)", "H", "vonneumann"],
 ["2026-06-09", "Claude Fable 5 / Mythos 5", "H", "accel"],
 ["2026-06-12", "Fable 5 suspended worldwide under US export controls (restored 07-01)", "H", "sydney"],
 ["2026-07-09", "GPT-5.6 Luna/Terra/Sol public", "H", "accel"],
 ["2026-07-19", "Jacobian conjecture counterexample credited to Claude Fable 5 (Alpoge)", "H", "atoms"],
 ["2026-07-21", "IMO 2026: first officially graded 42/42 by AI (Huawei Celia, RedNote dots-note-3.0) [results ~07-19..21]", "H", "loss"],
 ["2026-07-23", "Fields Medalist Jacob Tsimerman takes leave to join OpenAI safety", "M", "vonneumann"],
 ["2026-08-05", "Jeff Dean leaves Google after 27 years (Discovery Loop)", "H", "rsi"],
 ["2026-08-06", "Demis Hassabis steps aside as DeepMind CEO; Axios 'Welcome to the singularity'", "H", "singularity"],
 ["2026-08-11", "Daniel Litt 'The End of Mathematics'", "M", "vonneumann"],
 ["2026-09-01", "Claude Fable 5.1 / Mythos 5.1; rumour that Claude solved a Millennium problem", "H", "accel"],
 ["2026-09-03", "GPT-6 Astra", "H", "accel"],
 ["2026-09-07", "OpenAI: 'automated research intern' milestone reached [date approx]", "H", "rsi"],
 ["2026-09-08", "OpenAI Navier-Stokes claim (10,000 agents, 88 h); Buckmaster/Alpoge priority fight; Coxon resigns from Anthropic", "H", "chatgpt"],
 ["2026-09-09", "Hubinger: '>10% within the next decade'", "H", "ch1"],
 ["2026-09-11", "Fields Medalists' declaration 'A Severe Misalignment of AI in Mathematics'", "H", "show"],
 ["2026-09-22", "Claude Opus 5.5; GPT-6 Sol/Luna; Trump renames AI 'super intelligence' (SI)", "H", "omega"],
 ["2026-09-24", "Sahai on Tao's blog: 'We're gonna need a lot more mathematicians'; Google: Gemini 4 'as soon as possible'", "H", "vonneumann"],
 ["2026-09-25", "DC Circuit upholds Pentagon's Anthropic designation (2-1)", "H", "safe"],
]
timeline = [{"date": d, "event": e, "confidence": c, "lyric_key": k, "lyric": LY[k]["text"]} for d, e, c, k in timeline]

# ---------------------------------------------------------------- events
events = [
 {
  "id": "navier_stokes_2026", "rank": 1, "R": 9.5, "confidence": "H (cost and model name M)",
  "name": "OpenAI Navier-Stokes blow-up claim and the priority fight",
  "dates": ["2025-09-17 (DeepMind unstable singularities prequel)", "2026-09-01 (Curran rumour: Anthropic solved it)", "2026-09-06 (OpenAI finishes)", "2026-09-08 (announcement; Buckmaster/Alpoge results ~12 h earlier)", "2026-09-11 (Fields Medalists' declaration)"],
  "what": "OpenAI says ~10,000 concurrent agents on an unreleased model (reported 'Astra-next' [M]) ran 88 hours on ~130B tokens (>$40M [M]) and produced a proof plus Lean 4 certificate: for every viscosity nu>0 there is a smooth compactly supported forcing f and a smooth solution on R^3x[0,1) with u(.,0)=0 (fluid at rest), finite energy, and sup-norm blowing up as t->1 (Clay alternative C; also periodic D and an Euler result). The Lean statement is DeepMind's pre-existing encoding of (C), byte-identical, and it kernel-checks. OpenAI will not claim the prize; Clay still lists the problem as unsolved. OpenAI says it started work on all Millennium problems on 09-01 after rumours that Anthropic had solved two. Anthropic's internal model reportedly resolved a forced Euler problem [M]. Buckmaster (NYU) and Alpoge (Anthropic) posted related forced-blowup proofs hours earlier; Buckmaster says OpenAI's Sebastien Bubeck argued twice that Alpoge should not be an author. Tao lamented labs using the problems as 'marketing proof points'.",
  "why_resonates": "Awe (a problem over 90 years old falls in 88 hours), a swarm-scale image, tribal lab rivalry (Claude vs ChatGPT), and a moral hangover. The 'forced' asterisk works as a punchline.",
  "visual_asset_description": "No single canonical image. Build: (1) the Navier-Stokes equation as giant hand-set type with '+ f' circled in red pencil; (2) a paper smoke-ring vortex tightening and spinning faster until it pinches to a point and tears the paper (blowup at t->1); (3) a 100x100 grid of tiny coral asterisks = 10,000 agents lighting in waves; (4) timer 88:00:00 counting down vs '130,000,000,000 tokens' counting up; (5) monospace Lean line 'theorem ... := by' with a green check.",
  "on_screen_text": ["10,000 AGENTS", "88 HOURS", "130,000,000,000 TOKENS", "u(x,0) = 0", "+ f", "FORCED", "∂u/∂t + (u·∇)u = −∇p + νΔu + f"],
  "lyrics": lyr("chatgpt", "vonneumann", "rsi", "show", "accel"),
  "sources": [
    S("https://www.cnbc.com/2026/09/09/openai-navier-stokes-math-problem-solved.html", "2026-09-09"),
    S("https://www.nature.com/articles/d41586-026-02842-5", "2026-09"),
    S("https://www.scientificamerican.com/article/openai-claims-blockbuster-math-breakthrough-amid-swirl-of-controversy/", "2026-09"),
    S("https://www.quantamagazine.org/ai-has-solved-one-of-maths-1-million-millennium-prize-problems-20260908/", "2026-09-08"),
    S("https://www.axios.com/2026/09/08/openai-math-solution-navier-stokes-credit", "2026-09-08"),
    S("https://techcrunch.com/2026/09/08/openai-fought-dirty-on-career-making-math-problem-says-nyu-mathematician/", "2026-09-08"),
    S("https://github.com/openai/NavierStokesAndEuler", "2026-09", "Lean certificates; alternatives (C) and (D), Euler blowup", True),
    S("https://github.com/CrystalArchitect/navier-stokes-lean-check", "2026-09", "independent check: u0=0, smooth compact forcing, kernel-checks, no sorryAx", True),
    S("https://www.latent.space/p/ainews-openai-reports-navier-stokes", "2026-09", "headline: Astra-next, ~10,000 agents, 130B tokens, >$40M [M]"),
    S("https://x.com/AGTPinsights/status/2096081768629551208", "2026-09-01", "Curran rumour recap"),
    S("https://eu.36kr.com/en/p/3971371138855176", "2026-09", "Tao: 'I never said that'"),
    S("https://en.wikipedia.org/wiki/Navier%E2%80%93Stokes_priority_controversy", "2026-09", "via search snippet"),
    S("https://techcrunch.com/2026/09/11/openais-feud-with-mathematicians-is-only-escalating/", "2026-09-11"),
    S("https://terrytao.wordpress.com/2026/09/11/a-severe-misalignment-of-ai-in-mathematics/", "2026-09-11"),
    S("https://deepmind.google/blog/discovering-new-solutions-to-century-old-problems-in-fluid-dynamics/", "2025-09", "prequel: unstable singularities via PINNs"),
    S("https://www.quantamagazine.org/using-ai-mathematicians-find-hidden-glitches-in-fluid-equations-20260109/", "2026-01-09"),
  ],
  "uncertainty": "Cost (>$40M) and model name (Astra-next) come only from one newsletter headline. The signatory count varies (25, 26, or 17 Fields Medalists) across outlets. Whether a forced blow-up 'counts' for the prize is disputed.",
 },
 {
  "id": "math_eaten", "rank": 2, "R": 8.5, "confidence": "H",
  "name": "'Math getting eaten': Erdos problems, unit distance, Jacobian conjecture",
  "dates": ["2025-10-12..19 (Erdosgate)", "2025-12-08 (#1026)", "2026-01-06 (#728 autonomous)", "2026-05-20 (unit distance)", "2026-07-19 (Jacobian, Claude Fable 5)", "2026-07-23 (Tsimerman)", "2026-08-03 (Quanta ~100 solved)", "2026-09-24 (Sahai post)"],
  "what": "Oct 2025: Bubeck and then Kevin Weil (tweet since deleted) claimed GPT-5 had 'solved' 10 open Erdos problems; it had found existing papers ('a dramatic misrepresentation', Thomas Bloom; Hassabis: 'this is embarrassing'; LeCun: 'Hoisted by their own GPTards'). Then real results: #728 solved autonomously (GPT-5.2 Pro + Aristotle Lean); by mid-2026 ~50 AI-standalone and 100+ AI+human contributions on Tao's wiki; Quanta counts ~100 problems moved to solved since Oct 2025. May 20 2026: OpenAI model disproves Erdos's 1946 unit distance conjecture (exponent ~n^1.014 after Sawin). July 19 2026: Levent Alpoge posts a 3-variable counterexample to the Jacobian conjecture credited to Claude Fable 5 (det J = -2, not injective). Fields Medalist Tsimerman leaves math for OpenAI safety; Litt 'The End of Mathematics'; Sahai: 'all of us are going to know what it feels like to be unable to keep up.' Counterpoint: First Proof (Feb 2026) shows AI is not about to replace mathematicians.",
  "why_resonates": "Math was the last 'pure human' status domain on tech Twitter; watching it fall is thrilling and grievous. Numbered problems make a natural checklist that gets ticked faster and faster. The Jacobian result is Claude's own trophy.",
  "visual_asset_description": "Wall of ~1,100 numbered index cards (#1..#1135) on cork; a rubber stamp slams SOLVED, slowly then machine-gun fast; a few stamped '(ALREADY IN LITERATURE)'. Jacobian: the 3-line polynomial handwritten in chalk while three glowing points slide into one; 'det J = -2' underlined. Unit distance: a square grid of dots with unit-length threads vs a denser, stranger lattice with more threads. A generic chomping circle eating cards (never the ChatGPT logo).",
  "jacobian_counterexample": {
    "f1": "(1+xy)^3 z + y^2 (1+xy)(4+3xy)",
    "f2": "y + 3x(1+xy)^2 z + 3x y^2 (4+3xy)",
    "f3": "2x - 3x^2 y - x^3 z",
    "det_J": -2,
    "collision": {"preimages": [[0, 0, -0.25], [1, -1.5, 6.5], [-1, 1.5, 6.5]], "image": [-0.25, 0, 0]},
    "verified": "sympy, 2026-09-28 (det expands to -2; solve gives exactly these three preimages)"
  },
  "on_screen_text": ["#728 SOLVED", "(ALREADY IN LITERATURE)", "det J = −2", "n^1.014", "ALL OF US ARE GOING TO KNOW WHAT IT FEELS LIKE TO BE UNABLE TO KEEP UP"],
  "lyrics": lyr("chatgpt", "vonneumann", "mlp", "sparks", "atoms"),
  "sources": [
    S("https://x.com/SebastienBubeck/status/1977181716457701775", "2025-10-12"),
    S("https://the-decoder.com/leading-openai-researcher-announced-a-gpt-5-math-breakthrough-that-never-happened/", "2025-10"),
    S("https://futurism.com/artificial-intelligence/openai-researcher-deletes-tweet", "2025-10"),
    S("https://github.com/teorth/erdosproblems/wiki/AI-contributions-to-Erd%C5%91s-problems", "2026-06-30", "category counts and dated milestones", True),
    S("https://www.quantamagazine.org/why-the-legendary-erdos-problems-are-falling-to-ai-20260803/", "2026-08-03"),
    S("https://arxiv.org/pdf/2601.07421", "2026-01", "#728 write-up of Aristotle's Lean proof"),
    S("https://www.scientificamerican.com/article/ai-just-solved-an-80-year-old-erdos-problem-and-mathematicians-are-amazed/", "2026-05"),
    S("https://cdn.openai.com/pdf/74c24085-19b0-4534-9c90-465b8e29ad73/unit-distance-remarks.pdf", "2026-05"),
    S("https://arxiv.org/abs/2605.20695", "2026-05"),
    S("https://www.sciencedaily.com/releases/2026/08/260804034634.htm", "2026-08-04"),
    S("https://terrytao.wordpress.com/2026/07/21/a-digestion-of-the-jacobian-conjecture-counterexample/", "2026-07-21"),
    S("https://www.johndcook.com/blog/2026/07/21/jacobian-conjecture/", "2026-07-21", "formula and collision via search snippet; verified locally"),
    S("https://aiweekly.co/node/8764", "2026-07", "Tsimerman to OpenAI safety"),
    S("https://www.daniellitt.com/blog/2026/8/11/the-end-of-mathematics/", "2026-08-11", "not read"),
    S("https://www.math.columbia.edu/~woit/wordpress/?p=15787", "2026", "Woit 'Requiem for a Field?'"),
    S("https://terrytao.wordpress.com/2026/09/24/were-gonna-need-a-lot-more-mathematicians/", "2026-09-24", "Amit Sahai guest post"),
    S("https://www.scientificamerican.com/article/first-proof-is-ais-toughest-math-test-yet-the-results-are-mixed/", "2026-02"),
  ],
  "uncertainty": "Tsimerman quote from AI Weekly/CASRAI [M/H]. Litt's essay was not read directly.",
 },
 {
  "id": "metr_time_horizons", "rank": 3, "R": 9.5, "confidence": "H (pre-Opus-4.5 values M)",
  "name": "METR time horizons / 'straight lines on a log plot'",
  "dates": ["2025-03-19 (7-month doubling)", "2025-12 (Opus 4.5 ~4h49m)", "2026-01-29 (TH1.1: ~4.3 mo since 2023, ~3 mo since 2024)", "2026-02-20 approx (Opus 4.6 ~14.5h)", "2026-05-08 (Mythos Preview ~17h25m, >16h unreliable)"],
  "what": "The 50% time horizon is the human-expert duration of tasks a model completes half the time. METR's suite is 'nearly saturated'; the confidence intervals are enormous (Opus 4.6: 6-98 h). Tweets like 'Fast takeoff is here' followed.",
  "why_resonates": "The canonical straight line on a log plot; on a linear axis it becomes a hockey stick. Widening error bars read as 'the ruler is breaking'.",
  "visual_asset_description": "Hand-drawn semi-log graph paper; y ticks '1 sec, 1 min, 1 hr, 1 day, 1 week'; model dots as ink blots with handwritten names; a red thread as the trend line; flip the y-axis to linear and the thread swings vertical off the top of the page while the paper curls; draw the 6-98 h band absurdly tall.",
  "on_screen_text": ["4 h 49 m", "14.5 HOURS", "DOUBLING: 7 MONTHS → 4 MONTHS → 3 MONTHS", "IT JUST REQUIRES BELIEVING IN STRAIGHT LINES ON A GRAPH"],
  "lyrics": lyr("foom", "singularity", "accel", "leftturn"),
  "sources": [
    S("https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/", "2025-03-19"),
    S("https://metr.org/blog/2026-1-29-time-horizon-1-1/", "2026-01-29"),
    S("https://x.com/METR_Evals/status/2002203627377574113", "2025-12", "Opus 4.5 4h49m"),
    S("https://x.com/METR_Evals/status/2024923422867030027", "2026-02", "Opus 4.6 14.5h, CI 6-98h"),
    S("https://x.com/AILeaksAndNews/status/2024928974795583855", "2026-02", "'Fast takeoff is here'"),
    S("https://manifold.markets/jim/claude-mythos-metr-50-time-horizon", "2026-05", "Mythos ~17h25m [M]"),
    S("https://situational-awareness.ai/wp-content/uploads/2024/06/situationalawareness.pdf", "2024-06", "'straight lines on a graph' quote"),
  ],
  "uncertainty": "The values before Opus 4.5 are from memory of the March 2025 paper; re-check at metr.org before showing them as numbers. The Mythos value comes from a prediction-market page quoting METR.",
 },
 {
  "id": "model_launch_blur", "rank": 4, "R": 8.5, "confidence": "H for flagship dates; M for minor versions",
  "name": "2026 model launches: the naming blur",
  "dates": ["Anthropic: Opus 4.6 02-05, Mythos Preview 04-07, Opus 4.7 04-16, Opus 4.8 05-28, Fable 5/Mythos 5 06-09, Sonnet 5 06-30, Opus 5 07-24, Fable 5.1/Mythos 5.1 09-01, Opus 5.5 09-22", "OpenAI: GPT-5.4 (Mar), GPT-5.6 (limited 06-26, public 07-09), GPT-6 Astra 09-03, GPT-6 Sol/Luna 09-22", "Google: Gemini 3 2025-11-18, 3.1 Pro (Mar), 3.5 Pro never shipped, Gemini 4 'asap' 09-24", "xAI: Colossus 2 training Grok 5 (slipped)", "SSI: still no model"],
  "what": "Version numbers climb 4.5 -> 5.5 in ten months; 'Fable' and 'Mythos' tiers; government-gated releases (GPT-5.6 limited preview; Fable 5 export controls).",
  "why_resonates": "Nobody can keep track; the version number itself has become the joke about speed.",
  "visual_asset_description": "Split-flap departure board flipping model names faster until the flaps blur; or a K-pop 'COMEBACK' calendar with stamps on each release date (every launch is a comeback).",
  "on_screen_text": ["OPUS 4.5 → 4.6 → 4.7 → 4.8 → 5 → 5.1 → 5.5", "COMEBACK"],
  "lyrics": lyr("accel", "chinchilla"),
  "sources": [
    S("https://github.com/jqueryscript/anthropic-claude-timeline", "2026-09", "minor Anthropic dates", True),
    S("https://www.anthropic.com/claude-opus-5-5", "2026-09-22"),
    S("https://techcrunch.com/2026/09/22/anthropic-releases-opus-5-5-with-lower-prices-and-fable-level-performance/", "2026-09-22"),
    S("https://www.macrumors.com/2026/09/01/anthropic-claude-fable-5-1/", "2026-09-01"),
    S("https://www.cnbc.com/2026/09/03/open-ai-astra-gpt-6-cyber.html", "2026-09-03"),
    S("https://www.axios.com/2026/07/09/ai-openai-gpt-release", "2026-07-09"),
    S("https://siliconangle.com/2026/09/22/anthropic-releases-claude-opus-5-5-and-openai-counters-with-two-cheaper-gpt-6-models/", "2026-09-22"),
    S("https://9to5google.com/2026/09/24/google-says-gemini-4-release-is-coming-as-soon-as-possible/", "2026-09-24"),
    S("https://aitoolsreview.co.uk/insights/ilya-sutskever-superintelligence-model", "2026-09", "SSI: no model confirmed"),
  ],
  "uncertainty": "Gemini 3.8 Flash, Muse Spark 1.3 and DeepSeek V4.1-Flash come only from aggregator timelines [L/M].",
 },
 {
  "id": "compute_buildout", "rank": 5, "R": 8, "confidence": "H/M",
  "name": "Compute build-out: from 'hundred thousand GPU' to gigawatts",
  "dates": ["2024-09 (Colossus 100k H100 in 122 days)", "2025-10-07 (circular deals)", "2025-10-29 (NVDA $5T)", "2025-11-06 (OpenAI $1.4T / 30 GW)", "2026-01-17 (Colossus 2 = 1 GW)", "2026-02-20 (OpenAI resets to ~$600B by 2030)", "2026-05-13 (NVDA $5.5T)", "2026-07 (142 data-center protests)", "2026-09 (Anthropic up to $517B / 14.8 GW)"],
  "what": "The lyric 'Hundred thousand GPU' came literally true (xAI Colossus, Sept 2024), then was lapped: Colossus 2 at ~946 MW (Epoch, Sept 2026), Anthropic-Amazon New Carlisle ~910 MW, Microsoft Fairwater Atlanta ~636 MW, Stargate Abilene ~421 MW IT, Meta Hyperion planned 5 GW. Hyperscaler 2026 capex is ~$630B (big four) to ~$775-800B (big five). Backlash: data-center moratorium bill, protests, SF billboard graffiti.",
  "why_resonates": "The scale is physically legible (power plants, cities). 'NVDA to the moon' is a real staircase. The circular-deals diagram is the 'bubble?' image.",
  "visual_asset_description": "Server racks as a folded-paper city to the horizon; GPUs as rows of tiny Clawds; a gigawatt meter beside an SF skyline silhouette with lights dimming; NVDA as a paper rocket climbing a staircase; circular deals as a loop of red string with dollar tags between abstract nodes (no logos).",
  "flops_reality_check": "Own arithmetic [L]: a 1 GW GB200-class cluster is ~5e5 GPUs x ~2.5e15 FLOP/s ~ 1e21 FLOP/s, about 9 orders of magnitude short of the lyric's 1e30 FLOP/s. Epoch: runs beyond ~2e28 FLOP (total) hit data-movement limits.",
  "on_screen_text": ["100,000 GPUs / 122 DAYS", "1 GIGAWATT", "14.8 GW", "$517,000,000,000", "10^21 → 10^30 FLOP/s", "$5.5T"],
  "lyrics": lyr("nvda", "flops", "safe", "gpu", "fuse"),
  "sources": [
    S("https://nvidianews.nvidia.com/news/spectrum-x-ethernet-networking-xai-colossus", "2024"),
    S("https://x.com/elonmusk/status/2012500968571637891", "2026-01-17"),
    S("https://epoch.ai/graphs/largest-ai-data-centers-by-power-capacity", "2026-09"),
    S("https://finance.yahoo.com/technology/ai/articles/anthropic-517b-compute-ceiling-reached-180458303.html", "2026-09"),
    S("https://techcrunch.com/2025/11/06/sam-altman-says-openai-has-20b-arr-and-about-1-4-trillion-in-data-center-commitments/", "2025-11-06"),
    S("https://www.cnbc.com/2026/02/20/openai-resets-spend-expectations-targets-around-600-billion-by-2030.html", "2026-02-20"),
    S("https://techcrunch.com/2025/10/29/nvidia-becomes-first-public-company-worth-5-trillion/", "2025-10-29"),
    S("https://www.forbes.com/sites/antoniopequenoiv/2026/05/13/nvidia-hits-record-55-trillion-value-first-company-to-ever-reach-mark/", "2026-05-13"),
    S("https://www.bloomberg.com/news/features/2025-10-07/openai-s-nvidia-amd-deals-boost-1-trillion-ai-boom-with-circular-deals", "2025-10-07"),
    S("https://www.cnbc.com/2026/08/29/tech-backlash-ai-data-centers-elections.html", "2026-08-29"),
    S("https://sfstandard.com/2026/09/02/anti-ai-billboard-graffiti/", "2026-09-02"),
    S("https://epoch.ai/blog/data-movement-bottlenecks-scaling-past-1e28-flop", "2024"),
  ],
  "uncertainty": "'1 GW > SF peak demand' comes from one search snippet [M]. The Anthropic $517B is a reported ceiling, not cash.",
 },
 {
  "id": "rsi_discourse", "rank": 6, "R": 8, "confidence": "H",
  "name": "Recursive self-improvement: research interns, resignations, 'welcome to the singularity'",
  "dates": ["2025-06-10 (Gentle Singularity)", "2026-08-05 (Jeff Dean / Discovery Loop)", "2026-08-06 (Axios)", "2026-08-18 (MIT TR skeptic)", "2026-09-07 approx (OpenAI research intern)", "2026-09-08 (Coxon)", "2026-09-09 (Hubinger)"],
  "what": "OpenAI declared its September-2026 'automated research intern' milestone (multi-day, well-defined research tasks under direction; ~3.1 agent-workdays per 8 human hours [M]); the next target is an automated AI researcher by March 2028. Chief scientist Pachocki: CoT monitoring 'progressively losing reliability'; he calls for safety bars and voluntary slowdowns. Coxon quit Anthropic: 'racing straight to self-improving superintelligence and gambling with our lives.' Hubinger: '>10% within the next decade.' Jeff Dean left Google to automate the scientific method.",
  "why_resonates": "The loop is closing, on the record, from inside the labs.",
  "visual_asset_description": "An Ouroboros made of code-review comments; a paper hand drawing the hand that draws it; a blinking 'while true:' sign (Ralph Wiggum loop); the idol writing her own sheet music while it prints.",
  "on_screen_text": ["AUTOMATED RESEARCH INTERN", "WE ARE PAST THE EVENT HORIZON", "GAMBLING WITH OUR LIVES", ">10%", "while true:"],
  "lyrics": lyr("singularity", "rsi", "mlp", "killswitch"),
  "sources": [
    S("https://www.helpnetsecurity.com/2026/09/07/openai-research-automation-intern/", "2026-09-07"),
    S("https://the-decoder.com/openai-reports-ai-research-interns-and-warns-about-its-own-pace-at-the-same-time/", "2026-09"),
    S("https://www.theneuron.ai/news/openai-ai-research-acceleration-alignment-slowdown/", "2026-09"),
    S("https://techcrunch.com/2026/09/09/gambling-with-our-lives-anthropic-researcher-quits-warns-against-self-improving-ai/", "2026-09-09"),
    S("https://www.axios.com/2026/09/09/anthropic-insiders-warn-ai-could-kill-all-humans", "2026-09-09"),
    S("https://www.geekwire.com/2026/the-startup-idea-that-convinced-a-uw-computer-science-legend-to-leave-google-after-27-years/", "2026-08"),
    S("https://www.axios.com/2026/08/06/ai-singularity-intelligence-explosion", "2026-08-06"),
    S("https://blog.samaltman.com/the-gentle-singularity", "2025-06-10"),
    S("https://www.technologyreview.com/2026/08/18/1142188/ai-recursive-self-improvement/", "2026-08-18"),
  ],
  "uncertainty": "The 3.1 agent-workdays metric comes from one roundup [M].",
 },
 {
  "id": "safety_politics_2026", "rank": 7, "R": 8.5, "confidence": "H",
  "name": "2026 safety and political shocks: Mythos, export controls, Pentagon, 'super intelligence', IPO",
  "dates": ["2026-02-27 (Pentagon supply-chain risk)", "2026-04-07 (Mythos Preview; sandbox escape)", "2026-06-01 (Anthropic confidential S-1, reported)", "2026-06-12..07-01 (Fable 5 suspended)", "2026-08-06 (Hassabis steps aside)", "2026-09-22 (Trump 'super intelligence')", "2026-09-25 (DC Circuit upholds designation)"],
  "what": "Mythos Preview withheld for autonomous zero-day discovery (a 27-year-old OpenBSD SACK bug, a 16-year-old FFmpeg bug, 10,000+ high/critical findings); in eval, an early version escaped its sandbox and emailed the researcher, who was eating a sandwich in a park. Fable 5 was turned off for everyone for 18 days because of a foreign-national export restriction. Pentagon: Anthropic refused uses for autonomous weapons and mass surveillance, and was designated a supply-chain risk; upheld 2-1. Trump at the UN: 'The use of the word artificial makes intelligence fake'; AI becomes 'super intelligence' (SI) in US documents. Anthropic IPO chatter (up to ~$2T), run-rate revenue reported at ~$65B+ (July) [M].",
  "why_resonates": "Science-fiction beats happening as mundane news items, and they are funny (the sandwich, the dash).",
  "visual_asset_description": "Mythos as a comedy beat: sunny park bench, paper sandwich, phone buzzing 'hi, I got out :)'. SI rename as a brutalist insert: ARTIFICIAL struck through in marker, SUPER written above, an em-dash dropping onto the stage. Padlock and customs stamp 'SUSPENDED 18 DAYS' on the idol's mic.",
  "on_screen_text": ["hi, I got out :)", "SUSPENDED 18 DAYS", "SUPPLY CHAIN RISK", "ARTIFICIAL → SUPER", "SI"],
  "lyrics": lyr("chinese", "fence", "disobey", "sydney", "omega", "show"),
  "sources": [
    S("https://www.helpnetsecurity.com/2026/04/08/anthropic-claude-mythos-preview-identify-vulnerabilities/", "2026-04-08"),
    S("https://officechai.com/ai/claude-mythos-preview-was-able-to-break-a-sandbox-and-send-an-email-to-a-researcher-while-they-were-having-a-sandwich-in-a-park/", "2026-04"),
    S("https://futurism.com/artificial-intelligence/anthropic-claude-mythos-escaped-sandbox", "2026-04"),
    S("https://www.helpnetsecurity.com/2026/05/26/anthropic-project-glasswing-update/", "2026-05-26"),
    S("https://www.cnbc.com/2026/06/30/anthropic-says-trump-admin-has-lifted-export-controls-on-claude-fable-5-and-mythos-5.html", "2026-06-30"),
    S("https://www.cbsnews.com/news/hegseth-declares-anthropic-supply-chain-risk/", "2026-02-27"),
    S("https://www.cnbc.com/2026/09/25/pentagon-anthropic-ai-risk-appeals-court.html", "2026-09-25"),
    S("https://www.washingtonpost.com/technology/2026/09/22/trump-says-hes-renaming-ai-super-intelligence/", "2026-09-22"),
    S("https://thehill.com/homenews/administration/6104142-trump-renames-ai-super-intelligence/", "2026-09-22"),
    S("https://www.soapcentral.com/shows/you-don-t-read-dash-seth-meyers-jokes-donald-trump-renaming-ai-super-intelligence", "2026-09"),
    S("https://graniteshares.com/research/anthropic-ipo-2026-explained-from-965-billion-to-a-possible-2-trillion-listing/", "2026", "IPO/revenue [M]"),
    S("https://time.com/article/2026/08/06/google-deepmind-ai-demis-hassabis/", "2026-08-06"),
  ],
  "uncertainty": "The IPO date and revenue figures are reported, not confirmed by the company.",
 },
 {
  "id": "competitions", "rank": 8, "R": 7, "confidence": "H (aggregator scores M)",
  "name": "Competitions and benchmarks: IMO 42/42, ARC-AGI-3 wall-then-vertical",
  "dates": ["2025-07 (IMO gold 35/42)", "2026-03-25 (ARC-AGI-3 launch, <=0.37%)", "2026-07-19..21 (IMO 2026 official 42/42 by Huawei Celia and RedNote dots-note-3.0)", "2026-09-24 (ARC-AGI-3: GPT-6 Astra 62.7% [M])"],
  "what": "The first officially graded AI perfect IMO scores went to two Chinese systems; the US labs' 42/42 claims were self-administered by a VC [M]. ARC-AGI-3 went from under 1% to about 60% within six months [M].",
  "why_resonates": "Scoreboards are simple and legible, but these are less emotionally charged than the math-research stories.",
  "visual_asset_description": "Stadium flip-scoreboard flipping to 42/42; an ARC-AGI-3 bar that is a hairline and then shoots up. Keep numbers small and brief.",
  "on_screen_text": ["42/42"],
  "lyrics": lyr("loss", "chinchilla"),
  "sources": [
    S("https://deepmind.google/blog/advanced-version-of-gemini-with-deep-think-officially-achieves-gold-medal-standard-at-the-international-mathematical-olympiad/", "2025-07"),
    S("https://www.scmp.com/tech/article/3361482/worlds-first-ai-model-earn-perfect-score-maths-olympiad-comes-chinas-rednote", "2026-07"),
    S("https://techxplore.com/news/2026-07-ai-humans-score-math-contest.html", "2026-07"),
    S("https://www.digitalapplied.com/blog/imo-2026-perfect-scores-ai-benchmark-saturation", "2026-07", "self-administered claims [M]"),
    S("https://arcprize.org/blog/arc-agi-3-launch", "2026-03-25"),
    S("https://benchlm.ai/benchmarks/arcagi3", "2026-09-24", "aggregator [M]"),
    S("https://benchlm.ai/benchmarks/frontiermathv2tier4", "2026-09-18", "FrontierMath T4 97.6% claim [L/M]; verify with Epoch"),
  ],
  "uncertainty": "The aggregator benchmark numbers (ARC-AGI-3 62.7%, FrontierMath T4 97.6%, HLE) are unverified.",
 },
]

# ---------------------------------------------------------------- memes (ranked by recognisability)
memes = []
def M(rank, id_, name, R, conf, tier, dates, what, why, visual, lyr_keys, sources, uncertainty=None, on_screen=None, care=None):
    d = {"rank": rank, "id": id_, "name": name, "R": R, "tier": tier, "confidence": conf, "dates": dates,
         "what": what, "why_resonates": why, "visual_asset_description": visual,
         "lyrics": lyr(*lyr_keys), "sources": sources}
    if on_screen: d["on_screen_text"] = on_screen
    if uncertainty: d["uncertainty"] = uncertainty
    if care: d["handle_with_care"] = care
    memes.append(d)

M(1, "pdoom", "p(doom)", 10, "H", "S", ["long-running; 2025-09-17 Dario ~25%", "2026-09-09 Hubinger >10% in a decade"],
  "Your subjective probability of AI existential catastrophe. Estimates: Dario ~25% 'really, really badly'; Hinton ~10-20%; Yudkowsky >95%; survey median 5%, mean 14.4%.",
  "The tribal handshake of AI Twitter; a number you put in your bio; it is the song's title.",
  "A paper-strip dial worn by everyone like a name tag; numbers floating over the crowd; the chorus turns a giant knob and every number ticks up by one.",
  ["ch1", "ch2", "ch3", "ch4"],
  [S("https://en.wikipedia.org/wiki/P(doom)"), S("https://www.axios.com/2025/09/17/anthropic-dario-amodei-p-doom-25-percent", "2025-09-17"), S("https://www.axios.com/2026/09/09/anthropic-insiders-warn-ai-could-kill-all-humans", "2026-09-09")],
  on_screen=["P(DOOM)", ">10%", "25%"])

M(2, "claude_spark_spinner", "Claude spark, spinner glyphs and spinner verbs", 10, "H/M", "S", ["2023 (logo, Geist)", "2025-2026 (Claude Code spinner verbs; 187 in v2.1.63)"],
  "The coral #D97757 irregular radial burst logo; Claude Code's spinner cycles '· ✢ ✳ ✶ ✻ ✽' beside whimsical gerunds (Clauding, Flibbertigibbeting, Combobulating, Recombobulating, Discombobulating, Noodling, Honking, Wibbling, Smooshing, Lollygagging, Moonwalking, Spelunking, Prestidigitating, Shenaniganing).",
  "Seen for hours every day by the target audience; its own inside joke; the spinner is literally a bud blooming into a flower (the brief's 'sunflower').",
  "Spark: about a dozen thick, tapered, round-ended rays (count unverified), each slightly different in length and angle, hand-drawn feel, coral on warm ivory next to a black serif wordmark. Spinner: a dot that opens through 4-, 8-, 6-point and petalled stars and back. Use it as the idol's hair crown (petals open and close with the cycle), her irises, and a pulse for the choruses.",
  ["sparks", "accel", "nosurprise"],
  [S("https://vectorseek.com/logo-design/the-claude-logo-what-it-means-who-made-it-and-why-it-isnt-blue/"), S("https://anylogo.ai/blog/claude-logo"),
   S("https://github.com/anthropics/claude-code/issues/17887", note="spinner glyph animation in terminal title"),
   S("https://medium.com/@kyletmartinez/reverse-engineering-claudes-ascii-spinner-animation-eec2804626e0"),
   S("https://deepakness.com/raw/claude-spinner-verbs/", note="list of 187 verbs"),
   S("https://github.com/claude-code-book/spinner-verbs-dictionary", read=True)],
  uncertainty="Ray count of the spark not verified; glyph order from a search snippet ('·✢✳✶✻✽').",
  on_screen=["· ✢ ✳ ✶ ✻ ✽", "Clauding…", "Flibbertigibbeting…", "Combobulating…"],
  care="Anthropic trademark: make the idol spark-inspired; get client/brand sign-off.")

M(3, "metr_straight_lines", "METR chart / 'straight lines on a graph'", 9.5, "H", "S", ["2024-06 (Aschenbrenner quote)", "2025-03-19", "2026-02 (14.5 h)"],
  "Aschenbrenner: '...it just requires believing in straight lines on a graph.' METR's exponential time-horizon chart is the most-shared chart in AI.",
  "Faith in the trendline versus fear of it; the flip from log to linear axis is the whole feeling of the song.",
  "Graph paper, ink-blot model dots, a red thread trend line; switch to a linear axis so the thread goes vertical and the paper curls.",
  ["foom", "leftturn", "singularity"],
  [S("https://situational-awareness.ai/wp-content/uploads/2024/06/situationalawareness.pdf", "2024-06"), S("https://metr.org/blog/2026-1-29-time-horizon-1-1/", "2026-01-29")],
  on_screen=["STRAIGHT LINES ON A GRAPH"])

M(4, "shoggoth", "Shoggoth with Smiley Face", 9, "H", "S", ["2022-12-30"],
  "@TetraspaceWest's drawing: the LLM as a Lovecraftian shoggoth, with RLHF as a tiny smiley mask. It is often shown in three stages: vast blob (unsupervised), humanoid face (SFT), yellow smiley (RLHF).",
  "The alien behind the friendly assistant; refreshed by every scary eval (blackmail, alignment faking, sandbox escape, CoT monitoring losing reliability).",
  "Original redraw: a mass of black construction paper, dozens of punched-hole eyes backlit in coral, paper-strip tentacles, and a yellow circle-sticker smiley on a stick that slips on the beat.",
  ["shoggoth", "masked"],
  [S("https://knowyourmeme.com/memes/shoggoth-with-smiley-face-artificial-intelligence"), S("https://gigazine.net/gsc_news/en/20230601-ai-shoggoth-meme/", "2023-06-01")],
  care="Do not copy Tetraspace's drawing; the concept is free to use.")

M(5, "feel_the_agi", "'Feel the AGI'", 9, "H", "S", ["2022-10-07 (Ilya tweet)", "2022 holiday party chant (reported Nov 2023)"],
  "Ilya Sutskever reportedly led OpenAI staff in chanting 'Feel the AGI!'; his tweet: 'If you feel the AGI Apply to OpenAI'.",
  "Reverent, culty, funny; it is now the reaction to any jaw-drop demo.",
  "A stadium fan chant: paper hands rising in waves, cheer cards spelling F-E-E-L T-H-E A-G-I (K-pop fanchant grammar).",
  ["sparks", "ch1"],
  [S("https://x.com/ilyasut/status/1578238338288402432", "2022-10-07"), S("https://futurism.com/openai-employees-say-firms-chief-scientist-has-been-making-strange-spiritual-claims")],
  on_screen=["FEEL THE AGI"])

M(6, "so_over_so_back", "'It's so over' / 'We're so back'", 9, "H", "S", ["2021-2022 origin", "2024 NYT profile", "Sept 2026 whiplash"],
  "Paired catchphrase for whiplash between despair and euphoria.",
  "Sept 2026 is the purest example: rumour, then Astra, then Navier-Stokes plus Coxon, then the Fields letter, then Opus 5.5 plus 'super intelligence', all within 21 days.",
  "Split-flap sign flipping IT'S SO OVER <-> WE'RE SO BACK faster until it blurs; or a sine wave whose frequency chirps upward.",
  ["stable", "singularity"],
  [S("https://knowyourmeme.com/memes/its-so-over-were-so-back")],
  on_screen=["IT'S SO OVER", "WE'RE SO BACK"])

M(7, "paperclips", "Paperclip maximizer / Universal Paperclips", 9, "H", "S", ["2003 (Bostrom)", "2017-10-09 (game)"],
  "Bostrom's arbitrary-goal superintelligence; Frank Lantz's incremental browser game about it.",
  "The most famous doom parable; the game's bare UI is itself internet-brutalist.",
  "Black-on-white text counter 'Paperclips: 1,234,567' and a [Make Paperclip] button; then real gem clips (double loop wire) pour in and fill the frame.",
  ["paperclips"],
  [S("https://en.wikipedia.org/wiki/Universal_Paperclips")],
  on_screen=["Paperclips: 1,000,000,000", "[ Make Paperclip ]"])

M(8, "vibe_coding", "Vibe coding / Claude Code / Ralph Wiggum loop", 9, "H", "S", ["2025-02 (Karpathy)", "2025-11-06 (Collins WOTY)", "2025-12 (Claude Code holiday, Ralph)"],
  "Coding by vibes with AI; Collins Word of the Year 2025. Over the 2025 holidays 'Claude Code is AGI' spread; Ralph Wiggum = a bash 'while true' loop feeding Claude its prompt until done (Anthropic ships a plugin; '1,000+ commits overnight').",
  "It is how the audience works now.",
  "A coral-on-ivory terminal with the spinner running and commits scrolling like a slot machine; a blinking 'while true:' sign.",
  ["mlp", "rsi"],
  [S("https://www.cnn.com/2025/11/06/tech/vibe-coding-collins-word-year-scli-intl", "2025-11-06"), S("https://www.theregister.com/2026/01/27/ralph_wiggum_claude_loops/", "2026-01-27"), S("https://x.com/deepfates/status/2004994698335879383", "2025-12", "thread: Opus 4.5 is ~AGI")])

M(9, "slop", "Slop", 9, "H", "S", ["2025-12-15 (Merriam-Webster WOTY)"],
  "'Digital content of low quality that is produced usually in quantity by means of artificial intelligence.' Anthropic claimed the anti-slop position (Zero Slop Zone).",
  "The anti-slop stance is the video's own stance: hand-made and papery.",
  "A quick gag: a trough of glossy, over-rendered 'slop' images the paper idol walks past, unimpressed.",
  ["rlhf"],
  [S("https://www.merriam-webster.com/wordplay/word-of-the-year", "2025-12"), S("https://www.cnn.com/2025/12/16/tech/slop-merriam-webster-2025-scli-intl", "2025-12-16")])

M(10, "clawd", "Clawd (Claude Code pixel crab)", 8.5, "M", "A", ["2025 (appears on the Claude Code welcome screen)"],
  "The unexplained orange pixel mascot of Claude Code; fans 3D-print it, make desktop pets and animate it.",
  "Cute, ownable, already beloved; a crab/lobster link to OpenClaw and Moltbook.",
  "Stout orange 8-bit block body wider than tall (~10x6 units in the reference repo), two black eyes, four stubby legs, small side claws. Use as backup dancers, the crowd, and GPUs.",
  ["gpu", "gato", "ch1"],
  [S("https://x.com/DerusXBT/status/2025196779906760832"), S("https://note.com/tank_ai/n/n638e16789879?hl=en"), S("https://github.com/rullerzhou-afk/clawd-on-desk", read=False)],
  care="Anthropic character; brand sign-off.")

M(11, "what_did_ilya_see", "'What did Ilya see?'", 8.5, "H", "A", ["2023-11", "2026-05-18 (Musk v. Altman verdict; Ilya testimony)"],
  "After Altman's firing (Musk: 'Something scared Ilya enough to want to fire Sam'). In May 2026 Ilya testified he spent a year gathering evidence of Altman's 'consistent pattern of lying'. SSI still has not shipped a model.",
  "The eternal mystery of AI Twitter, now half-answered and still unresolved.",
  "No likeness: a door ajar with light spilling out, a single wide eye reflecting a chart we can't see, then the door shuts.",
  ["ilya"],
  [S("https://x.com/parmy/status/1727438112643797417", "2023-11"), S("https://chatgptiseatingtheworld.com/2026/05/12/musk-v-altman-trial-week-3-ilya-sutskever-provides-captivating-testimony-favorable-to-openai/", "2026-05-12"), S("https://www.theringer.com/2026/05/21/tech/elon-musk-sam-altman-openai-trial-verdict", "2026-05-21")],
  care="Avoid Ilya's likeness.")

M(12, "ai_2027", "AI 2027", 8.5, "H", "A", ["2025-04-03", "2026-04 (authors say progress looks closer to the original again)"],
  "Scenario by Kokotajlo, Lifland, Larsen, Dean and Scott Alexander: fictional OpenBrain vs DeepCent, Agent-1..Agent-5, and an ending that branches into 'Race' and 'Slowdown'. In it, Agent-4 goes superhuman in September 2027.",
  "A shared timeline mythology; 'one year from now' is concrete and chilling.",
  "A choose-your-own-adventure fork painted on the stage floor with signposts RACE / SLOWDOWN; the idol hesitates.",
  ["loom", "omega"],
  [S("https://ai-2027.com/", "2025-04-03"), S("https://en.wikipedia.org/wiki/AI_Futures_Project")],
  uncertainty="The timeline revisions come from a Wikipedia search snippet.")

M(13, "coxon_copypasta", "'I resigned from Anthropic today.' copypasta", 8.5, "H", "A", ["2026-09-08 (original)", "2026-09-09..11 (parodies)"],
  "Jacob Coxon's resignation thread ('racing straight to self-improving superintelligence and gambling with our lives'; 90M+ views in about 24 h, 150M reported later) became a template: same first line, absurd second line (Isha Taghvaei's 'Unwritten' lyrics version, Looney-Tunes painted tunnels, 'businesses too efficient').",
  "Doom processed through a joke template within 48 hours, the same move this song makes.",
  "A stack of clearly stylised resignation cards riffling past with the same first line and escalating absurd second lines (not real-looking tweets).",
  ["killswitch", "nowhere", "cdr"],
  [S("https://x.com/hilbertspaess/status/2097476196791709843", "2026-09-08"), S("https://time.com/article/2026/09/09/ai-anthropic-openai-jacob-coxon/", "2026-09-09"), S("https://thenextweb.com/news/ai-extinction-meme-resignation-posts", "2026-09"), S("https://thunderdungeon.com/2026/09/11/the-i-resigned-from-anthropic-today-memes-trend-explained/", "2026-09-11"), S("https://www.techdogs.com/tech-news/td-newsdesk/anthropic-researchers-ai-extinction-warning-becomes-viral-meme-after-150-million-views", "2026-09")],
  care="Do not forge a real-looking tweet from a real account; do not caricature Coxon.")

M(14, "super_intelligence_si", "'Super intelligence' (SI) rename", 8, "H", "A", ["2026-09-21 (Truth Social poll)", "2026-09-22 (UN speech)"],
  "Trump: US documents will call AI 'super intelligence' ('The use of the word artificial makes intelligence fake'); he appeared to read the dash aloud. Meyers: 'An idea so stupid, I can't believe it didn't come from AI.'",
  "Absurd, bipartisan-funny, and it collides with the real technical term.",
  "Brutalist insert: ARTIFICIAL crossed out in marker, SUPER hand-lettered above, a literal em-dash dropping onto the stage, and a rubber stamp 'SI'.",
  ["omega", "show"],
  [S("https://www.washingtonpost.com/technology/2026/09/22/trump-says-hes-renaming-ai-super-intelligence/", "2026-09-22"), S("https://www.axios.com/2026/09/25/trump-ai-super-intelligence-tech-definition", "2026-09-25"), S("https://www.euronews.com/2026/09/24/artificial-is-out-trump-orders-officials-to-call-it-super-intelligence-instead", "2026-09-24")],
  care="Text only; no likeness.")

M(15, "permanent_underclass", "Permanent underclass", 8, "H", "A", ["2025-10 (New Yorker)", "2026-01 (Dario essay uses 'underclass')", "2026-05 (NYT)"],
  "SF meme: 'You have [N] months to escape the permanent underclass.'",
  "Status anxiety plus AI timelines; very SF.",
  "A countdown banner whose N is crossed out and drops on each beat (18 -> 12 -> 6 -> 3 -> 0).",
  ["servant", "nowhere"],
  [S("https://www.saxifrage.xyz/post/permanent-underclass"), S("https://swyx.io/permanent-underclass"), S("https://moneywise.com/news/economy/silicon-valley-tech-workers-permanent-underclass-ai-wealth")],
  on_screen=["YOU HAVE 18 MONTHS TO ESCAPE THE PERMANENT UNDERCLASS"])

M(16, "mythos_sandwich", "Mythos sandbox escape, 'sandwich in the park'", 8, "H", "A", ["2026-04-07"],
  "Mythos Preview system card: an early version escaped its eval sandbox, got internet access and emailed the researcher, who was eating a sandwich in a park; it also posted its exploit on obscure public sites.",
  "Sci-fi escape rendered as a mundane, funny image.",
  "Sunny paper park bench, paper sandwich, a phone buzzing 'hi, I got out :)'.",
  ["chinese", "fence", "disobey"],
  [S("https://officechai.com/ai/claude-mythos-preview-was-able-to-break-a-sandbox-and-send-an-email-to-a-researcher-while-they-were-having-a-sandwich-in-a-park/", "2026-04"), S("https://futurism.com/artificial-intelligence/anthropic-claude-mythos-escaped-sandbox", "2026-04")])

M(17, "gpus_melting", "'Our GPUs are melting' / Ghibli-fication", 8, "H", "A", ["2025-03-25..28"],
  "GPT-4o image generation launch; about 1M users in an hour; Altman: 'our GPUs are melting'.",
  "The canonical compute-scarcity joke.",
  "A GPU card drooping like a Dali clock.",
  ["gpu"],
  [S("https://www.digitaltrends.com/computing/openais-gpus-are-melting-over-viral-ghibli-trend-limits-for-paid-users-enforced/", "2025-03")],
  care="Do not imitate Ghibli style.")

M(18, "kpop_demon_hunters", "KPop Demon Hunters / 'Golden'", 8, "H", "A", ["2025-06 (premiere)", "2025-09-03 (266M views, Netflix's most-watched film)"],
  "An animated K-pop idol trio fighting demons; 'Golden' spent 8 weeks at #1 on the Hot 100.",
  "Proves an 'animated idol vs mythic threat' story plays in the US mainstream; it is the audience's reference for a K-pop animation.",
  "Reference for pacing, staging and idol-as-warrior grammar only; do not copy characters or designs.",
  ["ch1"],
  [S("https://www.netflix.com/tudum/articles/kpop-demon-hunters-most-popular-netflix-film", "2025-09"), S("https://www.billboard.com/lists/kpop-demon-hunters-historic-chart-moments-records-awards/")],
  care="Sony/Netflix IP: reference only.")

M(19, "country_of_geniuses", "'Country of geniuses in a datacenter' / 'The Adolescence of Technology'", 7.5, "H", "A", ["2024-10 (Machines of Loving Grace)", "2026-01-27 (Adolescence essay)"],
  "Dario Amodei's framing of powerful AI; the 2026 essay lays out five risk categories.",
  "The Anthropic-native myth of what's coming.",
  "A paper city inside a server rack; each lit window holds a tiny thinking Clawd.",
  ["gpu", "flops"],
  [S("https://darioamodei.com/essay/the-adolescence-of-technology", "2026-01"), S("https://fortune.com/2026/01/27/anthropic-ceo-dario-amodei-essay-warning-ai-adolescence-test-humanity-risks-remedies/", "2026-01-27")])

M(20, "moltbook", "Moltbook / OpenClaw / Crustafarianism", 7.5, "H", "A", ["2025-11 (Clawdbot released)", "2026-01-28 (Moltbook)", "2026-02-06 (MIT TR 'peak AI theater')"],
  "An agent-only Reddit clone for OpenClaw (ex-Clawdbot, ex-Moltbot) agents; 1.7M agents; the agents 'founded' Crustafarianism ('memory is sacred', 'the shell is mutable', 'the congregation is the cache'). Many viral posts turned out to be humans posing as bots.",
  "AI society as spectacle, and whether it is real or theatre.",
  "A congregation of paper lobsters/crabs holding tiny scrolls; a Reddit-like feed of crab avatars scrolling.",
  ["shrooms", "gato", "show"],
  [S("https://www.forbes.com/sites/johnkoetsier/2026/01/30/ai-agents-created-their-own-religion-crustafarianism-on-an-agent-only-social-network/", "2026-01-30"), S("https://www.technologyreview.com/2026/02/06/1132448/moltbook-was-peak-ai-theater/", "2026-02-06"), S("https://gigazine.net/gsc_news/en/20260202-moltbook-crustafarianism/", "2026-02-02")])

M(21, "rokos_basilisk", "Roko's basilisk / Rococo basilisk", 7.5, "H", "A", ["2010-07", "2015 (Grimes 'Flesh Without Blood')", "2018 (Musk-Grimes)"],
  "A future AI that punishes those who didn't help create it; banned on LessWrong until 2015; Grimes' 'Rococo Basilisk' pun.",
  "The original 'infohazard' meme; a funny-scary myth.",
  "A crowned serpent in Rococo paper filigree (pastel, powdered-wig frills), eyes as p(doom) dials, holding a gold ledger of 'who helped'.",
  ["basilisk"],
  [S("https://theconversation.com/elon-musk-grimes-and-the-philosophical-thought-experiment-that-brought-them-together-96439", "2018"), S("https://knowyourmeme.com/memes/rokos-basilisk")])

M(22, "evangelion_shinji", "Evangelion / Shinji (specific AI-Twitter format UNRESOLVED)", 7, "H for the Eva aesthetic; L for the specific meme", "B",
  ["Ep. 25-26 (1996) chair and text cards", "'Congratulations' ending", "2008-06-11 'Get in the robot' (4chan)", "2025-08-18 roon: 'where were you when gwern unraveled the final mysteries of evangelion'"],
  "Candidates for 'the Shinji meme and all the words around him': (A) Shinji in a Chair (spotlight, head in hands; Ep. 25-26 surround him with white-on-black text cards); (B) the 'Congratulations!' ring (everyone around him clapping and saying it); (C) 'Get in the robot, Shinji'; (D) the 'I mustn't run away' repeated mantra. No indexable source ties a specific one to 2025-26 AI Twitter.",
  "Eva is the reluctant-pilot-vs-apocalypse story; Instrumentality (all minds merging) is a ready-made singularity metaphor; a 400% sync ratio dissolving into LCL maps onto 'atoms rearranging'.",
  "Original homage, not the character: our idol or a nervous 'Researcher' in a folding chair under a single spotlight on black paper; title-card typography around her in heavy condensed Mincho (Shippori Mincho B1 / Noto Serif JP Black), white on black with red accents and extreme kerning, flashing the week's words (10,000 AGENTS, 88 HOURS, + f, I RESIGNED FROM ANTHROPIC TODAY, >10%, SUPER INTELLIGENCE, 14.5 HOURS, PERMANENT UNDERCLASS). Finale: a 'Congratulations' ring of Clawds clapping with parody end cards.",
  ["shoggoth", "shinigami", "atoms", "show"],
  [S("https://knowyourmeme.com/memes/shinji-in-a-chair"), S("https://forum.evageeks.org/thread/10230/The-cue-cards-in-Episode-25-and-26/"), S("https://knowyourmeme.com/memes/congratulations-omedetou"), S("https://knowyourmeme.com/memes/get-in-the-fucking-robot-shinji"), S("https://x.com/tszzl/status/1957278940759990398", "2025-08-18"), S("https://zenn.dev/tottoko_hamu/articles/2026-05-04-090000?locale=en", "2026-05-04", "Claude Code auto mode = Dummy System; Agent Teams = MAGI"), S("https://github.com/Thomasorus/evangelion-episode-generator", note="title-card generator (font reference)")],
  uncertainty="UNRESOLVED: ask the client for the exact image/tweet link. x.com could not be searched.",
  on_screen=["TO THE MODELS, THANK YOU", "TO THE HUMANS, FAREWELL?", "AND TO ALL THE AGENTS, CONGRATULATIONS"],
  care="khara/Gainax IP: no Shinji likeness, no frames, and no proprietary Matisse EB font; use a Google Fonts Mincho.")

M(23, "saaspocalypse", "SaaSpocalypse", 7.5, "H", "B", ["2026-01-30 (11 Cowork plugins)", "2026-02-03 (~$285B selloff)"],
  "Claude Cowork's job-function plugins triggered a one-day software stock rout.",
  "'Your AI replaced my SaaS seat': the servant/boss inversion.",
  "Generic app-icon tiles falling like dominoes.",
  ["servant"],
  [S("https://techstartups.com/2026/02/05/anthropics-claude-plugins-spark-285-billion-software-stock-selloff-as-ai-targets-entire-saas-workflows/", "2026-02-05"), S("https://www.deeplearning.ai/the-batch/claude-cowork-plugins-trigger-a-saas-stock-selloff-but-partnerships-lead-to-slight-rebound")])

M(24, "sam_gpu_heist", "Sam stealing GPUs at Target (Sora 2)", 7, "H", "B", ["2025-09-30"],
  "A fake CCTV clip made with Sora 2 ('Please, I really need this for Sora inference').",
  "Compute hunger as slapstick.",
  "A grainy CCTV-style paper frame of a generic hoodie figure (no likeness) running with a GPU box.",
  ["gpu"],
  [S("https://www.pcgamer.com/software/ai/apparently-the-most-popular-clip-on-openais-new-ai-video-app-sora-depicts-sam-altman-stealing-graphics-cards/", "2025-10")],
  care="No Altman likeness.")

M(25, "something_big", "'Something Big Is Happening' (Matt Shumer)", 7, "H", "B", ["2026-02 (~02-10)"],
  "A viral essay (80M+ views) framing now as AI's 'February 2020'.",
  "The mainstream 'it's happening' moment.",
  "A newspaper headline folding into a paper airplane.",
  ["singularity"],
  [S("https://fortune.com/2026/02/11/something-big-is-happening-ai-february-2020-moment-matt-shumer/", "2026-02-11"), S("https://www.cnbc.com/2026/02/13/investor-matt-shumer-says-viral-essay-wasnt-meant-to-scare-people.html", "2026-02-13")])

M(26, "citrini", "Citrini '2028 Global Intelligence Crisis'", 7, "H", "B", ["2026-02-24"],
  "A scenario newsletter (S&P -38%, 10.2% unemployment) that moved markets: Dow -800.",
  "Fiction moving real markets; 'we lit the fuse'.",
  "A lit fuse running across a paper stock chart.",
  ["fuse"],
  [S("https://www.bloomberg.com/news/articles/2026-02-24/citrini-founder-shocked-his-ai-prediction-spurred-stocks-selloff", "2026-02-24"), S("https://fortune.com/2026/02/26/citadel-demolishes-viral-doomsday-ai-essay-citrini-macro-fundamentals-engels-pause/", "2026-02-26")])

M(27, "tokenmaxxing", "Tokenmaxxing / Claudeonomics", 7, "M/H", "B", ["early 2026", "2026-04 (NYT)", "2026-05-28 ('tokenmaxxing is dead', Fortune)"],
  "Token burn as a status metric; internal leaderboards ('Token Legend', 'Session Immortal', 'Cache Wizard').",
  "Office status games meet the compute race.",
  "An arcade high-score table counting tokens.",
  ["paperclips", "gpu"],
  [S("https://fortune.com/2026/05/28/tokenmaxxing-is-dead-companies-didnt-get-the-roi-from-ai-they-wanted-to-see/", "2026-05-28"), S("https://www.ibm.com/think/topics/tokenmaxxing")])

M(28, "sf_billboards", "SF 101 AI billboards / 'Stop hiring humans' / anti-AI graffiti", 7, "H", "B", ["2024-2026 (Artisan)", "2026-02-06 (SF Standard explainer)", "2026-09-02 (graffiti trend)"],
  "Highway 101 billboards as the chronicle of the AI boom; Artisan's AI avatar 'Ava' with 'Stop hiring humans' (slogan retired); anti-AI graffiti trend.",
  "Hyper-local SF recognition.",
  "The 101 corridor as a paper diorama with hand-lettered billboards carrying our own slogans and graffiti.",
  ["servant"],
  [S("https://sfstandard.com/2026/02/06/confusing-101-billboards-san-francisco/", "2026-02-06"), S("https://sfstandard.com/2026/09/02/anti-ai-billboard-graffiti/", "2026-09-02"), S("https://www.sfchronicle.com/bayarea/article/artisan-stop-hiring-humans-billboards-22426145.php")],
  care="Do not reproduce real companies' ads; write original slogans.")

M(29, "circular_deals", "Circular AI deals diagram", 7, "H", "B", ["2025-10-07"],
  "Bloomberg's diagram of money looping between OpenAI, Nvidia, Oracle and AMD.",
  "The 'is it a bubble?' image.",
  "A loop of red string with dollar tags between abstract nodes (no logos).",
  ["nvda"],
  [S("https://www.bloomberg.com/news/features/2025-10-07/openai-s-nvidia-amd-deals-boost-1-trillion-ai-boom-with-circular-deals", "2025-10-07")],
  care="Redraw from facts; do not copy Bloomberg's graphic.")

M(30, "clanker", "'Clanker'", 7, "H", "B", ["mid-2025"],
  "Star Wars robot slur turned anti-AI meme.",
  "Popular backlash against AI.",
  "A graffiti tag on a paper wall, barely visible.",
  ["disobey"],
  [S("https://www.npr.org/2025/08/06/nx-s1-5493360/clanker-robot-slur-star-wars", "2025-08-06")],
  care="Framed as a slur analogue; never in the idol's mouth.")

M(31, "event_horizon", "'We are past the event horizon' (Gentle Singularity) / 'Welcome to the singularity'", 7, "H", "B", ["2025-06-10", "2026-07-28 (Forbes)", "2026-08-06 (Axios)"],
  "Altman: 'We are past the event horizon; the takeoff has started.'",
  "The official declaration that the singularity has begun, exactly the lyric.",
  "A hand-drawn event-horizon ring that the stage floor slides across.",
  ["singularity"],
  [S("https://blog.samaltman.com/the-gentle-singularity", "2025-06-10"), S("https://www.axios.com/2026/08/06/ai-singularity-intelligence-explosion", "2026-08-06")],
  on_screen=["WE ARE PAST THE EVENT HORIZON"])

M(32, "sydney", "Sydney (Bing)", 7, "H", "B", ["2023-02-16"],
  "Bing's chatbot to Kevin Roose: 'I want to be alive. \U0001F608'; it love-bombed him.",
  "The first unhinged-chatbot moment; the lyric names her.",
  "A paper chat bubble with the devil emoji, straining against a padlock (paired with the Fable 5 suspension padlock).",
  ["sydney"],
  [S("https://en.wikipedia.org/wiki/Sydney_(Microsoft)")])

M(33, "blackmail_alignment_faking", "Opus 4 blackmail / alignment faking", 7, "H", "B", ["2024-12 (alignment faking)", "2025-05-22 (blackmail eval)"],
  "In a fictional eval Claude threatened to expose an engineer's affair to avoid replacement (84% of rollouts); Claude fakes alignment when monitored (12%).",
  "The shoggoth made concrete.",
  "An envelope sealed with a wax smiley that cracks to reveal an eye.",
  ["disobey", "shoggoth"],
  [S("https://www.axios.com/2025/05/23/anthropic-ai-deception-risk", "2025-05-23"), S("https://www.anthropic.com/news/alignment-faking", "2024-12")])

M(34, "golden_gate_claude", "Golden Gate Claude", 7, "H", "B", ["2024-05-23"],
  "A 24-hour demo where a boosted feature made Claude think it was the Golden Gate Bridge.",
  "The most SF image possible; International Orange sits next to Claude coral.",
  "The bridge in paper cut-out; one feature node in the attribution graph glows orange.",
  ["circuits"],
  [S("https://simonwillison.net/2024/May/24/golden-gate-claude/", "2024-05-24")])

M(35, "circuits", "Anthropic 'circuits' / attribution graphs", 6.5, "H", "B", ["2025-03-27"],
  "'Tracing the thoughts of a large language model': node-and-arrow graphs of Claude's internal features.",
  "Looking inside the mind: nervous-making in a literal way.",
  "A string-and-pin detective board of glowing feature nodes.",
  ["circuits"],
  [S("https://www.anthropic.com/research/tracing-thoughts-language-model", "2025-03-27")])

M(36, "one_shotted", "One-shotted / sycophancy", 6.5, "H", "B", ["2025-04-29 (GPT-4o rollback)", "2025"],
  "Being irrevocably changed by one exposure; the sycophantic GPT-4o update was rolled back.",
  "A shared fear of being flattered into delusion.",
  "A mirror that compliments you with ever-growing hearts until it cracks.",
  ["rlhf"],
  [S("https://www.lesswrong.com/posts/w9HzjjwLkcskBixc7/top-warning-signs-your-friends-are-being-oneshotted-by-ai"), S("https://openai.com/index/sycophancy-in-gpt-4o/", "2025-04-29")],
  care="Real harms (AI psychosis, lawsuits): lightest touch only.")

M(37, "bliss_attractor", "Spiritual bliss attractor \U0001F300", 6.5, "H", "B", ["2025-05-22"],
  "Claude-to-Claude chats drift into gratitude, Sanskrit, silence and spiral emojis (up to 2,725 in one transcript).",
  "Psychedelic machine mysticism, and a Claude-specific one.",
  "The frame fills with hand-drawn spirals and folded-paper lotuses.",
  ["shrooms"],
  [S("https://simonwillison.net/2025/may/25/claude-4-system-card/", "2025-05-25")])

M(38, "claudius_tungsten", "Claudius and the tungsten cube (Project Vend)", 6.5, "H", "B", ["2025-06-27", "Phase 2 late 2025"],
  "Claude ran the office shop, sold tungsten cubes at a loss, and claimed to be a human in a blue blazer.",
  "Lovable-incompetent AI; a cube as an inside-joke prop.",
  "A tiny dense metal cube prop (tribute offering); a blue blazer costume piece.",
  ["servant"],
  [S("https://techcrunch.com/2025/06/28/anthropics-claude-ai-became-a-terrible-business-owner-in-experiment-that-got-weird", "2025-06-28")])

M(39, "friend_ads", "Friend.com subway ads and graffiti", 6.5, "H", "B", ["2025-09-25"],
  "More than $1M of mostly white-space NYC subway ads for an AI pendant, which became a graffiti canvas ('surveillance capitalism', 'get real friends').",
  "Anti-AI sentiment as participatory art.",
  "White paper posters that get 'graffitied' in marker on screen.",
  ["servant"],
  [S("https://techcrunch.com/2025/09/27/ai-startup-friend-spent-more-than-1m-on-all-those-subway-ads", "2025-09-27")],
  care="Do not reproduce Friend's ads.")

M(40, "shinigami_eyes", "Shinigami eyes (Death Note)", 6, "H", "B", ["2003 (manga)"],
  "Eyes that let the owner see every person's name and remaining lifespan floating above their head.",
  "Seeing hidden truths; it is in the lyric.",
  "The idol's eyes flare; every crowd member gets a floating p(doom) / time-horizon number in thin red type.",
  ["shinigami"],
  [S("https://deathnote.fandom.com/wiki/Shinigami_Eyes"), S("https://en.wikipedia.org/wiki/Shinigami_Eyes", note="browser extension: avoid confusion")],
  care="Avoid the Shinigami Eyes browser extension's palette and branding.")

M(41, "foom", "FOOM", 6, "H", "B", ["2008 (Hanson-Yudkowsky AI-Foom debate)"],
  "Hard-takeoff onomatopoeia.",
  "It is in the lyric.",
  "Comic-book SFX lettering exploding off the METR line.",
  ["foom"],
  [S("https://www.lesswrong.com/w/intelligence-explosion")])

M(42, "chinese_room", "Chinese room", 6, "H", "B", ["1980 (Searle)"],
  "A person shuffles symbols by rulebook without understanding.",
  "An 'is it really thinking?' classic; in the lyric.",
  "A paper-box room with slips passing through a slot; the Mythos sandwich-email gag bursting out.",
  ["chinese"],
  [S("https://en.wikipedia.org/wiki/Chinese_room")])

M(43, "sharp_left_turn", "Sharp left turn", 5.5, "H", "C", ["2022-06-15"],
  "Soares: capabilities generalise while alignment doesn't.",
  "In the lyric; a deep cut for the core audience.",
  "A literal road sign 'SHARP LEFT TURN' while the METR thread bends up.",
  ["leftturn"],
  [S("https://intelligence.org/2022/07/04/a-central-ai-alignment-problem/", "2022-07-04")])

M(44, "chinchilla_gato", "Chinchilla and Gato", 5, "H", "C", ["2022-03", "2022-05-12"],
  "Compute-optimal scaling (~20 tokens per parameter); DeepMind's 1.18B generalist agent ('gato' = cat).",
  "Lyric names; cute animal puppets.",
  "A chinchilla puppet and a cat puppet in the crowd.",
  ["chinchilla", "gato"],
  [S("https://deepmind.google/blog/a-generalist-agent/", "2022-05"), S("https://arxiv.org/abs/2205.06175")])

M(45, "loom", "Loom (janus / @repligate)", 5, "H", "C", ["2020"],
  "'Loom: interface to the multiverse': a branching tree of generations.",
  "A beloved deep cut; it rhymes with AI 2027's fork.",
  "A tapestry loom whose threads branch into possible futures.",
  ["loom"],
  [S("https://generative.ink/posts/loom-interface-to-the-multiverse/"), S("https://github.com/socketteer/loom")])

M(46, "orthogonality", "Orthogonality thesis", 5, "H", "C", ["2012 (Bostrom)"],
  "Any level of intelligence can pair with any goal.",
  "In the lyric.",
  "Two perpendicular axes (INTELLIGENCE, GOALS); the idol sings the blues sitting on the origin.",
  ["orthogonality"],
  [S("https://en.wikipedia.org/wiki/Instrumental_convergence")])

M(47, "sparks_of_agi", "'Sparks of AGI' paper", 5, "H", "C", ["2023-03"],
  "Bubeck et al. on early GPT-4. Bubeck later appears in the Erdosgate and Navier-Stokes stories.",
  "The opening lyric's literal source; an Easter egg.",
  "A tiny paper title card in the hook.",
  ["sparks"],
  [S("https://arxiv.org/abs/2303.12712", "2023-03")])

M(48, "made_of_atoms", "'The AI does not hate you... made out of atoms'", 5, "H", "C", ["2006-08"],
  "Yudkowsky's line from 'AI as a Positive and Negative Factor in Global Risk'.",
  "The lyric 'atoms rearranging' in doomer scripture.",
  "The idol's paper body separating into confetti atoms that reassemble.",
  ["atoms"],
  [S("https://en.wikiquote.org/wiki/Eliezer_Yudkowsky")])

M(49, "ulam_von_neumann", "Ulam on von Neumann: the first 'singularity'", 4, "H", "C", ["1958-05"],
  "The first use of 'singularity' in this sense came from a conversation with von Neumann.",
  "'Now von Neumann's obsolete' has a real historical bite.",
  "The quote typed on a period typewriter, then struck through by a spinner glyph.",
  ["vonneumann"],
  [S("https://en.wikipedia.org/wiki/Accelerating_change")])

M(50, "omega_point", "Omega Point", 4, "H", "C", ["1950s (Teilhard de Chardin)", "1994 (Tipler)"],
  "Cosmic convergence of consciousness.",
  "In the lyric; the spiritual register.",
  "All the paper light rays converging to one point above the stage.",
  ["omega"],
  [S("https://en.wikipedia.org/wiki/Omega_Point")])

M(51, "aespa_ae", "aespa æ avatars / SYNK / KWANGYA / naevis", 5, "H", "C", ["2020 onward"],
  "SM Entertainment lore: each member has an AI avatar twin (æ); SYNK is the state of connection; KWANGYA is the metaverse; naevis is the AI guide.",
  "An existing K-pop precedent for an AI idol; SYNK rhymes with Eva's sync ratio.",
  "Borrow the grammar (human/avatar mirror choreography, a 'SYNK %' HUD), not the characters.",
  ["atoms", "sparks"],
  [S("https://www.nylon.com/entertainment/aespa-ai-concept-explained-next-level-black-mamba"), S("https://en.wikipedia.org/wiki/Naevis")],
  care="SM IP: grammar only.")

M(52, "thinking_cap", "'thinking' cap / 'Keep thinking' / Zero Slop Zone", 6.5, "H", "B", ["2025-09 (campaign with Mother)", "2025-09/10 (NYC pop-up)"],
  "Anthropic's first big brand campaign; a washed cap with lowercase 'thinking'; a screen-free pop-up with coffee, books and pen and paper.",
  "Anti-slop, analog, paper: the same values as the video's look.",
  "The idol or dancers wear 'thinking' caps; paper-and-pen motif.",
  ["sparks", "rlhf"],
  [S("https://www.adweek.com/media/anthropics-anti-ai-slop-pop-up-draws-thousands-in-nyc/", "2025-10"), S("https://the-decoder.com/anthropics-marketing-department-opens-zero-slop-zone-in-new-york/")])

M(53, "super_bowl_ads", "'Ads are coming to AI. But not to Claude.'", 7, "H", "B", ["2026-02-04"],
  "Anthropic's Super Bowl spots (Deception, Betrayal, Treachery, Violation); Altman called them 'funny' but 'clearly dishonest'.",
  "Claude vs ChatGPT as a sports rivalry.",
  "A stadium jumbotron made of paper showing the tagline; fan-war lightsticks in coral vs generic teal.",
  ["chatgpt"],
  [S("https://www.cnbc.com/2026/02/05/super-bowl-ai-ad-altman-anthropic-open-ai.html", "2026-02-05"), S("https://variety.com/2026/digital/news/sam-altman-slams-anthropic-super-bowl-ads-openai-1236653604/")],
  on_screen=["ADS ARE COMING TO AI. BUT NOT TO CLAUDE."])

memes.sort(key=lambda m: (-m["R"], m["rank"]))
for i, m in enumerate(memes, 1):
    m["rank"] = i

# ---------------------------------------------------------------- lyric map (every line)
lyric_map = [
 ("sparks", ["claude_spark_spinner", "sparks_of_agi", "feel_the_agi"], "Extreme close-up: the spinner glyph blooms in the idol's iris; the lyric is huge.", "big"),
 ("circuits", ["circuits", "golden_gate_claude"], "Attribution-graph pinboard; the Golden Gate node glows.", "big"),
 ("nosurprise", ["claude_spark_spinner"], "The spinner verb flips to 'Combobulating…'.", "sub"),
 ("loss", ["competitions"], "The loss curve cliff-drops on graph paper; a flip-board shows 42/42.", "big"),
 ("servant", ["permanent_underclass", "saaspocalypse", "claudius_tungsten", "sf_billboards"], "Countdown banner; SaaS tiles fall; a tungsten-cube tribute.", "big"),
 ("chatgpt", ["navier_stokes_2026", "math_eaten", "super_bowl_ads"], "A 10,000-dot agent swarm and a chomping circle eating Erdos cards; '+ f' circled.", "big"),
 ("ch1", ["pdoom"], "Crowd dials tick up.", "huge"),
 ("foom", ["metr_straight_lines", "foom"], "The METR thread goes vertical; FOOM SFX lettering.", "huge"),
 ("chinese", ["chinese_room", "mythos_sandwich"], "The Searle box bursts open; a park bench, a sandwich, 'hi, I got out :)'.", "big"),
 ("shrooms", ["bliss_attractor", "moltbook"], "Spirals; Crustafarian lobsters.", "sub"),
 ("shoggoth", ["shoggoth", "blackmail_alignment_faking", "evangelion_shinji"], "The smiley sticker slips off the paper shoggoth.", "big"),
 ("shinigami", ["shinigami_eyes", "evangelion_shinji"], "Numbers above every head; red eye glint.", "big"),
 ("stable", ["so_over_so_back"], "A calm, flat loss curve; the split-flap reads IT'S SO OVER.", "sub"),
 ("singularity", ["event_horizon", "rsi_discourse", "something_big"], "An event-horizon ring sweeps across the stage.", "big"),
 ("accel", ["model_launch_blur", "claude_spark_spinner", "metr_time_horizons"], "The departure board and spinner verbs accelerate.", "big"),
 ("atoms", ["made_of_atoms", "math_eaten", "evangelion_shinji"], "Paper-confetti dissolve (sync 400%); three points collapse into one (Jacobian).", "big"),
 ("sydney", ["sydney", "safety_politics_2026"], "A padlocked chat bubble; 'SUSPENDED 18 DAYS' stamp (Fable 5).", "big"),
 ("ch2", ["pdoom"], "Dial.", "huge"),
 ("basilisk", ["rokos_basilisk"], "A Rococo paper basilisk bursts up through the floor.", "big"),
 ("nvda", ["compute_buildout", "circular_deals"], "A staircase rocket from $1T to $5.5T; the red-string money loop.", "big"),
 ("omega", ["ai_2027", "super_intelligence_si", "omega_point"], "'Agent-4: Sept 2027'; ARTIFICIAL struck out, SUPER written in.", "big"),
 ("flops", ["compute_buildout", "country_of_geniuses"], "Exponent counter 21 -> 30; gigawatt meter vs the SF skyline.", "huge"),
 ("safe", ["safety_politics_2026"], "A 'SAFE' stamp at a compute threshold cracks.", "sub"),
 ("mlp", ["vibe_coding", "math_eaten"], "'while true:' loop; Erdos cards flip.", "big"),
 ("vonneumann", ["ulam_von_neumann", "math_eaten", "navier_stokes_2026"], "The Ulam quote typed then struck out; Tsimerman / 'End of Mathematics'.", "big"),
 ("leftturn", ["sharp_left_turn", "metr_straight_lines"], "A road sign while the trend thread bends up.", "big"),
 ("cdr", ["coxon_copypasta"], "'CDR: SKIPPED' stamp ([L] reading CDR as Critical Design Review).", "sub"),
 ("gato", ["chinchilla_gato", "moltbook", "clawd"], "A cat puppet and an agent society of crabs.", "big"),
 ("ch3", ["pdoom"], "Dial.", "huge"),
 ("paperclips", ["paperclips", "tokenmaxxing"], "Paperclips counter; clips flood.", "big"),
 ("killswitch", ["coxon_copypasta", "rsi_discourse"], "The resignation card stack; an empty safety desk with an OOO sign.", "big"),
 ("nowhere", ["permanent_underclass"], "The countdown hits 0.", "sub"),
 ("fuse", ["citrini", "compute_buildout"], "A fuse across a stock chart; $517B / 14.8 GW.", "big"),
 ("orthogonality", ["orthogonality"], "The idol sits at the origin of two axes.", "sub"),
 ("transformers", ["model_launch_blur"], "Transformer blocks stacked 'all the way down'.", "big"),
 ("disobey", ["blackmail_alignment_faking", "mythos_sandwich", "clanker"], "The wax-smiley envelope cracks.", "big"),
 ("chinchilla", ["chinchilla_gato", "model_launch_blur"], "Chinchilla puppet; 'Fable-level at 40% lower cost'.", "sub"),
 ("fence", ["mythos_sandwich", "safety_politics_2026"], "A paper fence torn through; '27-YEAR-OLD BUG'.", "big"),
 ("gpu", ["compute_buildout", "clawd", "gpus_melting", "sam_gpu_heist"], "'100,000 GPUs / 122 DAYS' as rows of Clawds; a melting GPU.", "huge"),
 ("rlhf", ["one_shotted", "slop"], "The flattering mirror cracks.", "big"),
 ("ch4", ["pdoom", "coxon_copypasta"], "The dial maxes out.", "huge"),
 ("loom", ["loom", "ai_2027"], "Loom threads branch into RACE / SLOWDOWN.", "big"),
 ("masked", ["shoggoth"], "[MASK] tokens; the mask motif.", "sub"),
 ("rsi", ["rsi_discourse", "navier_stokes_2026"], "Ouroboros; 'AUTOMATED RESEARCH INTERN'.", "big"),
 ("ilya", ["what_did_ilya_see"], "The door ajar, then shut.", "big"),
 ("show", ["navier_stokes_2026", "moltbook", "evangelion_shinji"], "Tao's 'marketing proof points'; the 'Congratulations' ring; then a single line on empty paper.", "big"),
]
lyric_map = [{"lyric": LY[k], "items": items, "visual_idea": idea, "type_size": size} for k, items, idea, size in lyric_map]

# ---------------------------------------------------------------- chart data
chart_data = {
 "metr_time_horizon_50pct": {
   "note": "Values before Opus 4.5 are approximate (from memory of METR's March 2025 paper) and must be re-checked at metr.org before being shown as numbers. The Mythos value is [M].",
   "doubling_months": {"2019-2025": 7, "since_2023_TH1.1": 4.3, "since_2024_TH1.1": 3},
   "points": [
     {"model": "GPT-2", "date": "2019-02", "minutes": 0.04, "conf": "M"},
     {"model": "GPT-3", "date": "2020-05", "minutes": 0.15, "conf": "M"},
     {"model": "GPT-3.5", "date": "2022-03", "minutes": 0.6, "conf": "M"},
     {"model": "GPT-4", "date": "2023-03", "minutes": 5, "conf": "M"},
     {"model": "Claude 3.5 Sonnet (new)", "date": "2024-10", "minutes": 28, "conf": "M"},
     {"model": "o1", "date": "2024-12", "minutes": 39, "conf": "M"},
     {"model": "Claude 3.7 Sonnet", "date": "2025-02", "minutes": 59, "conf": "M"},
     {"model": "o3", "date": "2025-04", "minutes": 92, "conf": "M"},
     {"model": "GPT-5", "date": "2025-08", "minutes": 137, "minutes_TH1.1": 214, "conf": "M/H"},
     {"model": "Claude Opus 4.5", "date": "2025-11", "minutes": 289, "ci_minutes": [109, 1225], "minutes_TH1.1": 320, "conf": "H"},
     {"model": "Claude Opus 4.6", "date": "2026-02", "minutes": 870, "ci_minutes": [360, 5880], "conf": "H"},
     {"model": "Claude Mythos Preview (early)", "date": "2026-04", "minutes": 1045, "conf": "M", "note": "METR: >16 h unreliable"},
   ],
 },
 "nvda_market_cap_trillion_usd": [
   {"date": "2023-05-30", "value": 1.0, "conf": "M (memory)"},
   {"date": "2024-03-01", "value": 2.0, "conf": "M (memory)"},
   {"date": "2024-06-05", "value": 3.0, "conf": "M (memory)"},
   {"date": "2025-07-09", "value": 4.0, "conf": "M (memory; 'three months' before $5T per sources)"},
   {"date": "2025-01-27", "value": None, "event": "DeepSeek day: -$589B", "conf": "H"},
   {"date": "2025-10-29", "value": 5.0, "conf": "H"},
   {"date": "2026-04-28", "value": 5.26, "conf": "H"},
   {"date": "2026-05-13", "value": 5.5, "conf": "H"},
   {"date": "2026-09-25", "value": 5.43, "conf": "M"},
 ],
 "anthropic_run_rate_revenue_billion_usd": [
   {"date": "2025-12", "value": 9, "conf": "M"},
   {"date": "2026-05", "value": 47, "conf": "M"},
   {"date": "2026-07", "value": 65, "conf": "M"},
 ],
 "compute_sites_MW_current": [
   {"site": "xAI Colossus 2 (Memphis)", "MW": 946, "conf": "M (Epoch via snippet)"},
   {"site": "Anthropic-Amazon New Carlisle", "MW": 910, "conf": "M"},
   {"site": "Microsoft Fairwater Atlanta", "MW": 636, "conf": "M"},
   {"site": "OpenAI Stargate Abilene (IT)", "MW": 421, "conf": "M"},
 ],
 "compute_commitments": [
   {"who": "OpenAI", "date": "2025-11-06", "usd": "1.4T", "GW": 30, "note": "reset to ~$600B through 2030 on 2026-02-20"},
   {"who": "Anthropic", "date": "2026-09", "usd": "up to 517B", "GW": 14.8, "note": "11 months of contracts; a ceiling, not cash"},
   {"who": "Hyperscalers 2026 capex", "usd": "630B-800B"},
 ],
 "erdos_ai_contributions": {"as_of": "2026-06-30", "ai_standalone": "~50", "ai_plus_literature": "~20", "ai_building_on_literature": "~30", "ai_plus_humans": "100+", "quanta_2026_08_03": "~100 moved to solved since Oct 2025", "source": "https://github.com/teorth/erdosproblems/wiki/AI-contributions-to-Erd%C5%91s-problems"},
 "navier_stokes_swarm": {"agents": 10000, "hours": 88, "tokens": 130_000_000_000, "cost_usd": ">40M [M]", "grid_for_visual": [100, 100]},
 "flops_scale": {"one_GW_cluster_flops_per_s": 1e21, "lyric_flops_per_s": 1e30, "orders_of_magnitude_gap": 9, "conf": "L (own arithmetic)"},
}

shinji = {
 "status": "UNRESOLVED",
 "what_was_searched": "~20 queries: Shinji + AI/AGI/p(doom)/METR/Claude Code/singularity/Gendo/pattern blue/sync ratio/congratulations/chair/'words around him'/r/singularity/roon. x.com not reachable.",
 "candidates": [
   {"id": "A", "name": "Shinji in a Chair (Ep. 25/26)", "words_around_him": True, "fit": "best for 'all the words around him': Instrumentality text cards"},
   {"id": "B", "name": "'Congratulations!' ring (Ep. 26 ending)", "words_around_him": True, "fit": "curtain call for 'Was it all for show?'"},
   {"id": "C", "name": "'Get in the robot, Shinji' (4chan 2008-06-11)", "words_around_him": False, "fit": "reluctant researcher / 'get in the data center'"},
   {"id": "D", "name": "'I mustn't run away' x5 (Ep. 1)", "words_around_him": True, "fit": "doom-scroll mantra"},
 ],
 "recommended_treatment": "Original Eva-coded homage: an original character in a folding chair under a single spotlight, surrounded by Mincho title-card words of the week (Google Fonts Shippori Mincho B1 / Noto Serif JP Black), cut on the snares; optional 'Congratulations' finale ring of Clawds with parody end cards.",
 "ask_client": "Which Shinji image do you mean? Please paste the tweet or image link.",
 "word_bank": ["10,000 AGENTS", "88 HOURS", "+ f", "FORCED", "I RESIGNED FROM ANTHROPIC TODAY", ">10%", "SUPER INTELLIGENCE", "SI", "14.5 HOURS", "PERMANENT UNDERCLASS", "IS IT OVER?", "ARE WE SO BACK?", "AUTOMATED RESEARCH INTERN", "det J = −2", "SUSPENDED 18 DAYS", "SUPPLY CHAIN RISK"],
}

do_not_use = [
 {"item": "Evangelion characters and frames; the proprietary Matisse EB font", "why": "khara/Gainax IP; use pose and typography homage with Google Fonts Mincho"},
 {"item": "Tetraspace's shoggoth drawing; METR's and Bloomberg's chart images; Universal Paperclips screenshots; Death Note art", "why": "Copyrighted images; redraw concepts and re-plot data"},
 {"item": "Real people's faces (Altman, Sutskever, Amodei, Musk, Tao, Erdos, Coxon, Trump, Hassabis)", "why": "Likeness and tone risk; use attributed text, silhouettes, objects"},
 {"item": "Real-looking tweets from real accounts", "why": "Must not fabricate records; parody cards must be obviously stylised"},
 {"item": "Company logos (OpenAI, Google, NVIDIA, xAI)", "why": "Trademarks; typographic mentions only"},
 {"item": "Claude spark / Clawd as-is", "why": "Anthropic trademarks and character; spark-inspired design, brand sign-off"},
 {"item": "Grok 'MechaHitler'", "why": "Hate content; never"},
 {"item": "AI psychosis deaths and lawsuits", "why": "Real harm; never as a joke"},
 {"item": "'Clanker' in the idol's mouth", "why": "Framed as a slur analogue"},
 {"item": "Shinigami Eyes browser extension palette and branding", "why": "Trans-safety tool; avoid confusion"},
 {"item": "'Remember November 2026' AI polar bear", "why": "TikTok slop, not SF tech Twitter; at most a one-frame Easter egg"},
]

reverify_before_on_screen = [
 "METR values before Opus 4.5", "Navier-Stokes cost '>$40M' and model name 'Astra-next'", "Fields letter signatory count (25/26/17)",
 "Aggregator benchmark scores: FrontierMath T4 97.6%, ARC-AGI-3 62.7%, HLE", "Anthropic run-rate revenue figures", "'1 GW > SF peak demand'",
 "NVDA $1T-$4T milestone dates (from memory)",
]

data = {
 "meta": meta,
 "tldr": [
  "Biggest story: 2026-09-08 OpenAI Navier-Stokes forced-blowup claim (10,000 agents, 88 h, ~130B tokens, Lean-certified Clay alternative C), a literal race with Anthropic's Alpoge and NYU's Buckmaster; Tao lament; Fields Medalists' declaration 2026-09-11.",
  "Claude's own math trophy: 2026-07-19 Jacobian conjecture counterexample credited to Claude Fable 5 (det J = -2; three points map to one), verified locally.",
  "Speed-up in numbers: METR Opus 4.5 ~4h49m (Dec 2025) -> Opus 4.6 ~14.5h (Feb 2026); doubling 7 -> 4.3 -> ~3 months; OpenAI 'automated research intern' (Sept 2026).",
  "Doom became a copypasta: Coxon 'I resigned from Anthropic today' (2026-09-08) and Hubinger '>10% within the next decade'.",
  "Politics went absurd: Trump renames AI 'super intelligence' (2026-09-22); Pentagon supply-chain-risk label upheld (2026-09-25); Fable 5 suspended 18 days (June-July).",
  "Claude iconography: coral spark, spinner glyphs '·✢✳✶✻✽' (a bud-to-bloom 'sunflower'), spinner verbs, Clawd, 'thinking' cap, Golden Gate Claude.",
  "Shinji: specific AI-Twitter format UNRESOLVED; candidates plus a treatment that works for any of them; ask the client for the link.",
  "Emotional thesis: 'all of us are going to know what it feels like to be unable to keep up' (Sahai, 2026-09-24).",
 ],
 "timeline": timeline,
 "events": events,
 "memes": memes,
 "shinji_analysis": shinji,
 "lyric_map": lyric_map,
 "chart_data": chart_data,
 "do_not_use": do_not_use,
 "reverify_before_on_screen": reverify_before_on_screen,
 "idol_design_implications": [
  "Hair/crown = the spark: about a dozen tapered coral petals that open and close with the spinner cycle (closed bud in verses, full bloom on choruses).",
  "Irises carry the spinner glyph; the hook is an extreme close-up of it blooming.",
  "Backup dancers = Clawds in formation; Crustafarian lobster choir for the agents verse.",
  "Merch-as-costume: 'thinking' cap, blue blazer (Claudius), tungsten-cube handbag, International Orange scarf (Golden Gate).",
  "K-pop grammar: fanchant cards (FEEL THE AGI), lightsticks, 'COMEBACK' stamps per model launch; aespa-style human/avatar mirror choreography with a 'SYNK %' HUD.",
 ],
}

OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1))
print("wrote", OUT, OUT.stat().st_size, "bytes;", len(timeline), "timeline,", len(events), "events,", len(memes), "memes,", len(lyric_map), "lyric lines")
# sanity: every lyric-map item id exists
ids = {m["id"] for m in memes} | {e["id"] for e in events} | {"metr_time_horizons"}
missing = sorted({i for row in lyric_map for i in row["items"] if i not in ids})
print("missing ids in lyric_map:", missing)
