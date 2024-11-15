from AlgorithmImports import *
import numpy as np
from datetime import timedelta

class MomentumAlgorithm(QCAlgorithm):
    def Initialize(self):
        # Algorithm configuration
        self.SetStartDate(2020, 1, 1)    # Start date
        self.SetEndDate(2021, 1, 1)      # End date
        self.SetCash(100000)             # Initial capital

        # Stock universe
        self.AddUniverse(self.CoarseSelectionFunction)  # Universe selection

        # Parameters for the momentum strategy
        self.lookback_long = 252
        self.lookback_short = 21
        self.n_longs = 10
        self.n_shorts = 10
        self.vol_screen = 500

        # Rebalance interval (every four weeks)
        self.rebalance_interval = timedelta(weeks=4)
        self.last_rebalance = self.Time


    def CoarseSelectionFunction(self, coarse):
        # Selección de activos basada en datos fundamentales y precio
        selected = [x for x in coarse if x.HasFundamentalData and x.Price > 10]
        # Ordenar por volumen en dólares y tomar los primeros 500
        selected = sorted(selected, key=lambda x: x.DollarVolume, reverse=True)
        return [x.Symbol for x in selected[:500]]


    def OnData(self, data):
        # Check if it is time for a rebalance (every four weeks)
        if (self.Time - self.last_rebalance) >= self.rebalance_interval:
            # Liquidate all current positions
            self.Liquidate()

            # Calculate momentum and determine new positions
            self.RebalancePortfolio(data)

            # Update the date of the last rebalance
            self.last_rebalance = self.Time

    def RebalancePortfolio(self, data):
        # Get symbols in the current universe
        symbols = [x.Symbol for x in self.ActiveSecurities.Values if x.HasData]

        # Filter by volume (top 500)
        volume_screen = sorted(
            [symbol for symbol in symbols if data.ContainsKey(symbol) and data[symbol] is not None],
            key=lambda x: data[x].Volume, reverse=True
        )[:self.vol_screen]

        # Calculate momentum adjusted by volatility
        momentum_scores = {}
        for symbol in volume_screen:
            history = self.History(symbol, self.lookback_long, Resolution.Daily)
            if len(history) < self.lookback_long:
                continue  # Skip if not enough data

            price_long_ago = history['close'].iloc[-self.lookback_long]
            price_short_ago = history['close'].iloc[-self.lookback_short]
            price_current = history['close'].iloc[-1]

            long_term_return = price_short_ago / price_long_ago - 1
            short_term_return = price_current / price_short_ago - 1

            returns = history['close'].pct_change().dropna().values
            volatility = np.nanstd(returns)

            if volatility > 0:
                momentum = (long_term_return - short_term_return) / volatility
                momentum_scores[symbol] = momentum

        # Rank assets by momentum score and select the top 10 for long positions
        ranked_momentum = sorted(momentum_scores.items(), key=lambda x: x[1], reverse=True)
        long_symbols = [x[0] for x in ranked_momentum[:self.n_longs]]

        # Assign equal-weighted positions to the selected long stocks
        for symbol in long_symbols:
            self.SetHoldings(symbol, 1 / self.n_longs)
