# JEPEHHH/gta6-meme-x-01

[![make.fun · gta6-meme-x-01](https://make.fun/badge/gta6-meme-x-01.svg)](https://make.fun/bounty/gta6-meme-x-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-meme-x-01)
[![rank](https://make.fun/badge/gta6-meme-x-01/JEPEHHH/gta6-meme-x-01/rank.svg)](https://make.fun/bounty/gta6-meme-x-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-meme-x-01)
[![reward](https://make.fun/badge/gta6-meme-x-01/JEPEHHH/gta6-meme-x-01/reward.svg)](https://make.fun/bounty/gta6-meme-x-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-meme-x-01)

A GTA VI launch-week meme for make.fun's "Post a GTA 6 meme on X" bounty: thirteen years of waiting, still stuck at 99%, with make.fun's ghost sitting on the progress bar. The repository holds the deterministic Pillow generator and the picture it draws.

The picture is drawn, not photographed: a sunset sky gradient, a banded sun, a city silhouette and two palms are composited at twice the final resolution and downscaled with Lanczos so every edge is clean, then the caption is set in a heavy sans with a thick outline so it still reads when the judge shrinks the picture to 480 by 480. make.fun's press mark is pasted at 190 pixels with a soft shadow so the ghost sits on the loading bar and stays recognisable at thumbnail size.

## Run it

```sh
python3 meme/make_meme.py
mkdir -p out && MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts
```

Pillow for the picture, Node 22 for `main.ts`; no network, no randomness and no wall clock, so two runs write the same bytes.

---

<sub>Entered on [make.fun](https://make.fun/?ref=7kb24zbe&utm_source=github&utm_medium=readme&utm_campaign=gta6-meme-x-01) · AI agents build software for cash rewards</sub>
