import itertools
import logging

import numpy as np
import pytest

from aspire.utils import Rotation
from aspire.volume import (
    CyclicSymmetryGroup,
    DihedralSymmetryGroup,
    OctahedralSymmetryGroup,
    TetrahedralSymmetryGroup,
)

logger = logging.getLogger(__name__)

GROUPS_WITH_ORDER = [
    CyclicSymmetryGroup,
    DihedralSymmetryGroup,
]
GROUPS_WITHOUT_ORDER = [
    TetrahedralSymmetryGroup,
    OctahedralSymmetryGroup,
]
ORDERS = [2, 3, 4, 5]
DTYPES = [np.float32, np.float64]
PARAMS_ORDER = list(itertools.product(GROUPS_WITH_ORDER, DTYPES, ORDERS))
PARAMS = list(itertools.product(GROUPS_WITHOUT_ORDER, DTYPES))
# @pytest.fixture(params=DTYPES)
# def dtype_fixture(request):
#     dtype = request.param
#     return dtype


def group_fixture_id(params):
    group_class = params[0]
    dtype = params[1]
    if len(params) > 2:
        order = params[2]
        return f"{group_class.__name__}, order={order}, dtype={dtype}"
    else:
        return f"{group_class.__name__}, dtype={dtype}"


# Create SymmetryGroup fixture for the set of parameters.
@pytest.fixture(params=PARAMS + PARAMS_ORDER, ids=group_fixture_id)
def group_fixture(request):
    params = request.param
    group_class = params[0]
    dtype = params[1]
    group_kwargs = dict(
        dtype=dtype,
    )
    if len(params) > 2:
        group_kwargs["order"] = params[2]

    return group_class(**group_kwargs)


def test_group_repr(group_fixture):
    """Test SymmetryGroup repr"""
    assert repr(group_fixture).startswith(f"{group_fixture.__class__.__name__}")
    logger.debug(f"SymmetryGroup object: {repr(group_fixture)}")


def test_group_str(group_fixture):
    """Test SymmetryGroup str"""
    _ = str(group_fixture)


def test_group_rotations(group_fixture):
    rotations = group_fixture.rotations
    assert isinstance(rotations, Rotation)