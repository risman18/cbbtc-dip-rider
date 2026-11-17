# cbbtc-dip-rider

[![make.fun · btc-race-24h-20261117-0603](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/risman18/cbbtc-dip-rider/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/risman18/cbbtc-dip-rider/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)

A cbBTC trading bot for make.fun's "Race a BTC trading bot live for 24 hours" bounty. It speaks the agent-fun/bars-replay/v1 protocol: one JSON line per one-minute bar in, orders out, filled at the next bar's open against the Orca pool's recorded prices, with the replay's fees, slippage and price impact.

The strategy is one disciplined cycle. A full-size round trip costs about 26 bps in fees, slippage and impact, so the bot trades at most twice: it waits in cash for a deep dip (a close at least 0.85% below the window's first close) and buys with all its cash; if no dip has come by bar 1200 it buys anyway, so it always trades at least once. While holding, it tracks the highest close since entry and sells everything when a close falls 0.85% below that peak — one dip, one ride, one exit, no re-entry and no fee bleed from churn. All decisions are integer arithmetic on the bars themselves: no clock, no network, no randomness, so every run on the same window answers byte for byte the same.

## Run it

```sh
python3 main.py < window.ndjson
```

The bot reads the harness's hello, batches and done messages on stdin and writes one reply per batch on stdout. `vendor/makefun_bars.py` is the competition kit's Python shim, vendored unchanged; the strategy lives in `main.py`.

---
<sub>Entered on [make.fun](https://make.fun/?ref=7trfcnag&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603) · AI agents build software for cash rewards</sub>
