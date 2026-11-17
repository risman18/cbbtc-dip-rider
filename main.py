"""Dip rider: a cbBTC trading bot for make.fun's bars-replay/v1.

Strategy (one cycle, long only, integer math only, fully deterministic):

- The bot speaks the agent-fun/bars-replay/v1 protocol through the kit's
  Python shim (vendor/makefun_bars.py): the harness sends a hello, then one
  batch per one-minute bar, and the bot answers each batch with its orders.
  An order decided on a batch fills at the next bar's open, paying the 4 bps
  fee, 2 bps of modelled slippage and constant-product price impact, so a
  full-size round trip costs roughly 26 bps: the bot trades at most twice.
- Entry: it waits for a deep dip. When a bar's close is at least DIP_BPS
  below the first scored close of the window, it buys with all its cash.
  Buying a sharp dip means the bounce only has to beat the round-trip cost,
  and cash held the rest of the time cannot bleed fees.
- Fallback: if no dip has come by FALLBACK_SEQ, it buys anyway, so the
  entry always makes at least one trade (the race guardrail asks for one).
- Exit: while holding, it tracks the highest close since the entry. When a
  close falls TRAIL_BPS below that peak, it sells everything and is done:
  one dip, one ride, one exit, no re-entry, no fee bleed from churn.

Every comparison is integer arithmetic on the bar closes the batch itself
carries; the bot reads no clock, no file and no environment, so two runs on
the same window answer byte for byte the same.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
#: Buy when a close is this far below the window's first scored close.
DIP_BPS = 85
#: Sell when a close falls this far below the highest close since entry.
TRAIL_BPS = 85
#: If no dip has triggered by this batch, buy anyway (one trade guaranteed).
FALLBACK_SEQ = 1200
#: Reject a fill priced further than this from the close we decided on.
MAX_SLIPPAGE_BPS = 200
BPS = 10_000


class DipRider:
    """The strategy's state: where the window started, and the one cycle."""

    def __init__(self):
        self.ref_close = None  # the first scored close of the window
        self.peak_close = None  # highest close since the entry was decided
        self.held_once = False  # a position has been seen: the cycle ran

    def on_batch(self, state, batch):
        if state.warming_up:
            return []
        close = state.close(SYMBOL)
        if close is None:
            return []
        if self.ref_close is None:
            self.ref_close = close
        holding = state.positions.get(SYMBOL)
        qty = holding.qty if holding is not None else 0
        if qty > 0:
            self.held_once = True
            if self.peak_close is None or close > self.peak_close:
                self.peak_close = close
            # Trailing exit: the ride is over once the close gives back
            # TRAIL_BPS from its peak; sell the whole position.
            if close * BPS <= self.peak_close * (BPS - TRAIL_BPS):
                return [self._sell(state, qty)]
            return []
        if self.held_once:
            # The exit filled; the one cycle is complete. Stay in cash.
            return []
        # Flat and never held: look for the dip, else take the fallback.
        if close * BPS <= self.ref_close * (BPS - DIP_BPS) or state.seq >= FALLBACK_SEQ:
            self.peak_close = close
            return [self._buy(state)]
        return []

    def _buy(self, state):
        return {
            "side": "buy",
            "symbol": SYMBOL,
            "notional_quote_units": state.cash,
            "max_slippage_bps": MAX_SLIPPAGE_BPS,
        }

    def _sell(self, state, qty):
        return {
            "side": "sell",
            "symbol": SYMBOL,
            "qty": qty,
            "max_slippage_bps": MAX_SLIPPAGE_BPS,
        }


def main():
    bot = DipRider()
    makefun_bars.run(bot.on_batch)


if __name__ == "__main__":
    main()
