import os.path
from unittest import TestCase

import numpy as np
from scipy.spatial.transform import Rotation as R

from aspire.operators import RadialCTFFilter
from aspire.source.simulation import Simulation

DATA_DIR = os.path.join(os.path.dirname(__file__), "saved_test_data")


class MySimulation(Simulation):
    # A subclassed ImageSource object that specifies a metadata alias
    metadata_aliases = {"greeting": "my_greeting"}


class SimTestCase(TestCase):
    def setUp(self):
        self.sim = MySimulation(
            n=1024,
            L=8,
            unique_filters=[
                RadialCTFFilter(defocus=d) for d in np.linspace(1.5e4, 2.5e4, 7)
            ],
        )

    def tearDown(self):
        pass

    def testMetadata1(self):
        # A new metadata column 'greeting' added to all images in the simulation, with the value 'hello'
        self.sim.set_metadata("greeting", "hello")
        # Get value of a metadata field for all images
        values = self.sim.get_metadata("greeting")
        # We get back 'hello' 1024 times
        self.assertTrue(np.all(np.equal(np.repeat("hello", 1024), values)))

    def testMetadata2(self):
        # Same as above, except that we set metadata twice in a row
        self.sim.set_metadata("greeting", "hello")
        self.sim.set_metadata("greeting", "goodbye")
        # Get value of a metadata field for all images
        values = self.sim.get_metadata("greeting")
        # We get back 'hello' 1024 times
        self.assertTrue(np.all(np.equal(np.repeat("goodbye", 1024), values)))

    def testMetadata3(self):
        # A new metadata column 'rand_value' added to all images in the simulation, with random values
        rand_values = np.random.rand(1024)
        self.sim.set_metadata("rand_value", rand_values)
        # Get value of a metadata field for all images
        values = self.sim.get_metadata("rand_value")
        self.assertTrue(np.allclose(rand_values, values))

    def testMetadata4(self):
        # 2 new metadata columns 'rand_value1'/'rand_value2' added, with random values
        rand_values1 = np.random.rand(1024)
        rand_values2 = np.random.rand(1024)
        new_data = np.column_stack([rand_values1, rand_values2])
        self.assertFalse(self.sim.has_metadata(["rand_value1", "rand_value2"]))
        self.sim.set_metadata(["rand_value1", "rand_value2"], new_data)
        self.assertTrue(self.sim.has_metadata(["rand_value2", "rand_value1"]))
        # Get value of metadata fields for all images
        values = self.sim.get_metadata(["rand_value1", "rand_value2"])
        self.assertTrue(np.allclose(new_data, values))

    def testMetadata5(self):
        # 2 new metadata columns 'rand_value1'/'rand_value2' added, for SPECIFIC indices
        values1 = [11, 12, 13]
        values2 = [21, 22, 23]
        new_data = np.column_stack([values1, values2])
        # Set value of metadata fields for indices 0, 1, 3
        self.sim.set_metadata(
            ["rand_value1", "rand_value2"], new_data, indices=[0, 1, 3]
        )
        # Get value of metadata fields for indices 0, 1, 2, 3
        values = self.sim.get_metadata(["rand_value1", "rand_value2"], [0, 1, 2, 3])
        # values that we didn't specify in get_metadata get initialized as 'missing'
        # according to the detected dtype of input, in this case, np.iinfo(int).min
        self.assertTrue(
            np.allclose(
                np.column_stack(
                    [
                        [11, 12, np.iinfo(int).min, 13],
                        [21, 22, np.iinfo(int).min, 23],
                    ]
                ),
                values,
                equal_nan=True,
            )
        )

    def test_get_metadata_all(self):
        """
        Test we can get the entire metadata table.
        """

        # Get the metadata via our API.
        metadata_api = self.sim.get_metadata()

        # Access the metadata directly in the frame.
        metadata_array = np.vstack(
            [self.sim._metadata[k] for k in self.sim._metadata.keys()]
        ).T

        # Assert we've returned the entire table.
        self.assertTrue(np.all(metadata_api == metadata_array))

    def test_get_metadata_index_slice(self):
        """
        Test we can get all columns for a selection of rows.
        """
        # Test rows
        rows = [0, 1, 42]

        # Get the metadata from our API.
        metadata_api = self.sim.get_metadata(indices=rows)

        # Access the metadata directly in the frame.
        metadata_df = np.vstack(
            [self.sim._metadata[k] for k in self.sim._metadata.keys()]
        ).T[rows]

        # Assert we've returned the rows
        self.assertTrue(np.all(metadata_api == metadata_df))

    def test_update_properties(self):
        """
        Test to see if updating certain key properties that modify metadata give us a new sim,
        leaving the original untouched
        """
        metadata_before = self.sim.get_metadata().copy()

        ref = R.random(len(self.sim.rotations)).as_matrix()

        sim = self.sim.update(rotations=ref)
        metadata_after = self.sim.get_metadata().copy()
        assert np.all(metadata_before == metadata_after)
        assert np.allclose(sim.rotations, ref)

        sim = self.sim.update(amplitudes=np.ones_like(self.sim.amplitudes))
        metadata_after = self.sim.get_metadata().copy()
        assert np.all(metadata_before == metadata_after)
        assert np.allclose(sim.amplitudes, np.ones_like(self.sim.amplitudes))
