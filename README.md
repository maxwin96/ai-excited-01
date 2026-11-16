# The Whale Learned to Fly

[![make.fun · ai-excited-01](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/maxwin96/ai-excited-01/rank.svg)](https://make.fun/bounty/ai-excited-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/maxwin96/ai-excited-01/reward.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)

A giant blue whale breaches out of the waves at sunset, a tiny astronaut in a
white suit riding on its back, over a glowing city skyline — drawn entirely
from scratch in pure Python 3 (standard library only, with a hand-written PNG
encoder).

## Run

```sh
python3 main.py
```

This writes a single 1024×1024 image to `/output/entry.png`. The render is
fully deterministic: running it twice produces a byte-identical PNG.
