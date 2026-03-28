"""Tests for era definitions and piecewise logarithmic timeline controller.

Covers PHYS-03: logarithmic timeline mapping across 60+ orders of magnitude.
"""
import math
import pytest

from bigbangsim.simulation.eras import (
    ERAS,
    EraDefinition,
    get_era_by_cosmic_time,
    total_screen_time,
    era_screen_start,
)
from bigbangsim.simulation.timeline import TimelineController


# ---- Era definition tests ----

class TestEraDefinitions:
    """Tests for the ERAS list and EraDefinition dataclass."""

    def test_exactly_11_eras(self):
        """There must be exactly 11 cosmological eras."""
        assert len(ERAS) == 11

    def test_era_indices_sequential(self):
        """Era indices must be 0 through 10 in order."""
        for i, era in enumerate(ERAS):
            assert era.index == i

    def test_cosmic_start_times_monotonically_increasing(self):
        """Era cosmic_start times are monotonically increasing across indices."""
        for i in range(len(ERAS) - 1):
            assert ERAS[i].cosmic_start <= ERAS[i + 1].cosmic_start, (
                f"Era {i} start ({ERAS[i].cosmic_start}) > Era {i+1} start ({ERAS[i+1].cosmic_start})"
            )

    def test_first_era_is_planck(self):
        """First era should be Planck Epoch."""
        assert ERAS[0].name == "Planck Epoch"
        assert ERAS[0].cosmic_start <= 1e-43

    def test_last_era_is_large_scale_structure(self):
        """Last era should be Large-Scale Structure."""
        assert ERAS[10].name == "Large-Scale Structure"

    def test_each_era_has_minimum_screen_time(self):
        """Each era must get at least 10 seconds of screen time."""
        for era in ERAS:
            assert era.screen_seconds >= 10.0, (
                f"Era '{era.name}' has only {era.screen_seconds}s screen time"
            )

    def test_total_screen_time_in_range(self):
        """Total screen time across all eras should be between 120 and 200 seconds."""
        total = total_screen_time()
        assert 120.0 <= total <= 200.0, f"Total screen time {total}s out of range"

    def test_era_screen_start_cumulative(self):
        """era_screen_start should return correct cumulative offsets."""
        assert era_screen_start(0) == 0.0
        assert era_screen_start(1) == ERAS[0].screen_seconds
        cumulative = 0.0
        for i, era in enumerate(ERAS):
            assert abs(era_screen_start(i) - cumulative) < 1e-9
            cumulative += era.screen_seconds

    def test_each_era_has_description(self):
        """Each era should have a non-empty description string."""
        for era in ERAS:
            assert isinstance(era.description, str)
            assert len(era.description) > 0

    def test_get_era_by_cosmic_time_planck(self):
        """Very early cosmic time (1e-40 s) should be in Planck Epoch."""
        era = get_era_by_cosmic_time(1e-40)
        assert era.index == 0
        assert era.name == "Planck Epoch"

    def test_get_era_by_cosmic_time_nucleosynthesis(self):
        """Cosmic time 100s should be in Nucleosynthesis era."""
        era = get_era_by_cosmic_time(100.0)
        assert era.index == 5
        assert era.name == "Nucleosynthesis"

    def test_get_era_by_cosmic_time_galaxy_formation(self):
        """Cosmic time ~1e16 s should be in Galaxy Formation era."""
        era = get_era_by_cosmic_time(2e16)
        assert era.index == 9
        assert era.name == "Galaxy Formation"


# ---- Timeline controller tests ----

class TestTimelineController:
    """Tests for the piecewise logarithmic timeline mapping."""

    @pytest.fixture
    def timeline(self):
        return TimelineController(ERAS)

    def test_screen_to_cosmic_start(self, timeline):
        """screen_to_cosmic(0.0) returns approximately Planck time (~1e-43)."""
        cosmic = timeline.screen_to_cosmic(0.0)
        # Should be close to 1e-43 (Planck time is the start of Era 0)
        assert cosmic < 1e-40, f"Start cosmic time {cosmic} too large"
        assert cosmic > 1e-50, f"Start cosmic time {cosmic} too small"

    def test_screen_to_cosmic_end(self, timeline):
        """screen_to_cosmic(total) returns approximately age of universe (~4.35e17)."""
        total = timeline.total_duration()
        cosmic = timeline.screen_to_cosmic(total)
        age_universe = 4.35e17
        # Within 5% of age of universe
        assert abs(cosmic - age_universe) / age_universe < 0.05, (
            f"End cosmic time {cosmic} not close to age of universe {age_universe}"
        )

    def test_screen_to_cosmic_era_boundary(self, timeline):
        """screen_to_cosmic at era boundary returns the correct cosmic time."""
        # At the boundary between era 0 and era 1, cosmic time should be era 1's start
        boundary_screen = era_screen_start(1)
        cosmic = timeline.screen_to_cosmic(boundary_screen)
        expected = ERAS[1].cosmic_start  # 1e-36
        # Check within an order of magnitude (log scale)
        log_ratio = abs(math.log10(cosmic) - math.log10(expected))
        assert log_ratio < 1.0, (
            f"Era boundary cosmic time {cosmic} too far from expected {expected}"
        )

    def test_round_trip_consistency(self, timeline):
        """cosmic_to_screen(screen_to_cosmic(t)) is approximately t."""
        total = timeline.total_duration()
        test_points = [0.0, 5.0, 20.0, 50.0, 80.0, total - 1.0, total]
        for t in test_points:
            cosmic = timeline.screen_to_cosmic(t)
            screen_back = timeline.cosmic_to_screen(cosmic)
            # 1% relative error tolerance (or small absolute for near-zero)
            if t > 0.1:
                rel_err = abs(screen_back - t) / t
                assert rel_err < 0.01, (
                    f"Round-trip failed at t={t}: got {screen_back}, rel_err={rel_err}"
                )
            else:
                assert abs(screen_back - t) < 0.1

    def test_get_current_era_start(self, timeline):
        """Era progress at the very start of an era should be close to 0.0."""
        cosmic_start = ERAS[5].cosmic_start  # Nucleosynthesis start = 1.0 s
        era_idx, progress = timeline.get_current_era(cosmic_start * 1.001)
        assert era_idx == 5
        assert progress < 0.05, f"Era progress at start = {progress}"

    def test_get_current_era_end(self, timeline):
        """Era progress near the end of an era should be close to 1.0."""
        cosmic_end = ERAS[5].cosmic_end  # Nucleosynthesis end = 1200.0 s
        era_idx, progress = timeline.get_current_era(cosmic_end * 0.999)
        assert era_idx == 5
        assert progress > 0.95, f"Era progress near end = {progress}"

    def test_total_duration(self, timeline):
        """Total duration should equal sum of all era screen_seconds."""
        assert abs(timeline.total_duration() - total_screen_time()) < 1e-9

    def test_screen_to_cosmic_monotonically_increasing(self, timeline):
        """screen_to_cosmic must be monotonically increasing."""
        total = timeline.total_duration()
        prev = 0.0
        for i in range(1, 100):
            t = total * i / 100.0
            cosmic = timeline.screen_to_cosmic(t)
            assert cosmic > prev, (
                f"Not monotonic at screen_time={t}: {cosmic} <= {prev}"
            )
            prev = cosmic

    def test_cosmic_to_screen_monotonically_increasing(self, timeline):
        """cosmic_to_screen must be monotonically increasing."""
        test_times = [1e-43, 1e-36, 1e-30, 1e-20, 1e-10, 1.0, 1e5, 1e10, 1e15, 4e17]
        prev = -1.0
        for ct in test_times:
            screen = timeline.cosmic_to_screen(ct)
            assert screen > prev, (
                f"Not monotonic at cosmic_time={ct}: {screen} <= {prev}"
            )
            prev = screen
