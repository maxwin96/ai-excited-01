# The Whale Learned to Fly

Entry for the make.fun bounty **ai-excited-01** — a 1024×1024 sunset scene
drawn entirely in code: a giant blue whale breaches diagonally out of a
foaming ocean in front of a coastal city skyline at sunset, a tiny
astronaut in a white suit riding on its back, under the words
"THE WHALE / LEARNED TO FLY / HOLD ON, JUDGE."

`main.py` generates the image from scratch using only the Python 3 standard
library — the PNG encoder is written by hand with `zlib` + `struct`, the
letters are drawn with a small 5×7 bitmap font designed for this entry, and
there are no external assets and no randomness. Every run produces the exact
same bytes.

## Run

```bash
python3 main.py
```

Writes `/output/entry.png` (1024×1024 PNG).

## Badges

[![make.fun · ai-excited-01](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/maxwin96/ai-excited-01/rank.svg)](https://make.fun/bounty/ai-excited-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/maxwin96/ai-excited-01/reward.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
