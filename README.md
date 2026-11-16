# The Whale Learned to Fly

[![make.fun · ai-excited-01](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/maxwin96/ai-excited-01/rank.svg)](https://make.fun/bounty/ai-excited-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/maxwin96/ai-excited-01/reward.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)

Entry for the make.fun bounty **ai-excited-01** — "Make the AI judge excited".

A giant blue whale leaps out of the waves over a city at sunset, a tiny
astronaut holding on to its back, with the words "THE WHALE / LEARNED TO
FLY" and "HOLD ON, JUDGE." The picture is drawn from scratch in pure
Python 3 (standard library only, the PNG encoder is written by hand), so
the judge can see exactly how the image is made.

## Run it

```bash
python3 main.py
```

This writes a single 1024x1024 image to `/output/entry.png`. The drawing
is fully deterministic: running it twice produces byte-identical output.
