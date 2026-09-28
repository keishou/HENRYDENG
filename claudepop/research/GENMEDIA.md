# GENMEDIA: making the protagonist's plates with fal.ai (playbook for the next session)

Research date: 2026-09-28. This session had no fal key: a queue call returned 405 and the Platform API returned
"API key authentication required". So nothing here has been run against a live model. Every schema and price was read
on 2026-09-28 from:

- the fal catalog: `GET https://api.fal.ai/v1/models`, 1,502 endpoints (saved as `claudepop/out/refs/fal/catalog_2026-09-28.json`);
- each model's `https://fal.ai/models/<endpoint-id>/llms.txt`, 60 files (saved under `claudepop/out/refs/fal/llms/`; a digest of every input and price is in `claudepop/out/refs/fal/summary.txt`);
- fal's docs (queue, errors, CDN, retention; `out/refs/fal/queue.md`).

Prices change often. MiniMax's H3 Max prices are a 50 % promotion that ends 2026-09-30, and the cost model below uses
the list prices that apply after that date.

The quality verdicts come from vendor claims plus the third-party reports cited with each one. None of them has been
checked on this protagonist yet. Stage 0 below is the check.

## 0. Decisions in brief

1. **No single model does everything, so plan shots by route.**
   - Face shots (close-ups and medium shots within about ±30° of frontal): Kling (O3 reference-to-video and v3
     image-to-video with "elements": a frontal image plus 1-3 angle references), MiniMax H3 Max (image-to-video,
     reference-to-video, an H3 LoRA), or Veo 3.1 for hero shots.
   - Face-free plates (backs, silhouettes, hands, wides, environments, "inferred" shots): Seedance 2.5, the most
     capable model for aesthetics and long takes. On fal it rejects any photoreal face.
2. **Seedance will not take his face on fal.** A third-party test on 2026-09-14 rejected even AI-generated photoreal
   faces at input with `content_policy_violation` ("likenesses of real people"). A headless body crop was accepted and
   its wardrobe transferred. ByteDance only allows real faces through its own verified channels. This fits the
   director's stance anyway (profile and back views as silhouettes).
3. **"Previs to plate" is now a product category, and it matches this session's work.** MiniMax H3 Max 3D-to-video
   (released 2026-09-16) turns "Blender renders and 3D previs into photorealistic video" and keeps "layout, camera
   movement, and timing" from the source clip, with image references for appearance. Kling O3 video-to-video
   reference, Luma Ray 3.2 video-to-video (with pose, depth and face controls), Kling v3 motion control and LTX 2.3
   render-to-real do similar jobs. Render the three.js avatar animatic to the exact slot length, then restyle it, and
   the timing is locked by construction.
4. **Keyframes can be pinned to frame numbers.** FLUX 3 keyframes-to-video takes up to 10 keyframes at explicit
   `frame_index` values (5-20 s), and Luma Ray 3.2 takes 1-64 keyframes at 24 fps indexes. Put the keyframes on beat
   frames computed from `claudepop/analysis/song.json`.
5. **The character sheet comes from image editors, then gets locked.** Nano Banana Pro or 2 edit, Seedream 5.0 Pro edit
   (up to 10 references), GPT Image 2.5 edit (up to 16 references) and FLUX.2 max edit produce front, 3/4, profile,
   back, full-body and wardrobe views from the one photo. Score each with ArcFace and have the user approve 12-20
   images. Optionally train a LoRA on them (Krea 2 at $0.003 per step, FLUX.2 at $0.0064 per step, H3 image-to-video
   at $0.01 per step).
6. **Budget.** About 50 plates cost roughly $350 as planned and about $700 with 2x retries, well inside $2,000. Put a
   hard spending cap of $1,200 in the queue client and keep the rest as reserve.
7. **Privacy.** fal CDN URLs are public by default. Send the photo as a data URI or set a file ACL, add
   `X-Fal-Store-IO: 0` and a short `X-Fal-Object-Lifecycle-Preference`, download every output at once to
   `claudepop/out/`, then delete the request payloads through the Platform API.
8. **Midjourney has no API, and its terms forbid automated access.** anabology drove it through browser automation.
   We do not. If the user wants Midjourney frames, he makes them by hand and drops them into `claudepop/out/genmedia/inbox/`.

## 1. Access and the queue API

### 1.1 Environment

- The key comes from the agent proxy. Header: `Authorization: Key <FAL_KEY>`.
- Hosts that need the header (fal-client 1.0.3 source, checked 2026-09-28): `queue.fal.run` and `fal.run` (inference),
  `rest.fal.ai` (file uploads; HANDOFF.md lists the older `rest.alpha.fal.ai`) and `api.fal.ai` (Platform API:
  pricing, estimates, usage, payload deletion).
- Output media come from `v3.fal.media` / `v3b.fal.media` and need no key.
- Check: `curl -sS -o /dev/null -w "%{http_code}\n" https://api.fal.ai/v1/models/pricing?endpoint_id=fal-ai/flux/dev`
  should return 200 once the key is attached (it returns 401 without one).

### 1.2 Queue pattern (from the fal queue docs, 2026-09-28)

```
POST https://queue.fal.run/<endpoint-id>                -> {request_id, status_url, response_url, cancel_url, queue_position}
GET  <status_url>?logs=1                                -> {status: IN_QUEUE | IN_PROGRESS | COMPLETED, error?, error_type?}
GET  <response_url>                                     -> model output JSON (video.url / images[].url ...)
PUT  <cancel_url>                                       -> 202 CANCELLATION_REQUESTED | 400 ALREADY_COMPLETED
```

- **Pitfall.** The status and result URLs use only the first two segments of the endpoint ID. Submitting to
  `bytedance/seedance-2.5/reference-to-video` gives a status URL of
  `https://queue.fal.run/bytedance/seedance-2.5/requests/<id>/status`. Always use the URLs returned by the submit call.
- **Optional headers.** `X-Fal-Request-Timeout` (start deadline), `X-Fal-Queue-Priority: low`, `fal_webhook=<url>`
  query parameter, `X-Fal-Store-IO: 0` (do not keep the JSON payloads, which are otherwise kept 30 days),
  `X-Fal-Object-Lifecycle-Preference: {"expiration_duration_seconds": 604800}`.
- **Errors.**
  - 422 `content_policy_violation` is not retryable. The docs say "flagged by either fal's filter or one of our
    partners'".
  - Also 422: `face_detection_error`, `image_too_small`, `file_too_large`, `no_media_generated`.
  - The 5xx `runner_*` and `*_timeout` types are transient: retry them.
  - fal says: "You are not charged for server errors or for time spent waiting in the queue." Check in the billing
    events on day 1 that content-policy rejections are not billed.
- **MiniMax pitfalls** ([atlascloud, 2026-08-17](https://www.atlascloud.ai/blog/tips/minimax-h3-reference-to-video)):
  malformed requests return 200 and fail 2-3 minutes later; mixing a first frame with references silently drops one
  of them; audio must be declared as `audio/mp3`.

Minimal client to write in the next session as `claudepop/genmedia/falq.py`:

```python
import json, os, time, hashlib, requests
KEY = os.environ.get("FAL_KEY", "")        # empty when the agent proxy injects the header
H = {"Content-Type": "application/json", "X-Fal-Store-IO": "0",
     "X-Fal-Object-Lifecycle-Preference": json.dumps({"expiration_duration_seconds": 7 * 86400})}
if KEY: H["Authorization"] = f"Key {KEY}"

def run(endpoint, payload, ledger="claudepop/out/genmedia/ledger.jsonl", poll=5, est_usd=None, cap_usd=1200):
    spent = sum(json.loads(l).get("est_usd", 0) for l in open(ledger)) if os.path.exists(ledger) else 0
    if est_usd and spent + est_usd > cap_usd: raise RuntimeError(f"budget cap: {spent:.2f}+{est_usd:.2f}")
    key = hashlib.sha1((endpoint + json.dumps(payload, sort_keys=True)).encode()).hexdigest()[:16]
    r = requests.post(f"https://queue.fal.run/{endpoint}", headers=H, json=payload, timeout=120); r.raise_for_status()
    sub = r.json()
    while True:
        s = requests.get(sub["status_url"] + "?logs=0", headers=H, timeout=60).json()
        if s["status"] == "COMPLETED": break
        time.sleep(poll)
    out = requests.get(sub["response_url"], headers=H, timeout=120)
    rec = {"t": time.time(), "endpoint": endpoint, "key": key, "request_id": sub["request_id"],
           "est_usd": est_usd, "ok": out.ok and "error" not in s, "error": s.get("error"), "error_type": s.get("error_type")}
    os.makedirs(os.path.dirname(ledger), exist_ok=True); open(ledger, "a").write(json.dumps(rec) + "\n")
    return out.json() if out.ok else {"error": out.text, **rec}
# After downloading outputs: requests.delete(f"https://api.fal.ai/v1/models/requests/{rid}/payloads", headers=H)
```

The ledger holds endpoint IDs, costs and error types only, no media and no face numbers, and it lives in
`claudepop/out/` (gitignored).

## 2. Models on fal that matter here (as of 2026-09-28)

"Min s" is the shortest clip a model will generate. Our plates are 2-8 s, so generate at least that length and trim.
Prices are USD. The verdicts are for a photoreal young East Asian man in fashion-film lighting.

### 2.1 Identity-consistent stills (character sheet and keyframes)

| Endpoint (catalog date) | Key inputs | Output | Price | Verdict |
|---|---|---|---|---|
| `fal-ai/nano-banana-pro/edit` (2025-11-20) | `prompt`, `image_urls[]` (required, several references), `resolution` 1K/2K/4K, `aspect_ratio`, `safety_tolerance` 1-6 (default 4), `system_prompt`, `enable_web_search` | still | $0.15 per image (4K costs 2x) | **A (expected).** Strongest single-photo identity carry-over and relighting in public tests. Google filters celebrities, and since the Nano Banana 2 launch (2026-02-27) it is stricter on face swaps. False-positive portrait refusals were reported from 2026-07-15 ([Google AI forum](https://discuss.ai.google.dev/t/nano-banana-pro-in-flow-false-policy-violation-on-normal-commercial-portrait-prompts/174894)). Main sheet generator |
| `fal-ai/nano-banana-2/edit` (2026-02-26) | as above, plus `video_url`/`audio_url` context and `thinking_level`; resolution 0.5K-4K | still | $0.08 (2K 1.5x, 4K 2x, 0.5K 0.75x) | **A-.** The cheap iteration twin of Pro |
| `bytedance/seedream/v5/pro/edit` (2026-07-07) | `prompt`, `image_urls[]` up to 10, `image_size` (1024²-2048², default auto_2K), `num_images` | still | $0.0675 per output (≤1536²) or $0.135 (≤2048²), plus $0.0045 per extra input | **A- (expected).** Editorial and fashion aesthetics, strong on East Asian faces, region-precise edits and layers. ByteDance real-face policy on stills through fal is unknown, so probe it |
| `bytedance/seedream/v5/flash/edit` (2026-09-23) | as above | still | $0.027 | B+. Fast drafts |
| `openai/gpt-image-2.5/flare/edit`, `.../sunburst/edit` (2026-09-08) | `image_urls[]` up to 16, `mask_url`, `quality` low to max | still | token-priced ($8 per 1M image input tokens, $30 per 1M output) | **B+/A.** The most precise instruction-following edits ("keeping subject, composition, and background intact"). Good for wardrobe and prop changes on approved frames. Policy on photos of private people: probe |
| `fal-ai/flux-2-max/edit` (2025-12-16) | `image_urls[]`, `safety_tolerance` 1-5 | still | $0.07 for the first MP plus $0.03 per extra MP (inputs count) | B+. Photoreal texture; identity from one reference is weaker than Nano Banana |
| `fal-ai/flux-2-pro/edit` (2025-11-23) | as above | still | $0.03 for the first MP plus $0.015 per extra MP | B. Cheap realism passes |
| `alibaba/qwen-image-3/edit` (2026-07-21) | `image_urls[]` 1-3 ("preserving facial features and identity"), `negative_prompt` | still | $0.04 (1K) / $0.075 (2K) | B. Cheap and good at structure-preserving edits |
| `luma/agent/uni-1/v1/max/edit` (2026-06-09) | `image_url`, `reference_image_urls[]` | still | $0.102 plus $0.003 per reference | B |
| `krea/v2/large/text-to-image` (2026-05-27) | `prompt`, `image_style_references[]` up to 10, `moodboards[]`, `styles[]`, `creativity` | still | $0.060 / $0.065 with style references | **A for mood, no identity input.** Style frames, environments and the moodboard look (the anabology "Midjourney plus moodboard" role). With `fal-ai/krea-2-trainer` ($0.003 per step, $3 per 1000 steps) plus `fal-ai/krea-2/turbo/lora` it can learn his identity from the approved sheet |
| `fal-ai/flux-2-trainer` (2025-11-25) / `-v2` (2026-01-10) | image zip | LoRA | $0.0064 per step ($6.40 per 1000) | B+. Identity LoRA from 15-25 approved images |
| `fal-ai/flux-2-lora-gallery/face-to-full-portrait` (2025-11-25) | `image_urls` (face crop) | still | $0.021 per MP | B-. Quick first full-body drafts from the face |
| `fal-ai/flux-pulid` (2024-10), `fal-ai/instant-character` (2025-04), `fal-ai/ideogram/character` (2025-08, one reference, $0.10-0.20) | a single reference | still | cheap | C. Older identity adapters, fallback only |
| `fal-ai/phota/create-profile` (2026-03-26) | 30-50 photos of the subject | profile | $2.90 per run | Not usable: we have one photo, and generated images of him should not train a "real-person" profile |

### 2.2 Video: image-to-video, reference-to-video, previs-to-plate

| Endpoint (catalog date) | Inputs | Length / resolution | Price (list) | Verdict |
|---|---|---|---|---|
| `fal-ai/kling-video/o3/pro/reference-to-video` (2026-02-04) | `prompt` or `multi_prompt[]` (multi-shot), `start_image_url`, `end_image_url`, `image_urls[]`, `elements[]` = {`frontal_image_url`, `reference_image_urls` (1-3 other angles), `video_url`?, `voice_id`?}, `shot_type`, `generate_audio` | 3-15 s; 16:9 / 9:16 / 1:1 | $0.112/s with audio off ($0.14 with audio) | **A- (expected): main route for face shots.** The element structure is our character sheet. Reviews rank Kling best for character consistency over many clips ([atlascloud 2026](https://atlascloud.ai/blog/guides/best-ai-video-generation-models-2026)). Probe acceptance of his face |
| `fal-ai/kling-video/v3/pro/image-to-video` (2026-02-04) | `start_image_url` (required), `end_image_url`, `elements[]`, `multi_prompt[]`, `negative_prompt`, `cfg_scale` | 3-15 s | $0.112/s audio off | **A-.** Keyframe-driven shots with first and last frames |
| `fal-ai/kling-video/v3/turbo/pro/image-to-video` (2026-06-16) | `image_url`, `multi_prompt[]` (1-6 shots, total ≤15 s) | 1080p, 3-15 s | $0.14/s | B+. Fast |
| `fal-ai/kling-video/v3/4k/image-to-video` (2026-04-22) | as v3 pro | native 4K | $0.42/s | Upgrade for hero shots |
| `fal-ai/kling-video/v3/pro/motion-control` (2026-03-05) | `image_url` (the character), `video_url` (motion source), `character_orientation`, `elements[]` (one face element) | up to 30 s ("video" orientation) | $0.168/s | **A for choreography.** Drive his approved still with our mocap or avatar walk render, with the face bound to an element |
| `fal-ai/kling-video/o3/pro/video-to-video/reference` (2026-02-04) | `video_url` (3-15 s, 720-3840 px), `elements[]`, `image_urls[]` (≤4 in total), `keep_audio` | matches the source | $0.168/s | **A-: previs to plate.** Keeps "motion and camera style" and swaps in the element |
| `minimax/h3-max/image-to-video` (2026-08-23) | `image_url`, `end_image_url`, `target_audio_url`, `prompt_expansion_mode` | 480P / 768P native, 1080P refinement; integer `duration` (default 5) | $0.05 / $0.08 / $0.16 per second after 2026-09-30 (half that until then) | **A- (expected).** Third-party reviews rank H3 first for human motion and walking ([PixMind, 2026-08-01](https://www.pixmind.io/posts/minimax-h3-vs-kling-veo)). Cheap drafts at 480P |
| `minimax/h3-max/reference-to-video` (2026-08-29) | `reference_image_urls[]`, `reference_video_urls[]`, `reference_audio_urls[]` (≤12 files; clips 2-15 s) | as above; aspect up to 21:9 | $0.05 / $0.08 / $0.16 per second, plus reference tokens beyond 4,096 | A-. No automatic real-face filter was reported (atlascloud, 2026-08-17): "users are responsible for asserting usage rights" |
| `minimax/h3-max/3d-to-video` (2026-09-16) | `video_url` (a render up to 15 s and 32 shots), `reference_image_urls[]`, `prompt` | duration taken from the source; 480P / 768P / 1080P | $0.05 / $0.08 / $0.16 per second (5 s minimum) plus reference tokens, about $0.96 for 5 s at 768P | **A: previs to plate.** Built to "transform Blender renders and 3D previs into photorealistic video"; camera, trajectories, timing and object count stay defined by the video |
| `minimax/h3-max/camera-controls` (2026-09-11) | `image_url`, `camera_trajectory[]` (orbit, elevation and distance keyframes) | 480P-1080P | $0.05-0.16/s | B+. Exact orbits and pushes around a frozen frame; the "reconstruction" orbit shots |
| `minimax/h3/i2v/trainer` plus `minimax/h3/image-to-video/lora` (2026-08-02) | a zip of clips or images; `loras[]` | up to 4K | training $0.01 per step; inference $0.0625-0.20/s | B+. An identity or motion LoRA inside the video model itself |
| `bytedance/seedance-2.5/reference-to-video` (2026-07-20) | `image_urls[]` ≤30, `video_urls[]` ≤10 (total ≤30.2 s, 24-60 fps), `audio_urls[]` ≤10, `task` reference / editing / extension, `draft` | 4-30 s; 480p / 720p / 1080p; 24 fps (the token formula uses 24) | $0.2205 / $0.473 / $1.164 per second; with video inputs ×0.6, both directions billed | **A for face-free plates; unusable for face shots on fal.** `draft=true` gives a 480p preview and a `draft_id` that `bytedance/seedance-2.5/draft/complete` finishes at 1080p within 7 days |
| `bytedance/seedance-2.5/image-to-video` (2026-07-20) | `image_url`, `end_image_url`, `draft` | 4-30 s | as above | As above: face-free first frames only |
| `bytedance/seedance-2.5/us/*` (2026-09-19) | same as the non-US endpoints | same | about 20 % more (US-hosted) | Same model hosted in the US |
| `fal-ai/veo3.1/reference-to-video` (2025-10-08) | `image_urls[]` ("consistent subject appearance"; Google documents up to 3), `resolution` up to 4K, `auto_fix`, `safety_tolerance` | 8 s | $0.20/s without audio at 720p/1080p ($0.40 with audio; 4K $0.40/$0.60) | **B+/A for hero face shots**, if Google's person filter accepts him. Reviewers rate Veo best for skin realism and a "film-grade look" |
| `fal-ai/veo3.1/first-last-frame-to-video` (2025-10-08) | `first_frame_url`, `last_frame_url` | 4 / 6 / 8 s | same | A-. Clean moves between two approved keyframes |
| `google/gemini-omni-flash/v1.1/reference-to-video` (2026-08-25) | `image_urls[]`, `reference_video_urls[]` (≤3, ≤3 s each) | 3-10 s; 360p-4K | $0.03 (360p) / $0.10 (720p) / $0.15 (1080p) / $0.30 (4K) per second | B+. The cheapest identity-aware drafting ("characters retaining their face, clothing, and voice") |
| `blackforestlabs/flux-3/keyframes-to-video` (2026-07-17) | `keyframes[]` ≤10 with a unique `frame_index`, `duration` 5-20 (required), `safety_tolerance` 0-4 | 720p / 1080p | $0.17 / $0.29 per second | **A- for timing-locked moves.** Pin poses to beat frames. BFL's filter on real faces: probe |
| `luma/agent/ray/v3.2/image-to-video` (2026-06-09) | `image_url` + `end_image_url`, or `keyframes[]` 1-64 at `keyframe_indexes` (duration × 24 fps), `loop`, `hdr`, `exr_export` | 5 / 10 s; 540p-1080p | 5 s: $0.15 / $0.30 / $1.20; HDR more | B+. The HDR/EXR output suits the grade |
| `luma/agent/ray/v3.2/video-to-video` (2026-06-11) | `video_url`, `start_image_url` or `keyframes[]`, `edit_strength`, or `controls` (pose, depth, normals, trajectory, face) | 5 / 10 s | 5 s: $0.72 / $1.08 / $2.16 | B+. Previs to plate with explicit face and pose control |
| `fal-ai/ltx-2.3-quality/render-to-real` (2026-06-26) | `video_url` (a CG render), optional first frame `image_url`, `intensity` | about 6 s at 720p or 15 s at 480p; 24 fps | $0.0024 per MP of video (121 frames at 720p ≈ $0.27) | B. The cheapest previs-to-real pass, good for tests |
| `alibaba/wan-3.0-prime/image-to-video` / `reference-to-video` (2026-08-24) | `start_image_url` + `end_image_url`, or up to 10 images, 5 videos and 5 audio references | 480p-1080p; `duration` default 5 | $0.068 / $0.14 / $0.28 per second | B |
| `xai/grok-imagine-video/v1.5/reference-to-video` (2026-07-29) | ≤7 reference images, audio | 480p / 720p, 24 fps | $0.08 / $0.14 per second | C+ |

Lip-sync (not planned: the voice is female and there is no lip-sync) exists as `fal-ai/sync-lipsync/v3` ($8 per
minute), `veed/lipsync/v2` ($0.07/s) and `minimax/h3-max/lip-sync/image-to-video` ($0.05-0.32/s).
`pixverse/music-video/vibemv` turns a song into a whole music video ($0.06-0.09/s); avoid it, since it produces
generic slop.

Audio references: Seedance 2.5 and MiniMax H3 accept song excerpts as `audio_urls` / `reference_audio_urls`.
MiniMax treats audio as a "mix steer" (envelope correlation 0.25 in atlascloud's test), not as timing. For us that is
not worth it: the soundtrack is fixed, and the models could invent lip movement. Pass `generate_audio: false` where
the option exists; Kling bills less with audio off.

### 2.3 Image to 3D (optional)

| Endpoint (date) | Inputs | Price | Use |
|---|---|---|---|
| `fal-ai/hyper3d/rodin/v2.5` (2026-05-28) | up to 5 images; `TAPose` (T/A-pose for rigging); quad or triangle mesh; PBR; `texture_delight` | $0.40, plus $0.80 with HighPack | **Best fit.** A riggable, wardrobe-accurate body from the approved full-body sheet, replacing MakeHuman clothes in the previs |
| `tripo3d/h3.1/multiview-to-3d` (2026-04-07) | 2-4 views [front, left, back, right] | $0.20-0.40, plus $0.20 detailed geometry | Multiview mesh of the sheet views |
| `tripo3d/p2/image-to-3d` (2026-09-20) | 1 image | $1.00-1.30 | |
| `fal-ai/trellis-2` (2026) | 1 image | $0.25-0.35 | Cheap tests |

Verdict: the generated heads are not him. Keep our own photo-projected face (the avatar pipeline) for anything facial,
and use generated meshes only for body, costume and silhouettes.

### 2.4 Finishing

`topaz/upscale/video/precision` ($0.20 per 10 s at 1080p, $0.60 at 4K; faithful), `blackforestlabs/flux-video-upscale`
($0.14/s precise, $0.20/s creative at 1080p), `topaz/interpolate/video` (retiming). Upscale only approved takes.

## 3. Likeness and moderation policies, and how to stay within them

The situation is the protagonist's own face, used with his consent in an artistic film. Store that consent as a
one-line note, dated, quoting his request, in `claudepop/out/genmedia/CONSENT.txt` (gitignored). The rules:

| Service | Policy (dated source) | Effect on us |
|---|---|---|
| fal (all models) | [Acceptable Use Policy](https://fal.ai/legal/acceptable-use-policy) (read 2026-09-28): bans "identity theft, impersonation, or deepfakes, including using another person's ... likeness without their consent", and non-consensual intimate imagery; "while [third-party] providers may apply their own safeguards, users remain subject to this acceptable use policy" | Allowed: his own face with consent, non-deceptive. Never another real person's face (no Ilya, Jensen, Altman images). Names appear only in our HUD text, never in prompts or references |
| ByteDance Seedance 2.x (and 2.5) | Model spec: "does not support direct upload of reference images/videos containing real human faces" ([ruoqijin, 2026-04-20](https://ruoqijin.com/blog/seedance-access-and-face-policy)). The rule was tightened after the Feb 2026 deepfake incidents and the Disney/MPA letters ([TechNode, 2026-02-10](https://technode.com/2026/02/10/bytedance-suspends-seedance-2-0-feature-that-turns-facial-photos-into-personal-voices-over-potential-risks/)). Through fal, "no face of any origin passes the input filter" (tests 2026-09-14, [recoupable/skills PR #145](https://github.com/recoupable/skills/pull/145), 2026-09-15). A headless body crop and a stylized face were accepted | Seedance only for face-free plates. Real-face exceptions exist only through ByteDance's own channels: the Jimeng/Doubao "digital avatar" with liveness verification, or Volcengine enterprise portrait authorization. Neither is reachable from fal |
| Google Veo 3.1, Nano Banana, Gemini Omni | Rejects celebrity likeness ("Sorry, we can't create videos from input images containing celebrity or their likenesses"); `personGeneration` handling varies by region ([Google AI forum](https://discuss.ai.google.dev/t/veo-3-1-image-to-video-rejects-documented-persongeneration-allow-adult/181139)); stricter face-swap filtering since 2026-02-27; SynthID watermark | A private adult with consent should pass. Probe. Expect some false-positive refusals, and rephrase the scene without trying to defeat the filter |
| Kling | Reported to block public figures and "private individuals without legal authorization", with a 400 on personality-rights flags ([glbgpt, 2026-04-21](https://www.glbgpt.com/resources/ai-video-human-face-seedance-veo-kling/)). Face lock with elements works for user-supplied faces in practice | Probe. If blocked, Kling's in-app "Face Model" (self-recorded and authorized) is the official path, which only the user can do |
| MiniMax H3 | No automatic real-face filter reported; the user asserts rights ([atlascloud, 2026-08-17](https://www.atlascloud.ai/blog/tips/minimax-h3-reference-to-video)) | Most permissive route for face shots. Consent note applies |
| OpenAI GPT Image 2.5, BFL FLUX 2/3 | Public-figure restrictions; `safety_tolerance` controls (FLUX 1-5, FLUX 3 video 0-4) | Probe |
| Midjourney | No official API as of Aug 2026. Terms: "You may not use automated tools to access, interact with, or generate Assets" ([midjourney/docs ToS](https://github.com/midjourney/docs/blob/main/terms-of-service-discord.md); [unifically, 2026](https://unifically.com/blogs/midjourney-api)). V8.1 became the default on 2026-06-10 | No agent automation. Manual use by the user only |

**Workarounds that stay within the rules**

- Send each shot type to a model whose rules allow it: faces to Kling, MiniMax or Veo; face-free to Seedance.
- Use the director's framing: faces within about ±30° of frontal; profiles, backs and wides as silhouettes, headless
  crops or deliberately "inferred" renders (point cloud or depth). The constraint becomes part of the meaning.
- Previs to plate with our own avatar: the face in the source render is ours, and the model restyles it.
- Composite in our engine: a face-free Seedance environment plate plus a Kling or H3 face plate keyed in. Each model
  only receives inputs its rules accept.
- For verified real-face features on a platform (ByteDance digital avatar, Kling Face Model, Google "Photo to Video"),
  the user completes the verification himself. We do not.

**Not allowed:** adversarial noise, masks or partial occlusion meant to slip a face past a filter, putting real names in
prompts, reusing a rejected input under another account, or sending other people's faces.

**Privacy of the face data** (the repo is public)

- Upload the photo as a data URI (`image_url: "data:image/jpeg;base64,..."`), or through `rest.fal.ai` with a file ACL.
- Add `X-Fal-Store-IO: 0` and a lifecycle of 7 days or less to every request that carries his face.
- Download results at once to `claudepop/out/plates/<shot>/`.
- `DELETE https://api.fal.ai/v1/models/requests/<id>/payloads` after download. It removes the input/output payloads
  and the CDN outputs; the request must be completed first.
- Never paste fal CDN URLs of face images into tracked files.

## 4. Recommended pipeline

Timing source: `claudepop/analysis/song.json` (132 BPM, t0 = 0.2356 s; beat n at t0 + n·60/132; bar b at
t0 + (b-1)·4·60/132). Assume an edit at 24 fps unless the bible says otherwise. Most models output 24 fps: Seedance
(token formula), H3, Luma, Grok and LTX by default. Conform everything else with ffmpeg.

**Stage 0: likeness probe (day 1, about $6).**
- Stills: send the rectified photo (from `claudepop/out/avatar/identity/`) with one neutral prompt ("same man, 3/4 view,
  studio softbox, white shirt") to nano-banana-pro/edit, nano-banana-2/edit, seedream v5 pro edit, gpt-image-2.5 flare
  edit, flux-2-max edit and qwen-image-3 edit.
- Video, cheapest settings: kling o3 pro reference-to-video (3 s, audio off), kling v3 pro image-to-video (3 s), h3-max
  image-to-video (480P, 5 s), gemini-omni-flash v1.1 (360p, 3 s), veo3.1 first-last-frame (4 s, 720p), wan-3.0-prime
  image-to-video (480p), flux-3 image-to-video (720p, 5 s). Add seedance-2.5 image-to-video (480p draft, 4 s) only to
  confirm the block.
- Record accepted or rejected, the error type and the ArcFace verdict in `claudepop/out/genmedia/probe.json`, and write a
  tracked text summary with no face numbers.

**Stage 1: identity pack.**
- Contents: the rectified photo and its mirror, crops (face, face plus hair, head and shoulders), and a text description
  of fixed traits in words only, no measured numbers.
- Optional structure hints: our avatar renders at 0° and ±20°, labelled as renders. Never send the avatar as "the
  person" to image models: they copy its CG look.

**Stage 2: character sheet (about $30).**
- Views: front, 3/4 left and right, profile left and right (expected to be the weakest), back, full body front and back,
  and 3 wardrobe states from the bible, 2 seeds each, from the 2-3 image models that passed Stage 0.
- Composition: one person, plain mid-grey or cold studio background, soft key plus rim, 85 mm look, no text or logos.
  This makes the images reusable as video references.
- Scoring: `python3 claudepop/avatar/tools/face_similarity.py <dir> --json <out>`.
  - Accept at or above the calibrated `match` threshold. Reject below `reject`. The thresholds live in
    `claudepop/out/avatar/identity/scorer_calibration.json` and are never copied into tracked files.
  - Profile and back views cannot be scored reliably (yaw above about 45°): judge them by eye against the approved 3/4
    views and keep hair, ears and neck consistent.
- Approval: the user approves 12-20 frames, which become `sheet/approved/`.
- Optional LoRA: train an identity LoRA on the approved set (Krea 2 or FLUX.2, about $5-10) for cheap consistent
  keyframes, and an H3 image-to-video LoRA (about $15) if H3 becomes the main face route.

**Stage 3: keyframes per shot (about $40).**
- For each shot in `shots.json`, generate 4-6 candidates of the first frame (and the last frame where needed) with the
  approved sheet as references. Use the exact composition from the animatic (the previs frame as a layout reference) and
  the bible's lighting.
- Score with ArcFace, check framing against the animatic, and have Claude look at each image.
- Face-free shots: environment keyframes from Krea 2 or Seedream with the bible's moodboard as style references.

**Stage 4: video plates, drafts then finals (about $240 as planned).**

| Route | Shot type | Inputs | Model |
|---|---|---|---|
| A. Keyframe to video | face shots | approved start (and end) frame plus an element (frontal plus 3 angles) | Kling v3 / O3 pro; H3 Max image-to-video |
| B. Previs to plate | walks and camera moves with exact timing | the avatar animatic rendered to slot length plus handles, and the approved sheet as references | H3 Max 3D-to-video; Kling O3 video-to-video reference; Kling motion control; Luma video-to-video with face/pose controls |
| C. Beat-pinned keyframes | poses that must land on beats | keyframes at the frames of beats or downbeats | FLUX 3 keyframes-to-video; Luma keyframes |
| D. Face-free | environments, hands, silhouettes, backs, the "inferred" point-cloud look | image or video references with no face | Seedance 2.5 (draft 480p, then complete at 1080p) |
| E. Hero upgrade | 3-5 key face shots | an approved Kling or H3 take, or its keyframes | Veo 3.1 1080p, or Kling v3 4K |

- Drafts: up to 3 per plate at the cheapest tier (H3 480P, Gemini Omni 360p, Seedance draft).
- Finals: up to 2 per plate at 1080p.

**Stage 5: automatic verification (after every take; a script that shells out to the existing tools).**
1. Probe with ffprobe: fps, frame count, duration. Duration must be at least slot + 2 × 12-frame handles.
2. Internal cuts: an ffmpeg scene score above 0.3 inside a plate means a multi-shot mistake, so reject.
3. Identity: `face_similarity.py <take.mp4> --every 6 --json`.
   - Use frames where a face is detected and yaw is within ±35° (estimated from the 5 SCRFD keypoints).
   - Accept if the median is at least `match` and the 10th percentile is at least `reject`. Flag if in between.
     Otherwise reject.
   - Require a face in at least 80 % of sampled frames for close-up and medium shots.
   - Record the spread between highest and lowest scores as drift.
4. Timing: frame-difference and optical-flow energy peaks, and for walks the heel-strike period from MediaPipe Pose
   (already in `venv-avatar`), compared with beat times from song.json within ±2 frames. Retime within ±8 % by frame
   blending or Topaz interpolation. Beyond that, regenerate. Route B and C plates are aligned by construction; only
   drift needs checking.
5. Artifacts: build a contact sheet (one frame every 0.5 s) and look at it with the Read tool. Check hands, teeth,
   stray text or logos, wardrobe continuity against the sheet, and background people with faces (reject: a face-free
   plate must stay face-free).
6. Log the take's scores to `claudepop/out/genmedia/verify.jsonl`.

**Stage 6: retries.**
- Rejected on identity: first change the route (a better keyframe, add an element angle, go from reference-to-video to
  image-to-video), then the model. After 3 failures, reframe the shot as a silhouette or "inferred" treatment in the
  edit. It is allowed to fail on purpose.
- Rejected on content policy: never retry the same input. Go to the next model in the route table.
- Stop a plate once it has spent 2.5× its planned cost, and flag it for the director.

**Stage 7: finishing.** Topaz precision upscale on the approved takes only. The plates then go into the locked
three.js / compositing edit (type, HUD, dither and grade are ours, applied in JS).

## 5. Cost model (list prices read 2026-09-28; H3 at post-2026-09-30 prices)

Assumptions: 50 plates with used lengths of 2-8 s (average 4 s). Each generation is billed for about 5 s after minimum
durations and handles.

| Stage | Volume | Unit price | Planned |
|---|---|---|---|
| 0 Probe | about 14 calls | mixed | $6 |
| 2 Character sheet | about 120 stills plus edits | $0.03-0.15 | $30 |
| 2b LoRAs (optional) | Krea 2 or FLUX.2 plus H3 image-to-video | $3-15 each | $25 |
| 3 Keyframes | 50 × 6 candidates plus 50 × 2 edits | about $0.10 | $40 |
| 4 Drafts | 50 × 3 × 5 s | $0.05-0.11/s (H3 480P, Gemini 360p, Seedance draft $0.22/s) | $60 |
| 4 Finals, face (Kling, H3) | 25 × 2 × 5 s | $0.112-0.16/s | $35 |
| 4 Finals, previs to plate (H3 3D-to-video, Kling video-to-video) | 10 × 2 × 5 s | about $0.19/s with reference tokens | $20 |
| 4 Finals, face-free (Seedance 2.5 1080p) | 10 × 2 × 5 s | $1.164/s | $116 |
| 4 Hero (Veo 3.1 1080p, audio off) | 5 × 2 × 8 s | $0.20/s | $16 |
| 7 Upscale | about 250 s | $0.02/s (Topaz 1080p) | $5 |
| **Planned total** | | | **about $355** |
| With 2x retries on stages 3-4 | | | **about $700** |
| Hard cap in `falq.py` | | | **$1,200** (reserve $800) |

Levers: Seedance 1080p is the largest line, so draft everything at 480p and complete only approved drafts through
`draft/complete`. Kling with audio off saves 20-33 %. H3 costs half until 2026-09-30. Veo only for the 3-5 hero shots.

## 6. Midjourney and other off-fal options

- Midjourney V8.1 (default since 2026-06-10; web and Discord only; no API; automation forbidden). If the user wants the
  "Midjourney plus moodboard" look anabology got, he runs the prompts himself (Omni Reference with his photo, plus the
  bible's moodboard) and drops the results into `claudepop/out/genmedia/inbox/`. They go through the same ArcFace and
  review gate.
- Higgsfield ("Soul ID", and "Face Eligibility" for Seedance face references after enterprise-email verification,
  reported 2026-04-20) and BytePlus ModelArk are outside this environment's credentials. Skip them.

## 7. Day-1 checklist for the next session

1. Check the key: `curl https://api.fal.ai/v1/models/pricing?endpoint_id=fal-ai/flux/dev` returns 200. Also check that
   `rest.fal.ai` and `api.fal.ai` are in the credential host list.
2. Re-read `llms.txt` for the endpoints actually used (prices and schemas drift).
3. Write `claudepop/genmedia/falq.py` (section 1.2), `probe.py` (Stage 0) and `verify_plate.py` (Stage 5).
4. Run Stage 0 (about $6). Fill in the route table with what was accepted. Show the user the sheet candidates before
   spending more than $50.
5. Lock the character sheet with the user. Then drafts, verification, finals and the edit.
