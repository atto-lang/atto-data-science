"""Immutable host-only online mean/variance reference for Atto data science."""
from dataclasses import dataclass
import math

MAX_SAMPLES = (1 << 32) - 1


class MomentsError(ValueError):
    pass


@dataclass(frozen=True)
class Moments:
    count: int = 0
    mean: float = 0.0
    m2: float = 0.0

    def add(self, value):
        if type(value) not in (int, float) or not math.isfinite(value):
            raise MomentsError("sample must be a finite number, not a boolean")
        if self.count >= MAX_SAMPLES:
            raise MomentsError("sample budget exceeded")
        n = self.count + 1
        delta = value - self.mean
        mean = self.mean + delta / n
        m2 = self.m2 + delta * (value - mean)
        if not math.isfinite(mean) or not math.isfinite(m2):
            raise MomentsError("numeric overflow in online variance")
        return Moments(n, mean, m2)

    def merge(self, other):
        if type(other) is not Moments:
            raise MomentsError("can merge only Moments summaries")
        if not other.count:
            return self
        if not self.count:
            return other
        n = self.count + other.count
        if n > MAX_SAMPLES:
            raise MomentsError("sample budget exceeded")
        delta = other.mean - self.mean
        mean = self.mean + delta * other.count / n
        m2 = (self.m2 + other.m2 +
              delta * delta * self.count * other.count / n)
        if not math.isfinite(mean) or not math.isfinite(m2):
            raise MomentsError("numeric overflow in merged variance")
        return Moments(n, mean, m2)

    def population_variance(self):
        if self.count == 0:
            raise MomentsError("variance requires at least one sample")
        return max(0.0, self.m2 / self.count)

    def sample_variance(self):
        if self.count < 2:
            raise MomentsError("sample variance requires at least two samples")
        return max(0.0, self.m2 / (self.count - 1))
