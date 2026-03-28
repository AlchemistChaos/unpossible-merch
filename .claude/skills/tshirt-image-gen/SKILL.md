---
name: tshirt-image-gen
description: Generate humorous t-shirt design images for events using Gemini. Covers prompt engineering, comedy personas, image format requirements, and Fourthwall upload constraints. Use when generating or improving t-shirt design prompts, debugging image quality, or adding new design categories.
---

# T-Shirt Image Generation

## Image Format Requirements

**Critical:** The generated image is ONLY the graphic/logo. It is NOT a t-shirt mockup and NOT a person wearing a shirt.

- **Format:** PNG with transparent background
- **Color:** Black ink only — no color, no gradients, no gray
- **Background:** Transparent (no white, no color fill)
- **Style:** High contrast, clean lines, screen-print ready
- **Composition:** Centered, standalone graphic
- **Why:** Fourthwall places the graphic onto their own t-shirt product templates. We select a WHITE t-shirt in Fourthwall, and the black graphic gets printed on it.

## Gemini Prompt Template

```
Create a graphic design for screen printing on a t-shirt.

DESIGN: {title}
CONCEPT: {description}
TEXT ON DESIGN: {slogans}

CRITICAL REQUIREMENTS:
- This is ONLY the graphic/logo — NOT a t-shirt mockup, NOT a person wearing a shirt
- Black ink only on a completely transparent/blank background
- PNG format, no background color at all
- High contrast, clean bold lines suitable for screen printing
- Bold, readable typography — text must be legible at t-shirt scale
- Centered composition, standalone graphic
- Illustration/graphic style only — no photographic elements
- Funny, clever, the kind of design that makes people laugh and want to wear it

COMEDY STYLE: {persona_style_guidance}
```

## Comedy Personas

Each design brief should be written through the lens of one of these comedy personas. The persona shapes the humor style, not the visual style (visuals are always black ink, print-ready).

### 1. Matt Rife Energy
**Style:** Crowd-work roast humor. Self-aware, slightly cocky, riffs on the absurdity of the situation.
**For event merch:** Makes fun of the event itself, the attendees, and the tech industry in a way that's endearing, not mean. Observational humor about hackathon culture.
**Example angles:**
- "I told my agent to build an app and it just opened Twitter"
- Roasting the lobster costume rule
- "My AI agent has more commits than my entire team"
- Making fun of how seriously people take hackathons

### 2. Nate Bargatze Energy
**Style:** Deadpan, wholesome absurdism. Says something completely ridiculous with a straight face. The humor is in how mundane he makes wild things sound.
**For event merch:** Takes the bizarre aspects of AI hackathons (agents coding while humans network, lobster costumes, not touching laptops) and presents them as totally normal everyday things.
**Example angles:**
- "My computer's been working all day. I've been eating snacks." (said like it's a normal job)
- Treating autonomous AI agents like they're just regular coworkers
- The quiet absurdity of wearing a lobster costume to type
- "I don't know what my agent built but I'm presenting it in 20 minutes"

### 3. Hasan Minhaj Energy
**Style:** Smart, high-energy, punchy cultural commentary. Connects tech to broader absurdity. Uses callbacks and escalation.
**For event merch:**  Takes the tech/VC/AI hype culture and punctures it with sharp observations. References sponsors, startup culture, and the gap between what people say AI does vs what it actually does.
**Example angles:**
- Sponsor name mashups as fake startup pitches
- "Raised $50M to let a robot write code I could've copy-pasted from Stack Overflow"
- The absurdity of AI agents competing while humans eat catering
- Tech buzzword overload as visual comedy

## Design Categories with Persona Mapping

| Category | Persona | Description |
|----------|---------|-------------|
| **crisp-simple** | Nate Bargatze | Minimalist typography, deadpan one-liner, clean layout. The joke lands because it's so understated. |
| **funny-meme** | Matt Rife | Bold graphic + roast-style text. Visual gag or illustrated joke about the event. Crowd-pleasing, shareable. |
| **sponsor-logo** | Hasan Minhaj | NASCAR-style sponsor name typography remixed as cultural commentary. Company names styled as absurd mashups or fake products. NOT actual logos. |

## Distribution

Generate 10 briefs total:
- 4 crisp-simple (Nate Bargatze deadpan)
- 4 funny-meme (Matt Rife roast)
- 2 sponsor-logo (Hasan Minhaj commentary)

Self-critique narrows to 6. Quality over quota — if the funniest designs all come from one category, that's fine.

## Evaluation Criteria (for self-critique stage)

1. **Would someone actually wear this?** — The #1 test. If it's not funny enough to wear in public, cut it.
2. **Does the joke land without explanation?** — If you need context to get it, it's too inside-baseball.
3. **Printability** — Clean lines, readable text, works as black on white at t-shirt scale.
4. **Event relevance** — References the specific event (Ralphathon, lobster rule, AI agents, sponsors) not generic tech humor.
5. **Variety** — Final 6 should have a mix of styles, not 6 variations of the same joke.

## Event-Specific Humor Source Material

Pull humor from these real event details:
- **Lobster costume rule:** "If you want to touch your laptop, you put on a lobster costume first"
- **Ralph Wiggum origin:** The event is named after Ralph Wiggum from The Simpsons ("Me fail English? That's unpossible!")
- **Autonomous agents:** Teams set up AI agents to code, then the humans go network while the agents work
- **Sponsors:** OpenAI, Naver D2SF, Hanriver Partners, Kakao Ventures, Bass Ventures, Weights & Biases
- **Prizes:** $10K first place in API credits
- **Previous event:** Started in Seoul as an overnight hackathon where people slept while agents coded
- **Speaker:** Geoffrey Huntley (creator of Ralph Loop) is speaking

## Fourthwall Upload

When uploading the generated PNG to Fourthwall:
1. Select the **white** t-shirt variant as the base product
2. Upload the black PNG graphic
3. The graphic prints as-is on the white shirt
4. Set product name from the brief title
5. Price at $25.00
