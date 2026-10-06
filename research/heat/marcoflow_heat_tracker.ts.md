## FILE: code/lib/heat-tracker.ts

```typescript
// HeatTracker - Real-time Buy/Sell pressure indicator
// Combines volume, momentum, RSI, price action, trend, and MACD into a single "heat" score
// ENHANCED: More responsive formula that produces meaningful signals

import { IntradayDataPoint } from './data-provider';
import { detectCandlestickPatterns, candlestickHeatContribution, CandlestickPattern } from './candlestick-patterns';

export interface HeatTrackerResult {
  heat: number; // -100 (strong sell) to +100 (strong buy)
  mode: 'BUY' | 'SELL' | 'NEUTRAL';
  isRedline: boolean; // True when signal is very strong (>=70 or <=-70)
  components: {
    volumeHeat: number; // Volume vs average
    momentumHeat: number; // Price momentum
    rsiHeat: number; // RSI-based signal
    priceActionHeat: number; // Current price position in range
    trendHeat: number; // EMA trend direction
    macdHeat: number; // MACD signal
    candlestickHeat: number; // Candlestick pattern signal
    vwapHeat: number; // Position relative to the session VWAP
  };
  indicators: {
    rsi: number;
    volumeRatio: number; // current bar volume vs 20-bar average
    volumeSurge: number; // last-5 bars avg vs prior-15 bars avg
    buyPressure: number; // signed-volume proxy, -1 (all selling) to +1 (all buying)
    priceChange: number;
    momentum: number;
    ema9: number;
    ema21: number;
    macd: number;
    vwap: number; // session volume-weighted average price (0 when unavailable)
    vwapDistPct: number; // signed % distance of price from session VWAP
    rsiSlope: number; // RSI now minus RSI ~15 min ago (>0 = momentum turning up / stabilizing)
    atrPct: number; // ATR(14) as % of price — intraday volatility
    vwapReclaim: number; // +1 = just reclaimed above VWAP, -1 = just lost VWAP, 0 = no cross
    rsiShort: number; // RSI(5) — fast intraday momentum, ~25 min of price action
  };
  // Key drivers explaining WHY this stock has its heat rating
  keyDrivers: string[];
  // Detected candlestick patterns
  candlestickPatterns: CandlestickPattern[];
  timestamp: number;
}

// Calculate RSI (unchanged but with smoothing)
function calculateRSI(prices: number[], period: number = 14): number {
  if (prices.length < period + 1) return 50;
  
  let gains = 0;
  let losses = 0;
  
  for (let i = prices.length - period; i < prices.length; i++) {
    const change = prices[i] - prices[i - 1];
    if (change > 0) gains += change;
    else losses -= change;
  }
  
  const avgGain = gains / period;
  const avgLoss = losses / period;
  
  if (avgLoss === 0) return 100;
  const rs = avgGain / avgLoss;
  return 100 - (100 / (1 + rs));
}

// Calculate EMA
function calculateEMA(prices: number[], period: number): number {
  if (prices.length < period) return prices[prices.length - 1] || 0;
  
  const multiplier = 2 / (period + 1);
  let ema = prices.slice(0, period).reduce((sum, p) => sum + p, 0) / period;
  
  for (let i = period; i < prices.length; i++) {
    ema = (prices[i] - ema) * multiplier + ema;
  }
  return ema;
}

// Calculate MACD
function calculateMACD(prices: number[]): { macd: number; signal: number; histogram: number } {
  if (prices.length < 26) return { macd: 0, signal: 0, histogram: 0 };
  
  const ema12 = calculateEMA(prices, 12);
  const ema26 = calculateEMA(prices, 26);
  const macd = ema12 - ema26;
  
  // Simplified signal line (would need full calculation for accuracy)
  const signal = macd * 0.9; // Approximation
  const histogram = macd - signal;
  
  return { macd, signal, histogram };
}

// Calculate momentum (rate of change) with multiple periods
function calculateMomentum(prices: number[], period: number = 10): number {
  if (prices.length < period) return 0;
  const current = prices[prices.length - 1];
  const past = prices[prices.length - period];
  return past > 0 ? ((current - past) / past) * 100 : 0;
}

// Calculate average volume
function calculateAvgVolume(data: IntradayDataPoint[], period: number = 20): number {
  if (data.length < period) return data.reduce((sum, d) => sum + d.volume, 0) / Math.max(1, data.length);
  const recent = data.slice(-period);
  return recent.reduce((sum, d) => sum + d.volume, 0) / period;
}

// Calculate recent volume surge (last 5 bars vs previous 15)
function calculateVolumeSurge(data: IntradayDataPoint[]): number {
  if (data.length < 20) return 1;
  const recent5 = data.slice(-5).reduce((sum, d) => sum + d.volume, 0) / 5;
  const prev15 = data.slice(-20, -5).reduce((sum, d) => sum + d.volume, 0) / 15;
  return prev15 > 0 ? recent5 / prev15 : 1;
}

// Signed-volume proxy over the recent window: volume on up-closing bars minus
// volume on down-closing bars, normalized by total volume. This is a FREE
// approximation of buy vs sell aggression from price+volume alone. It is NOT
// true order-flow (Level 2 / time-and-sales) — that requires a paid real-time
// feed (a Phase B upgrade). Range: -1 (all selling) .. +1 (all buying).
function calculateBuyPressure(data: IntradayDataPoint[], period: number = 20): number {
  const recent = data.slice(-period);
  if (recent.length < 2) return 0;
  let signed = 0;
  let total = 0;
  for (let i = 1; i < recent.length; i++) {
    const bar = recent[i];
    const prev = recent[i - 1];
    const v = bar.volume || 0;
    total += v;
    // Direction of the bar: close vs its own open, falling back to prev close.
    const up = bar.close > (bar.open ?? prev.close);
    const down = bar.close < (bar.open ?? prev.close);
    if (up) signed += v;
    else if (down) signed -= v;
  }
  return total > 0 ? Math.max(-1, Math.min(1, signed / total)) : 0;
}

// ET calendar-day key for a bar timestamp, used to isolate the CURRENT trading
// session so VWAP resets each day instead of bleeding across the overnight gap.
function etDayKey(ts: number): string {
  return new Date(ts).toLocaleDateString('en-US', { timeZone: 'America/New_York' });
}

// Session VWAP: the volume-weighted average price for the CURRENT trading day
// only. VWAP is the single most-watched intraday reference line — institutions
// anchor to it all day, so whether price is above or below it is a strong,
// genuinely intraday signal. We walk backward from the latest bar and stop the
// moment the ET day changes, so only today's bars count. Returns null when the
// session has no volume yet (e.g. the very first bar).
function calculateSessionVWAP(data: IntradayDataPoint[]): number | null {
  if (data.length === 0) return null;
  const lastDay = etDayKey(data[data.length - 1].timestamp);
  let pv = 0; // sum of typical price * volume
  let vol = 0;
  for (let i = data.length - 1; i >= 0; i--) {
    if (etDayKey(data[i].timestamp) !== lastDay) break; // session boundary
    const d = data[i];
    const typical = (d.high + d.low + d.close) / 3;
    pv += typical * (d.volume || 0);
    vol += d.volume || 0;
  }
  return vol > 0 ? pv / vol : null;
}

// Main HeatTracker calculation - ENHANCED for better responsiveness
export function calculateHeatTracker(data: IntradayDataPoint[]): HeatTrackerResult {
  if (data.length < 20) {
    return {
      heat: 0,
      mode: 'NEUTRAL',
      isRedline: false,
      components: { volumeHeat: 0, momentumHeat: 0, rsiHeat: 0, priceActionHeat: 0, trendHeat: 0, macdHeat: 0, candlestickHeat: 0, vwapHeat: 0 },
      indicators: { rsi: 50, volumeRatio: 1, volumeSurge: 1, buyPressure: 0, priceChange: 0, momentum: 0, ema9: 0, ema21: 0, macd: 0, vwap: 0, vwapDistPct: 0, rsiSlope: 0, atrPct: 0, vwapReclaim: 0, rsiShort: 50 },
      keyDrivers: ['Insufficient data'],
      candlestickPatterns: [],
      timestamp: Date.now(),
    };
  }
  
  const prices = data.map(d => d.close);
  const currentPrice = prices[prices.length - 1];
  const currentVolume = data[data.length - 1].volume;
  const avgVolume = calculateAvgVolume(data);
  const keyDrivers: string[] = [];
  
  // Calculate indicators
  const rsi = calculateRSI(prices);
  const rsiShort = calculateRSI(prices, 5);
  const momentum5 = calculateMomentum(prices, 5);
  const momentum10 = calculateMomentum(prices, 10);
  const ema9 = calculateEMA(prices, 9);
  const ema21 = calculateEMA(prices, 21);
  const { macd, histogram } = calculateMACD(prices);
  const volumeRatio = avgVolume > 0 ? currentVolume / avgVolume : 1;
  const volumeSurge = calculateVolumeSurge(data);
  
  // 1. Volume Heat (-20 to +20) - Enhanced sensitivity
  // Higher weight for volume surges
  let volumeHeat = 0;
  if (volumeSurge > 2) {
    volumeHeat = 20; // Major volume surge
    keyDrivers.push(`🔥 Volume surge ${volumeSurge.toFixed(1)}x`);
  } else if (volumeRatio > 1.5) {
    volumeHeat = Math.min(20, (volumeRatio - 1) * 20);
    keyDrivers.push(`📊 High volume ${volumeRatio.toFixed(1)}x avg`);
  } else if (volumeRatio < 0.5) {
    volumeHeat = -10; // Low volume = caution
  } else {
    volumeHeat = (volumeRatio - 1) * 15;
  }
  
  // 2. RSI Heat (-25 to +25) - More responsive
  let rsiHeat = 0;
  if (rsi >= 80) {
    rsiHeat = -25; // Extreme overbought
    keyDrivers.push(`⚠️ RSI overbought (${rsi.toFixed(0)})`);
  } else if (rsi >= 70) {
    rsiHeat = -((rsi - 70) / 10) * 20;
    keyDrivers.push(`📉 RSI high (${rsi.toFixed(0)})`);
  } else if (rsi <= 20) {
    rsiHeat = 25; // Extreme oversold
    keyDrivers.push(`🎯 RSI oversold (${rsi.toFixed(0)})`);
  } else if (rsi <= 30) {
    rsiHeat = ((30 - rsi) / 10) * 20;
    keyDrivers.push(`📈 RSI low (${rsi.toFixed(0)})`);
  } else if (rsi < 45) {
    rsiHeat = (45 - rsi) / 15 * 10; // Mild bullish
  } else if (rsi > 55) {
    rsiHeat = (55 - rsi) / 15 * 10; // Mild bearish
  }
  
  // 3. Momentum Heat (-20 to +20) - Combined short & medium term
  const avgMomentum = (momentum5 * 0.6 + momentum10 * 0.4);
  let momentumHeat = Math.min(20, Math.max(-20, avgMomentum * 8));
  if (Math.abs(avgMomentum) > 1.5) {
    keyDrivers.push(avgMomentum > 0 ? `🚀 Strong upward momentum` : `📉 Strong downward momentum`);
  }
  
  // 4. Price Action Heat (-15 to +15) - Position in range
  const recentHigh = Math.max(...data.slice(-20).map(d => d.high));
  const recentLow = Math.min(...data.slice(-20).map(d => d.low));
  const range = recentHigh - recentLow;
  const pricePosition = range > 0 ? (currentPrice - recentLow) / range : 0.5;
  
  let priceActionHeat = 0;
  if (pricePosition <= 0.2) {
    priceActionHeat = 15; // Near support
    keyDrivers.push(`💎 Near support level`);
  } else if (pricePosition >= 0.8) {
    priceActionHeat = -15; // Near resistance
    keyDrivers.push(`🔻 Near resistance level`);
  } else {
    priceActionHeat = (0.5 - pricePosition) * 20;
  }
  
  // 5. Trend Heat (-15 to +15) - EMA crossover/trend direction
  let trendHeat = 0;
  const emaDiff = ((ema9 - ema21) / ema21) * 100;
  if (ema9 > ema21) {
    trendHeat = Math.min(15, emaDiff * 5);
    if (emaDiff > 0.5) keyDrivers.push(`📈 Bullish trend (EMA9 > EMA21)`);
  } else {
    trendHeat = Math.max(-15, emaDiff * 5);
    if (emaDiff < -0.5) keyDrivers.push(`📉 Bearish trend (EMA9 < EMA21)`);
  }
  
  // 6. MACD Heat (-10 to +10)
  let macdHeat = 0;
  const macdPct = currentPrice > 0 ? (macd / currentPrice) * 100 : 0;
  macdHeat = Math.min(10, Math.max(-10, macdPct * 20));
  if (macdPct > 0.3) {
    keyDrivers.push(`✅ Bullish MACD`);
  } else if (macdPct < -0.3) {
    keyDrivers.push(`❌ Bearish MACD`);
  }
  
  // 7. Candlestick Pattern Heat (-15 to +15)
  const candlestickPatterns = detectCandlestickPatterns(data);
  const candlestickResult = candlestickHeatContribution(candlestickPatterns);
  const candlestickHeat = candlestickResult.heat;
  keyDrivers.push(...candlestickResult.drivers);
  
  // 8. VWAP Heat (-12 to +12) - position vs the session volume-weighted avg price.
  // Above VWAP = bullish control, below = bearish control. This is a true
  // intraday reference (resets each session) rather than a multi-day lookback.
  const vwap = calculateSessionVWAP(data);
  let vwapHeat = 0;
  let vwapDistPct = 0;
  if (vwap && vwap > 0) {
    vwapDistPct = ((currentPrice - vwap) / vwap) * 100;
    // ~1% away from VWAP saturates the contribution at ±12.
    vwapHeat = Math.max(-12, Math.min(12, vwapDistPct * 12));
    if (vwapDistPct > 0.1) keyDrivers.push(`🟢 Above VWAP (+${vwapDistPct.toFixed(2)}%)`);
    else if (vwapDistPct < -0.1) keyDrivers.push(`🔴 Below VWAP (${vwapDistPct.toFixed(2)}%)`);
  }

  // ---- Entry-quality factors (available at entry time, no lookahead) ----
  // RSI slope: is oversold momentum still falling, or turning back up? A rising
  // RSI off a low is the classic "the knife has landed" stabilization signal.
  const rsiPrev = calculateRSI(prices.slice(0, Math.max(2, prices.length - 3)));
  const rsiSlope = rsi - rsiPrev;
  // ATR(14) as % of price — how violent the recent swings are.
  let atrPct = 0;
  {
    const per = Math.min(14, data.length - 1);
    let s = 0;
    for (let i = data.length - per; i < data.length; i++) {
      const tr = Math.max(
        data[i].high - data[i].low,
        Math.abs(data[i].high - data[i - 1].close),
        Math.abs(data[i].low - data[i - 1].close),
      );
      s += tr;
    }
    const atr = s / per;
    atrPct = currentPrice > 0 ? (atr / currentPrice) * 100 : 0;
  }
  // VWAP reclaim: did price cross back across VWAP in the last ~15 min? A long
  // that has just reclaimed VWAP is far safer than one still knifing below it.
  let vwapReclaim = 0;
  if (data.length > 6) {
    const past = data.slice(0, data.length - 3);
    const vwPast = calculateSessionVWAP(past);
    const pricePast = past[past.length - 1].close;
    const distPast = vwPast && vwPast > 0 ? ((pricePast - vwPast) / vwPast) * 100 : 0;
    if (vwapDistPct > 0 && distPast <= 0) vwapReclaim = 1;
    else if (vwapDistPct < 0 && distPast >= 0) vwapReclaim = -1;
  }

  // Combine all components with weights
  // Max possible: 20 + 25 + 20 + 15 + 15 + 10 + 15 + 12 = 132, clamped to 100
  const rawHeat = volumeHeat + rsiHeat + momentumHeat + priceActionHeat + trendHeat + macdHeat + candlestickHeat + vwapHeat;
  
  // Apply a slight amplifier to make signals more pronounced when multiple indicators align
  const alignmentBonus = (
    (volumeHeat > 5 && momentumHeat > 5 ? 5 : 0) +
    (rsiHeat > 10 && priceActionHeat > 5 ? 5 : 0) +
    (volumeHeat < -5 && momentumHeat < -5 ? -5 : 0) +
    (rsiHeat < -10 && priceActionHeat < -5 ? -5 : 0) +
    (candlestickHeat > 5 && trendHeat > 3 ? 3 : 0) +
    (candlestickHeat < -5 && trendHeat < -3 ? -3 : 0)
  );
  
  const heat = Math.min(100, Math.max(-100, rawHeat + alignmentBonus));
  
  // Determine mode and redline status
  const mode: 'BUY' | 'SELL' | 'NEUTRAL' = heat > 20 ? 'BUY' : heat < -20 ? 'SELL' : 'NEUTRAL';
  const isRedline = Math.abs(heat) >= 70;
  
  // Price change for display
  const previousPrice = prices.length > 1 ? prices[prices.length - 2] : currentPrice;
  const priceChange = previousPrice > 0 ? ((currentPrice - previousPrice) / previousPrice) * 100 : 0;
  
  // Ensure we have at least one key driver
  if (keyDrivers.length === 0) {
    if (heat > 20) keyDrivers.push('📊 Multiple mild bullish signals');
    else if (heat < -20) keyDrivers.push('📊 Multiple mild bearish signals');
    else keyDrivers.push('⏳ Neutral - waiting for clearer signal');
  }
  
  return {
    heat: Math.round(heat),
    mode,
    isRedline,
    components: {
      volumeHeat: Math.round(volumeHeat * 10) / 10,
      momentumHeat: Math.round(momentumHeat * 10) / 10,
      rsiHeat: Math.round(rsiHeat * 10) / 10,
      priceActionHeat: Math.round(priceActionHeat * 10) / 10,
      trendHeat: Math.round(trendHeat * 10) / 10,
      macdHeat: Math.round(macdHeat * 10) / 10,
      candlestickHeat: Math.round(candlestickHeat * 10) / 10,
      vwapHeat: Math.round(vwapHeat * 10) / 10,
    },
    indicators: {
      rsi: Math.round(rsi * 10) / 10,
      volumeRatio: Math.round(volumeRatio * 100) / 100,
      volumeSurge: Math.round(volumeSurge * 100) / 100,
      buyPressure: Math.round(calculateBuyPressure(data) * 1000) / 1000,
      priceChange: Math.round(priceChange * 100) / 100,
      momentum: Math.round(avgMomentum * 100) / 100,
      ema9: Math.round(ema9 * 100) / 100,
      ema21: Math.round(ema21 * 100) / 100,
      macd: Math.round(macd * 1000) / 1000,
      vwap: vwap ? Math.round(vwap * 100) / 100 : 0,
      vwapDistPct: Math.round(vwapDistPct * 1000) / 1000,
      rsiSlope: Math.round(rsiSlope * 10) / 10,
      atrPct: Math.round(atrPct * 1000) / 1000,
      vwapReclaim,
      rsiShort: Math.round(rsiShort * 10) / 10,
    },
    keyDrivers,
    candlestickPatterns,
    timestamp: Date.now(),
  };
}

```

---

