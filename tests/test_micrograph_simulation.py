import itertools
import logging

import numpy as np
import pytest

from aspire.noise import WhiteNoiseAdder
from aspire.source import MicrographSimulation, Simulation

logger = logging.getLogger(__name__)
IMG_SIZES = [12, 13]
DTYPES = [np.float32, np.float64]
PARTICLES_PER_MICROGRAPHS = [7, 10]
MICROGRAPH_COUNTS = [1, 2]
MICROGRAPH_SIZES = [101, 100]
SIM_PARTICLES = [1, 2]
BOUNDARIES = [-1, 0, 20]


def vol_fixture_id(params):
    sim_particles = params[0]
    img_size = params[1]
    dtype = params[2]
    return f"number of volumes={sim_particles}, image size={img_size}, dtype={dtype.__name__}"


@pytest.fixture(
    params=itertools.product(SIM_PARTICLES, IMG_SIZES, DTYPES), ids=vol_fixture_id
)
def vol_fixture(request):
    sim_particles, img_size, dtype = request.param
    simulation = Simulation(C=sim_particles, L=img_size, dtype=dtype)
    return simulation.vols


def micrograph_fixture_id(params):
    particles_per_micrograph = params[0]
    micrograph_count = params[1]
    micrograph_size = params[2]
    boundary = params[3]
    return f"particles per micrograph={particles_per_micrograph}, micrograph count={micrograph_count}, micrograph size={micrograph_size}, boundary={boundary}"


@pytest.fixture(
    params=itertools.product(
        PARTICLES_PER_MICROGRAPHS, MICROGRAPH_COUNTS, MICROGRAPH_SIZES, BOUNDARIES
    ),
    ids=micrograph_fixture_id,
)
def micrograph_fixture(vol_fixture, request):
    """
    Construct a MicrographSimulation.
    """
    (
        particles_per_micrograph,
        micrograph_count,
        micrograph_size,
        boundary,
    ) = request.param
    return MicrographSimulation(
        volume=vol_fixture,
        interparticle_distance=0,
        particles_per_micrograph=particles_per_micrograph,
        micrograph_count=micrograph_count,
        micrograph_size=micrograph_size,
        boundary=boundary,
    )


def test_micrograph_source_has_correct_values(vol_fixture, micrograph_fixture):
    """
    Test the MicrographSimulation has the correct values from arguments.
    """
    v = vol_fixture
    m = micrograph_fixture
    assert v.resolution == m.particle_box_size
    assert v == m.simulation.vols
    assert len(m) == m.micrograph_count
    assert m.clean_images[0].shape[1] == m.micrograph_size
    assert m.clean_images[0].shape[2] == m.micrograph_size
    assert (
        repr(m)
        == f"{m.__class__.__name__} with {m.micrograph_count} {m.dtype.name} micrographs of size {m.micrograph_size}x{m.micrograph_size}"
    )
    _ = m.clean_images[:]
    _ = m.images[:]


def test_micrograph_raises_error_simulation():
    """
    Test that MicrographSimulation raises error when simulation argument is not a Simulation
    """
    with pytest.raises(Exception) as e_info:
        _ = MicrographSimulation(
            "Simulation",
            micrograph_size=100,
            particles_per_micrograph=20,
            interparticle_distance=10,
        )
    assert str(e_info.value) == "`volume` should be of type `Volume`."


def test_micrograph_raises_error_image_size(vol_fixture):
    """
    Test the MicrographSimulation class raises errors when the image size is larger than micrograph size.
    """
    with pytest.raises(ValueError) as e_info:
        v = vol_fixture
        _ = MicrographSimulation(
            v,
            micrograph_size=v.resolution - 1,
            particles_per_micrograph=10,
            interparticle_distance=0,
        )
    assert (
        str(e_info.value)
        == "The micrograph size must be larger or equal to the simulation's image size."
    )


def test_micrograph_centers_match(micrograph_fixture):
    """
    Test that the Micrograph's centers are forming at generated points.
    """
    m = micrograph_fixture
    centers = np.reshape(m.centers, (m.total_particle_count, 2))
    for i, center in enumerate(centers):
        if (
            center[0] >= 0
            and center[0] < m.micrograph_size
            and center[1] >= 0
            and center[1] < m.micrograph_size
        ):
            assert m.clean_images[i // m.particles_per_micrograph].asnumpy()[0][
                tuple(center)
            ] != np.min(m.clean_images[i // m.particles_per_micrograph].asnumpy()[0])


def test_micrograph_raises_error_when_out_of_bounds():
    """
    Test that the Micrograph raises an error when illegal boundary values are given.
    """
    for boundary_value in [-100, 1000]:
        with pytest.raises(ValueError) as e_info:
            s = Simulation(
                L=64,
                n=20 * 1,
                C=1,
                amplitudes=1,
                offsets=0,
            )
            _ = MicrographSimulation(
                s.vols,
                micrograph_size=500,
                particles_per_micrograph=20,
                micrograph_count=1,
                interparticle_distance=10,
                boundary=boundary_value,
            )
        assert str(e_info.value) == "Illegal boundary value."


def test_micrograph_raises_error_when_too_dense():
    """
    Tests that the micrograph fails when the fail limit is met.
    """
    with pytest.raises(RuntimeError, match="failures exceeded limit") as _:
        s = Simulation(
            L=64,
            n=400,
            C=1,
            amplitudes=1,
            offsets=0,
        )
        _ = MicrographSimulation(
            s.vols,
            micrograph_size=500,
            particles_per_micrograph=400,
            micrograph_count=1,
        )


def test_index_returns_correct_values():
    """
    Test index methods return expected values
    """
    s = Simulation(
        L=64,
        n=10,
        C=1,
        amplitudes=1,
        offsets=0,
    )
    m = MicrographSimulation(
        s.vols,
        micrograph_size=500,
        particles_per_micrograph=10,
        micrograph_count=1,
    )
    particle_id = 5
    assert m.get_micrograph_index(particle_id) == (0, particle_id)
    assert m.get_particle_indices(0, particle_id) == particle_id
    assert np.array_equal(
        m.get_particle_indices(0), np.arange(m.particles_per_micrograph)
    )


def test_index_functions_raise_errors():
    """
    Test errors for index method bounds
    """
    s = Simulation(
        L=64,
        n=10,
        C=1,
        amplitudes=1,
        offsets=0,
    )
    m = MicrographSimulation(
        s.vols,
        micrograph_size=500,
        particles_per_micrograph=10,
        micrograph_count=1,
    )
    with pytest.raises(RuntimeError) as e_info:
        m.get_particle_indices(1)
    assert str(e_info.value) == "Index out of bounds for micrograph."
    with pytest.raises(RuntimeError) as e_info:
        m.get_particle_indices(-1)
    assert str(e_info.value) == "Index out of bounds for micrograph."
    with pytest.raises(RuntimeError) as e_info:
        m.get_micrograph_index(11)
    assert str(e_info.value) == "Index out of bounds."
    with pytest.raises(RuntimeError) as e_info:
        m.get_micrograph_index(-1)
    assert str(e_info.value) == "Index out of bounds."
    with pytest.raises(RuntimeError) as e_info:
        m.get_particle_indices(0, 500)
    assert str(e_info.value) == "Index out of bounds for particle."
    with pytest.raises(RuntimeError) as e_info:
        m.get_particle_indices(0, -1)
    assert str(e_info.value) == "Index out of bounds for particle."


def test_default_values_work():
    """
    Tests that the default arguments work.
    """
    s = Simulation(
        L=64,
        n=100,
        C=1,
        amplitudes=1,
        offsets=0,
    )
    m = MicrographSimulation(
        s.vols,
    )
    assert m.micrograph_count == 1
    assert m.micrograph_size == 4096
    assert m.particles_per_micrograph == 100
    assert m.interparticle_distance == m.particle_box_size


def test_noise_works():
    """
    Tests that adding noise works by comparing to a micrograph with noise manually applied.
    """
    s = Simulation(
        L=20,
        n=10,
        C=1,
        amplitudes=1,
        offsets=0,
    )
    noise = WhiteNoiseAdder(1e-3)
    m = MicrographSimulation(
        s.vols,
        noise_adder=noise,
        micrograph_count=1,
        particles_per_micrograph=4,
        micrograph_size=200,
    )
    noisy_micrograph = noise.forward(m.clean_images[:], [0])
    assert np.array_equal(m.images[0], noisy_micrograph[0])