# Unpossible Merch — Design Document

## Overview

Unpossible Merch is an autonomous AI agent that generates event-branded t-shirt merchandise for Luma events end-to-end. Given a Luma event where it's been added as co-host, the agent:

1. Scrapes event details (name, theme, sponsors, attendee types) via playwright-cli
2. Generates 10 t-shirt design briefs, self-critiques, narrows to 6
3. Generates images via Gemini Imagen
4. Outputs designs to output/ directory

One-shot execution: the agent runs start-to-finish with no human intervention.

## Target Event

- **Event:** Unpossible Ralphathon
- **URL:** https://luma.com/hh5k4ahp
- **Date:** March 28-31, 2026 (main event March 30-31)
- **Location:** San Francisco, CA
- **Sponsors:** OpenAI, Naver D2SF, Hanriver Partners, Kakao Ventures, Bass Ventures, Weights & Biases
- **Type:** AI agent hackathon

## Pipeline

```
Stage 1: Scrape Luma event (playwright-cli)
Stage 2: Generate 10 design briefs (Gemini text via W&B Inference)
Stage 3: Self-critique & narrow to 6 (Gemini text via W&B Inference)
Stage 4: Generate images (Gemini Imagen - gemini-3.1-flash-image-preview)
Stage 5: Save results + Weave traces
```
