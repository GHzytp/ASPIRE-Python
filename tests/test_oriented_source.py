import logging

import numpy as np
import pytest

from aspire.abinitio import CLSymmetryC3C4, CLSyncVoting
from aspire.source import OrientedSource, Simulation
from aspire.volume import CnSymmetricVolume, CyclicSymmetryGroup

logger = logging.getLogger(__name__)


@pytest.fixture
def sim_fixture():
    L = 8
    n = 10
    sim = Simulation(L=L, n=n, C=1)
    vol_C4 = CnSymmetricVolume(L=L, order=4, C=1)
    sim_C4 = Simulation(L=L, n=n, vols=vol_C4.generate(), offsets=0)
    return sim, sim_C4


@pytest.fixture
def oriented_src_fixture(sim_fixture):
    # Original sources
    sim, sim_C4 = sim_fixture

    # Orientation estimators
    estimator = CLSyncVoting(sim)
    estimator_C4 = CLSymmetryC3C4(sim_C4, symmetry="C4", n_theta=72)

    # `OrientedSource`s
    src = OrientedSource(sim, orientation_estimator=estimator)
    src_C4 = OrientedSource(sim_C4, orientation_estimator=estimator_C4)
    src_from_rots = OrientedSource(
        sim,
        rotations=sim.rotations,
        symmetry_group=CyclicSymmetryGroup(order=1, dtype=sim.dtype),
    )
    return src, src_C4, src_from_rots


def test_repr(oriented_src_fixture, sim_fixture):
    sim, _ = sim_fixture
    src, _, _ = oriented_src_fixture

    # Check that original source is mentioned in repr
    logger.debug(f"repr(OrientedSrc): {repr(src)}")
    assert type(sim).__name__ in repr(src)


def test_images(oriented_src_fixture, sim_fixture):
    src, src_C4, src_from_rots = oriented_src_fixture
    sim, sim_C4 = sim_fixture
    assert np.allclose(src.images[:], sim.images[:])
    assert np.allclose(src_C4.images[:], sim_C4.images[:])
    assert np.allclose(src_from_rots.images[:], sim.images[:])


def test_rotations(oriented_src_fixture):
    src, src_C4, src_from_rots = oriented_src_fixture
    # Smoke test for rotations
    _ = src.rotations
    _ = src_C4.rotations
    _ = src_from_rots.rotations


def test_angles(oriented_src_fixture):
    src, src_C4, src_from_rots = oriented_src_fixture
    # Smoke test for angles
    _ = src.angles
    _ = src_C4.angles
    _ = src_from_rots.angles


def test_symmetry_group(oriented_src_fixture):
    src, src_C4, src_from_rots = oriented_src_fixture
    assert str(src.symmetry_group) == "C1"
    assert str(src_C4.symmetry_group) == "C4"
    assert str(src_from_rots.symmetry_group) == "C1"