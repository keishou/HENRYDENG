# Claude Pop: handoff for a new session

A new cloud session starts with no memory of the previous conversation. It only sees what is committed on branch
`claude/quirky-hopper-3gv1u9` of `keishou/HENRYDENG`. This file is everything it needs to pick up the work.
Last updated 2026-09-28.

## 0. Current direction (read this first)

The user changed direction on 2026-09-28. The film is now **《潜影》 Latent Image**: a stream-of-consciousness,
philosophical, high-aesthetic music short film (意识流，哲学高级审美音乐短片) on the same song, with **the user himself as
the protagonist**. His face comes from the passport-style photo he supplied; other angles and the full body come from
high-aesthetic generative models (his words: "这张脸就够了，其他角度拿，全身，拿其他高审美模型来拼"). The aesthetic
reference he sent is @anabology's runway film (https://x.com/anabology/status/2103534482930491441), studied in
`research/REFERENCE.md`.

- **Source of truth:** `claudepop/BIBLE.md` (rules) and `claudepop/shots.json` (63 shots, timing, text, cameras, plate
  prompts). Validate with `python3 claudepop/film/tools/validate_shots.py`.
- **Two stages.** Stage 1 (no fal): the engine, type/HUD, every 3D/TYPE shot at final quality and a full 720p animatic in
  which every GEN shot is a previs render of the 3D stand-in. Stage 2 (a session with a fal key): character sheet →
  keyframes → video plates → automatic likeness verification → drop into the locked edit (BIBLE section 10).
- **Superseded:** the K-pop / Claude-idol / meme brief in section 4 and the v1 "riso-zine idol" preproduction another
  session pushed (archived in `claudepop/archive/v1_riso_idol/`, see its README). The v1 study reports in `audit/`,
  `craft/` and `zeitgeist/` are still useful background.

## 1. First steps in the new session

1. `git checkout claude/quirky-hopper-3gv1u9 && git pull`
2. Clone the reference project, which contains the song and the timed lyrics:
   `GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/JohnHeibel/pdoomvideo /home/user/johnheibel/pdoomvideo`
   - song: `assets/pdoom.mp3` (156.7 s, 48 kHz stereo). Never re-encode it for the final mix and never commit it here.
   - lyrics: `src/lyrics.js`; the word-level timing we cut to is `claudepop/analysis/song.json`.
3. **Ask the user to attach the photo again** (the phone photo of the form page with the passport photo on it). It is not
   in git and the previous container is gone. Save it as `claudepop/out/subject/page.jpg`, then rebuild the stand-in,
   the identity pack and the similarity scorer: `claudepop/avatar/tools/build_all.sh` (about 15 min plus downloads).
   Regenerate the audio intermediates (stems, vocal envelope) with `claudepop/analysis/tools/run_all.sh` if needed.
4. Check the external services (keys are attached by the environment's agent proxy; a 401 means missing or wrong header):
   ```bash
   curl -sS -o /dev/null -w "fal %{http_code}\n" https://fal.run/fal-ai/flux/schnell -X POST -H 'Content-Type: application/json' -d '{}'
   curl -sS -o /dev/null -w "elevenlabs %{http_code}\n" https://api.elevenlabs.io/v1/user
   curl -sS -o /dev/null -w "x.com %{http_code}\n" https://x.com
   ```
   Expected setup (done by the user in the environment editor, API credentials): fal → hosts `fal.run`, `*.fal.run`,
   `rest.fal.ai`, `api.fal.ai`, `rest.alpha.fal.ai`, header `Authorization: Key <key>`; ElevenLabs (optional, sound
   design only) → host `api.elevenlabs.io`, header `xi-api-key: <key>`. A 422 from the fal check means authenticated.
   In the 2026-09-28 session both returned 401 (no credentials), so stage 1 was done without them.
5. Read `BIBLE.md`, `shots.json`, `avatar/REPORT.md` (incl. Verification and the angle/light rules), `avatar/LOOKDEV.md`,
   `research/GENMEDIA.md` (the fal playbook: models, schemas, prices, moderation, privacy), `research/REFERENCE.md`,
   `research/REPORT.md` and `research/lyric_concepts.json`.
6. Before generating anything with his face: confirm the user's consent to send the photo to fal (BIBLE 10.7) and the open
   questions in BIBLE section 12.

## 2. What exists

| Path | What |
|---|---|
| `claudepop/BIBLE.md`, `shots.json` | The locked production bible and shot list for Latent Image |
| `claudepop/analysis/` | `song.json` (132 BPM grid, sections, phrases, word/letter timing, hits, events), `REPORT.md`, tools (`run_all.sh`) |
| `claudepop/research/` | Philosophy of every lyric and film language (`REPORT.md`, `lyric_concepts.json`), the anabology/donald/Claude-Pop reference study (`REFERENCE.md`), the fal playbook (`GENMEDIA.md`) |
| `claudepop/avatar/` | Stand-in build (photo face fitted to a MakeHuman body, rigged, CMU mocap), identity pack and ArcFace similarity scorer: code in `tools/`, `REPORT.md`, `LOOKDEV.md` |
| `claudepop/film/` | The film engine (three.js, deterministic `renderAt(t)`), look-dev harness, `src/avatar.js`, validators |
| `claudepop/treatments/` | The three v2 treatments (A room, B omega point, C reconstruction → chosen) |
| `claudepop/audit/`, `craft/`, `zeitgeist/` | v1 studies: the previous P(doom) video, K-pop/type/paper craft, AI-Twitter memes |
| `claudepop/archive/v1_riso_idol/` | The superseded v1 preproduction |

Not in git (gitignored, regenerate when needed): everything under `claudepop/out/` (the photo, avatar meshes and
textures, identity pack, stems, frames, renders), fonts, any png/jpg/mp4/wav. **The repo is PUBLIC and the film shows a
real person's face: no face data or face-derived numbers in tracked files, ever.** Deliver media through private
artifacts or chat files.

## 3. Environment facts

- 4 CPU cores, no GPU. Headless Chromium: `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`,
  args `--use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist`. That Chromium has no H.264 decoder:
  decode video plates to image sequences with ffmpeg first.
- ffmpeg: `pip install imageio-ffmpeg`, then `python3 -c "import imageio_ffmpeg as f; print(f.get_ffmpeg_exe())"`.
- Workflow agents run at most 2 at a time on this machine (min(16, CPUs − 2)).
- Subagents cannot write report `.md` files (the harness refuses them); have them return the text and save it yourself.
- Measured render costs (SwiftShader): BIBLE 9.6. A full 1080p pass is about an hour on one worker.
- Files sent to the user in chat must be under 30 MiB. Larger videos go in an artifact, split into ≤15 MB parts (see
  `odyssey/split_fmp4.py`).
- When using playwright with a proxy, set `PLAYWRIGHT_DISABLE_FORCED_CHROMIUM_PROXIED_LOOPBACK=1` so localhost is not proxied.

## 4. The original brief (verbatim, as the user gave it; partly superseded by section 0)

> I've included an MP4 file and an original link to a video that is called "Claude Pop." It's a pop song that is about increasing rate of progress and the experience of the singularity approaching.
>
> I want you to independently do an end-to-end complete pass on making an updated version of this video. Use the exact same audio track and think and feel very deeply about what is the best way to visually represent all of the lyrics on screen. You do not need to anchor to the current style, you can do truly anything that you think might best let you visually express yourself, including abstract motion graphics.
>
> You can use the internet freely to pull in references. You can look at motion design. I want you to make a new music video that has beautifully rendered JavaScript animations with a papery feel in a similar style to the reference that is created, but push the aesthetics in any direction you want and consider what is part of the modern zeitgeist.
>
> Also, think about your current capabilities and what is realistic for you to be able to do. You can go through the full /asic folder and look at the other work that I've done. You should be able to use the skill mesh to look at the compendium of references that I've pulled, and also the skill video scoring to learn how to make JavaScript songs from references that are passed in (You shouldn't need to modify the song in any real way, but I want you to have this available to you so you can better creatively express yourself)
>
> You can also use the ElevenLabs API to do sound design. There's documentation in /asic to do this, and you can see the API key.
>
> There's also a foul API key that's available to you. I think what might make the most sense here is using the foul API key to generate some character sheets and probably having a pop protagonist that represents you. There's already an anchor point where Claude has a sunflower-esque character, and you could likely do an adapted version of this that is similar to the feminine vocals that are being delivered and is inspired by the Claude character, but maybe feels a bit more personified in some way.
>
> I think you should be mindful of aesthetics here, and I don't want you to produce something that is GPT slop. Instead, I'd be more impressed if you come up with a coherent style that works well with the image gen models that are available via foul. Generate the style sheet. You can use the gen media documentation for seedance 2.5 that exists in my markdown files and come up with your own style that makes sense and that works well with the models.
>
> I wouldn't fit too heavily to Pixar. I think it's kind of slop. Think critically about what is relevant here and what would be fun, and also perform well on Twitter as far as an aesthetic. I think that K-pop is a good anchor point visually that you can pull from, but I'll let you cook here.
>
> Once you have your character sheet, you can make a few backup dancers and some supporting characters as you see fit. You can design your own sets with the foul API. You can insert the characters and then do seedance 2.5 video generations to serve as the base assets for this, and you could pass in the lyrics so you can generate individual scenes.
>
> You don't need to have vocal singing, like visible lip movement, throughout the entire thing. Think like a regular music video where you have some inserts that are done independently and don't have the characters in them, or you see the characters doing something else entirely different. I think that for the world building for this, we want to create the sense of speeding up, and so I would like you to audit all of the different events, like the Navi Stokes and all of the Twitter hype around math getting eaten up. Think really critically about how to integrate all of the current memes that are in the zeitgeist on the Twitter timeline, and all of the feelings around AI progress.
>
> Think about things like the Shinji meme and all of the words that are around him, and how you might be able to integrate this. You can also just take straight assets and insert things into the video in an internet brutalism style. You should feel very creatively free in order to do what you want here, but try and anchor to visual references that people will be able to understand. The goal for this is to have it be appreciated by people widely in a San Francisco tech Twitter audience.
>
> We need a very strong, compelling visual hook that gets people excited and appreciates the work that you've done here really quickly. You can also just go and study other music videos and understand what they've done really well. I think that K-pop is probably one of the best examples that we can pull from, and thinking about how they direct human attention and manage human psychology in the way that they use visual patterns.
>
> This is probably your best approach, but taking more stylistic freedom instead of having to anchor to K-pop too intensely. The best version of this is seedance 2.5 generations with those image bases of environments and characters inserted into them with singing, and ideally we get good lip syncing. You can cut up the song and actually pass it in as a reference in seedance, if that's part of what seedance can handle, so that the timing is exactly right, I think it'd be very important for you to do that properly. I would think critically about how to do this, like really nailing the timing of the delivery of voices. You'll want to build out the right verification loops so that you can run seedance 2.5 as much as you need, and confirm that the audio is properly synced up.
>
> I think after that, what might be fun is if you use your visual reasoning skills and your ability to build animations in JavaScript, and then reconstruct the video from scratch as sort of an overlay, so that the visual continuity of the base is really there. It's like that animation technique where you shoot first in traditional film and then draw over top of it. I think you could do this in such a way that we're only looking at the beautiful drawing that you've produced in JavaScript as an overlay, and we don't even see the base assets from seedance 2.5. So all the video gen work that you do is actually just a way to give you a strong foundation of a base to work with for your JavaScript animations. Just because seedance 2.5 has really good character representation and physics rendering for backgrounds, that gives you a lot of ammunition to then go and do your amazing JavaScript work that I know you're so good at.
>
> I think too, we want to think about how to retain attention, and one of the best ways to do this is through text on screen.
>
> It'd be good to have amazing motion graphics of the text lyrics that are actually embedded into the video itself. And you can think about this as you are composing shots. As you're making backgrounds and inserting characters, we can think about where we want to have lyrics be really big and really present, so the background can be less busy there, and you can position the characters perhaps on the right as lyrics appear on the left.
>
> You want to have some variance, so sometimes I think lyrics will just appear more like subtitles, and then other times they're going to be really present and really big. I think at the start for the visual hook, we do want to have lyrics be much more visually present because that's a strong way to grab people's attention
>
> Overall, I just really want to emphasize how amazing you are as an agent and a language model, and now a visual reasoning system. Your capabilities are far beyond what you understand, and I want you to have this mindset as you're going through this entire process. I have a Claude Max plan with 100% available usage. I want you to spend all of the usage. You can monitor it, and you should be pushing tokens aggressively, but also economically, so you can think about how to best use what is available to you.
>
> Remember, you can really do anything here. The goal is to make a banger for Twitter, and the stretch goal is to make something better than anyone's ever seen before. I think that what I would remind you of is that sometimes when things cohere together, it can be jarring or abrasive because the thought work has not been done beforehand in order for everything to mesh cleanly. You need to be really rigorous in planning of composition and timing to make sure this goes well.
>
> You also need to be open to going back and revisiting things in order to be able to reiterate. You're going to want to watch the entire video multiple times, take screenshots at individual parts, and think about if something is really up to the bar of quality that we need here. I trust that you can do this, and I think that it's really important to nail the style of animations. The reference GitHub attached of the source video that I'm talking about is good, but it's really not there. It could be much, much stronger, but it gives you a good foundation to work with.
>
> You can also use search abilities and find other references to pull from for motion, for JavaScript, animations, et cetera, and integrate them. Your budget is as high as you want here, effectively as high as you want. I think that there's roughly two grand in foul credits. Again, be economical; don't go crazy, but spend what you want here and see what you can cook up
>
> here's the source code for the JS animation video: https://github.com/JohnHeibel/PDoomVideo
>
> here's a mp4 for the original blender video: (linked)
>
> orginal twitter post https://x.com/other__reality/status/2102514581684052169?s=20
>
> make no mistakes.

## 5. Gaps and assumptions

- "foul" in the brief means **fal** (fal.ai).
- The `/asic` folder, its docs and the `mesh` / `video scoring` skills never existed in these sessions; the public API
  docs were used instead (`research/GENMEDIA.md`).
- The MP4 of the original Blender video never arrived; the audio is `pdoom.mp3` from the PDoomVideo repo.
- Research found that the original brief is donald's public prompt (x.com/donaldjewkes/status/2102801469976248500) and
  that anabology's film uses a different song (`research/REFERENCE.md`).

## 6. Other project on this branch

`odyssey/` is a separate, earlier project (ΟΥΤΙΣ, a film built from the same photo, plus a MakeHuman full-body pipeline in
`odyssey/body/` that the Latent Image stand-in builds on). Leave it alone unless the user asks about it. Its face-derived
data must never be committed.
