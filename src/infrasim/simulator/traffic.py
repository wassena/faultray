"""Traffic pattern models for dynamic simulation.

Defines time-varying traffic patterns (DDoS, flash crowds, diurnal cycles, etc.)
that can be applied during scenario execution to model realistic load conditions.
"""

from __future__ import annotations

import math
import random
from enum import Enum

from pydantic import BaseModel, Field


class TrafficPatternType(str, Enum):
    """Types of traffic patterns that can be simulated."""

    CONSTANT = "constant"
    RAMP = "ramp"
    SPIKE = "spike"
    WAVE = "wave"
    DDoS_VOLUMETRIC = "ddos_volumetric"
    DDoS_SLOWLORIS = "ddos_slowloris"
    FLASH_CROWD = "flash_crowd"
    DIURNAL = "diurnal"


# Seeded RNG for reproducible jitter in DDoS patterns.
_rng = random.Random(42)


class TrafficPattern(BaseModel):
    """A time-varying traffic pattern applied during simulation.

    The ``multiplier_at`` method returns the traffic multiplier at any given
    second within the pattern's duration.  A multiplier of 1.0 represents
    normal (baseline) traffic; higher values represent proportional increases.
    """

    pattern_type: TrafficPatternType
    peak_multiplier: float = Field(
        description="Maximum traffic multiplier relative to baseline (1.0).",
    )
    duration_seconds: int = Field(
        default=300,
        description="Total duration of the traffic pattern in seconds.",
    )
    ramp_seconds: int = Field(
        default=0,
        description="Time in seconds to ramp from baseline to peak.",
    )
    sustain_seconds: int = Field(
        default=0,
        description="Time in seconds to sustain peak traffic after ramping up.",
    )
    cooldown_seconds: int = Field(
        default=0,
        description="Time in seconds to ramp back down from peak to baseline.",
    )
    wave_period_seconds: int = Field(
        default=60,
        description="Period of one full oscillation for WAVE patterns.",
    )
    burst_interval_seconds: int = Field(
        default=10,
        description="Interval between bursts for DDoS patterns.",
    )
    affected_components: list[str] = Field(
        default_factory=list,
        description="Component IDs affected by this pattern.  Empty means all.",
    )
    description: str = Field(
        default="",
        description="Human-readable description of the traffic pattern.",
    )

    def multiplier_at(self, t: int) -> float:
        """Return the traffic multiplier at time *t* (seconds from start).

        The returned value is always >= 1.0.  If *t* falls outside
        ``[0, duration_seconds)``, the baseline multiplier 1.0 is returned.
        """
        if t < 0 or t >= self.duration_seconds:
            return 1.0

        pt = self.pattern_type

        if pt == TrafficPatternType.CONSTANT:
            return self._constant()

        if pt == TrafficPatternType.RAMP:
            return self._ramp(t)

        if pt == TrafficPatternType.SPIKE:
            return self._spike(t)

        if pt == TrafficPatternType.WAVE:
            return self._wave(t)

        if pt == TrafficPatternType.DDoS_VOLUMETRIC:
            return self._ddos_volumetric(t)

        if pt == TrafficPatternType.DDoS_SLOWLORIS:
            return self._ddos_slowloris(t)

        if pt == TrafficPatternType.FLASH_CROWD:
            return self._flash_crowd(t)

        if pt == TrafficPatternType.DIURNAL:
            return self._diurnal(t)

        return 1.0

    # ------------------------------------------------------------------
    # Private helpers for each pattern type
    # ------------------------------------------------------------------

    def _constant(self) -> float:
        """CONSTANT: always return *peak_multiplier*."""
        return self.peak_multiplier

    def _ramp(self, t: int) -> float:
        """RAMP: linear up over *ramp_seconds*, sustain, then linear down.

        Timeline: [0, ramp) -> linear 1.0 to peak
                  [ramp, ramp+sustain) -> peak
                  [ramp+sustain, ramp+sustain+cooldown) -> linear peak to 1.0
                  beyond -> 1.0
        """
        ramp = self.ramp_seconds
        sustain = self.sustain_seconds
        cooldown = self.cooldown_seconds
        peak = self.peak_multiplier

        if ramp > 0 and t < ramp:
            # Linear ramp up from 1.0 to peak.
            return 1.0 + (peak - 1.0) * (t / ramp)

        t_after_ramp = t - ramp
        if t_after_ramp < sustain:
            return peak

        t_after_sustain = t_after_ramp - sustain
        if cooldown > 0 and t_after_sustain < cooldown:
            # Linear ramp down from peak to 1.0.
            return peak - (peak - 1.0) * (t_after_sustain / cooldown)

        return 1.0

    def _spike(self, t: int) -> float:
        """SPIKE: instant jump to peak at *ramp_seconds*, sustain, instant drop.

        Timeline: [0, ramp) -> 1.0 (baseline)
                  [ramp, ramp+sustain) -> peak
                  beyond -> 1.0
        """
        ramp = self.ramp_seconds
        sustain = self.sustain_seconds

        if ramp <= t < ramp + sustain:
            return self.peak_multiplier
        return 1.0

    def _wave(self, t: int) -> float:
        """WAVE: sinusoidal oscillation between 1.0 and *peak_multiplier*.

        Uses a sine wave shifted so that the output oscillates between
        1.0 (trough) and peak_multiplier (crest).
        """
        period = self.wave_period_seconds
        if period <= 0:
            return self.peak_multiplier

        amplitude = (self.peak_multiplier - 1.0) / 2.0
        midpoint = 1.0 + amplitude
        return midpoint + amplitude * math.sin(2.0 * math.pi * t / period)

    def _ddos_volumetric(self, t: int) -> float:
        """DDoS_VOLUMETRIC: fast ramp to peak in 10 s, then sustain with jitter.

        The ramp phase lasts a fixed 10 seconds (linear).  After that the
        multiplier holds at *peak_multiplier* with random +/-20 % jitter
        (seeded RNG for reproducibility).
        """
        peak = self.peak_multiplier
        ramp_duration = 10  # fixed 10-second ramp

        if t < ramp_duration:
            return 1.0 + (peak - 1.0) * (t / ramp_duration)

        # Sustain at peak with +/-20 % jitter.
        jitter = _rng.uniform(-0.20, 0.20)
        return max(1.0, peak * (1.0 + jitter))

    def _ddos_slowloris(self, t: int) -> float:
        """DDoS_SLOWLORIS: steady linear ramp over full duration.

        Connections increase slowly (not RPS bursts).  The multiplier
        increases linearly from 1.0 at t=0 to *peak_multiplier* at t=duration.
        """
        duration = self.duration_seconds
        if duration <= 0:
            return self.peak_multiplier
        return 1.0 + (self.peak_multiplier - 1.0) * (t / duration)

    def _flash_crowd(self, t: int) -> float:
        """FLASH_CROWD: exponential ramp up, then slow linear decay.

        Phase 1 (ramp): exponential curve from 1.0 to peak over *ramp_seconds*.
        Phase 2 (decay): linear decay from peak back to 1.0 over the remaining
        duration.
        """
        ramp = self.ramp_seconds
        peak = self.peak_multiplier

        if ramp > 0 and t < ramp:
            # Exponential ramp: 1.0 * e^(k*t) where k = ln(peak) / ramp
            # so that at t=ramp the value equals peak.
            k = math.log(peak) / ramp
            return math.exp(k * t)

        # Linear decay from peak to 1.0 over remaining duration.
        decay_duration = self.duration_seconds - ramp
        if decay_duration <= 0:
            return peak

        t_decay = t - ramp
        return peak - (peak - 1.0) * (t_decay / decay_duration)

    def _diurnal(self, t: int) -> float:
        """DIURNAL: 24 h sine wave compressed into *duration_seconds*.

        The curve is minimum (1.0) at the start and end of the window, and
        reaches *peak_multiplier* at the midpoint -- mimicking a natural
        day/night traffic cycle.
        """
        duration = self.duration_seconds
        if duration <= 0:
            return self.peak_multiplier

        # sin curve: 0 at t=0, peaks at t=duration/2, back to 0 at t=duration.
        amplitude = (self.peak_multiplier - 1.0) / 2.0
        midpoint = 1.0 + amplitude
        return midpoint - amplitude * math.cos(2.0 * math.pi * t / duration)


# =====================================================================
# Factory functions
# =====================================================================


def create_ddos_volumetric(
    peak: float = 10.0,
    duration: int = 300,
) -> TrafficPattern:
    """Create a volumetric DDoS traffic pattern.

    Ramps to *peak* in 10 seconds, then sustains with random +/-20 % jitter.
    """
    return TrafficPattern(
        pattern_type=TrafficPatternType.DDoS_VOLUMETRIC,
        peak_multiplier=peak,
        duration_seconds=duration,
        description=f"Volumetric DDoS: {peak}x peak, {duration}s duration",
    )


def create_ddos_slowloris(
    peak: float = 5.0,
    duration: int = 300,
) -> TrafficPattern:
    """Create a Slowloris-style DDoS traffic pattern.

    Connections increase linearly from baseline to *peak* over the full
    *duration*, modelling a slow resource-exhaustion attack.
    """
    return TrafficPattern(
        pattern_type=TrafficPatternType.DDoS_SLOWLORIS,
        peak_multiplier=peak,
        duration_seconds=duration,
        description=f"Slowloris DDoS: {peak}x peak, linear ramp over {duration}s",
    )


def create_flash_crowd(
    peak: float = 8.0,
    ramp: int = 30,
    duration: int = 300,
) -> TrafficPattern:
    """Create a flash-crowd traffic pattern.

    Exponential ramp to *peak* over *ramp* seconds, then slow linear decay
    over the remaining duration.
    """
    return TrafficPattern(
        pattern_type=TrafficPatternType.FLASH_CROWD,
        peak_multiplier=peak,
        duration_seconds=duration,
        ramp_seconds=ramp,
        description=f"Flash crowd: {peak}x peak, {ramp}s exponential ramp, {duration}s total",
    )


def create_viral_event(
    peak: float = 15.0,
    duration: int = 300,
) -> TrafficPattern:
    """Create a viral-event traffic pattern.

    Uses a RAMP profile with 60 s ramp-up, 120 s sustain, and 120 s cooldown,
    modelling a sudden surge of interest (e.g. trending social-media post).
    """
    return TrafficPattern(
        pattern_type=TrafficPatternType.RAMP,
        peak_multiplier=peak,
        duration_seconds=duration,
        ramp_seconds=60,
        sustain_seconds=120,
        cooldown_seconds=120,
        description=f"Viral event: {peak}x peak, 60s ramp / 120s sustain / 120s cooldown",
    )


def create_diurnal(
    peak: float = 3.0,
    duration: int = 300,
) -> TrafficPattern:
    """Create a diurnal (day/night) traffic pattern.

    A 24-hour sine wave compressed into *duration* seconds.  Minimum at the
    start and end, peak at the midpoint.
    """
    return TrafficPattern(
        pattern_type=TrafficPatternType.DIURNAL,
        peak_multiplier=peak,
        duration_seconds=duration,
        description=f"Diurnal cycle: {peak}x peak, compressed into {duration}s",
    )
