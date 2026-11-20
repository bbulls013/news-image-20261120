# The World in One Page — 20 November 2026

A single-image newspaper front page for Friday 20 November 2026, drawn
entirely in code. The program renders a cream broadsheet with a black
masthead, a red accent, the day's lead story (Trump, Xi and Putin in
first three-way talks in China), a cyclone warning for Odisha, and a
row of smaller headlines — all in one deterministic 1024×1024 PNG.

[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/bbulls013/news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/bbulls013/news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

Competition: https://make.fun/bounty/news-image-20261120

## How it works

`main.py` uses only the Python 3 standard library. It defines a fresh
5×7 bitmap font in code, draws the page pixel by pixel into an RGB
buffer (masthead, dateline, headlines, three flag panels and a
cyclone spiral), then encodes a PNG with `zlib` and `struct`
(filter 0 on every row, fixed compression level). There is no clock,
randomness or network access, so two runs produce byte-identical
output.

## Run

```bash
python3 main.py
```

Writes `entry.png` (1024×1024) to `$MAKEFUN_OUTPUT_DIR` when set,
otherwise to `/output`.

## License

MIT — see `LICENSE`.
