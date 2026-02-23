# mypy: disable-error-code="method-assign"
"""Tests for lifecycle RPCs: setup, stop, property queries."""


from .conftest import StarServiceFixture


class TestLifecycleRPCs:
  def test_num_channels(self, star_service: StarServiceFixture):
    assert star_service.remote.num_channels == 8

  def test_core96_head_installed(self, star_service: StarServiceFixture):
    assert star_service.remote.core96_head_installed is True

  def test_iswap_installed(self, star_service: StarServiceFixture):
    assert star_service.remote.iswap_installed is True

  def test_iswap_parked(self, star_service: StarServiceFixture):
    assert star_service.remote.iswap_parked is True

  def test_core_parked(self, star_service: StarServiceFixture):
    assert star_service.remote.core_parked is True
