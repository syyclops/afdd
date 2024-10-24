import unittest
from unittest.mock import MagicMock, patch, call
import pandas as pd

# Import the actual strip_brick_prefix function
from afdd.utils import strip_brick_prefix
from afdd.db import load_graph_data

class TestLoadGraphData(unittest.TestCase):
    @patch('afdd.db.load_component_data')
    def test_load_graph_data(self, mock_load_component_data):
        # Prepare mock rules_list with duplicate component types
        class Rule:
            def __init__(self, component_type):
                self.component_type = component_type

        rules_list = [
            Rule(component_type='ComponentA'),
            Rule(component_type='ComponentB'),
            Rule(component_type='ComponentA'),  # Duplicate to test uniqueness
        ]

        # Expected unique component classes
        expected_component_classes = {'ComponentA', 'ComponentB'}

        # Mock dataframes returned by load_component_data
        df_component_a = pd.DataFrame({
            'point': ['point1', 'point2'],
            'class': ['brick:Class1', 'brick:Class2'],
            'other_col': [1, 2],
        })

        df_component_b = pd.DataFrame({
            'point': ['point3'],
            'class': ['brick:Class3'],
            'other_col': [3],
        })

        # Define side effects for mock_load_component_data
        def load_component_data_side_effect(driver, component_class):
            if component_class == 'ComponentA':
                return df_component_a
            elif component_class == 'ComponentB':
                return df_component_b
            else:
                return pd.DataFrame()

        mock_load_component_data.side_effect = load_component_data_side_effect

        # Mock driver
        mock_driver = MagicMock()

        # Call the function under test
        result_df = load_graph_data(driver=mock_driver, rules_list=rules_list)

        # Assert load_component_data was called correctly
        expected_calls = [
            call(mock_driver, 'ComponentA'),
            call(mock_driver, 'ComponentB'),
        ]
        mock_load_component_data.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(mock_load_component_data.call_count, 2)

        # Prepare expected result dataframe
        expected_df = pd.concat([df_component_a, df_component_b], ignore_index=True)
        expected_df = expected_df.drop_duplicates()
        expected_df['class'] = expected_df['class'].apply(strip_brick_prefix)

        # Apply strip_brick_prefix to the result_df
        result_df['class'] = result_df['class'].apply(strip_brick_prefix)

        # Assert the result dataframe matches expected dataframe
        pd.testing.assert_frame_equal(
            result_df.reset_index(drop=True), expected_df.reset_index(drop=True)
        )

    @patch('afdd.db.load_component_data')
    def test_load_graph_data_with_duplicates(self, mock_load_component_data):
        # Prepare mock rules_list
        class Rule:
            def __init__(self, component_type):
                self.component_type = component_type

        rules_list = [Rule(component_type='ComponentA')]

        # Mock dataframe with duplicates
        df_with_duplicates = pd.DataFrame({
            'point': ['point1', 'point1'],  # Duplicate row
            'class': ['brick:Class1', 'brick:Class1'],
            'other_col': [1, 1],
        })

        # Set return value for load_component_data
        mock_load_component_data.return_value = df_with_duplicates

        # Mock driver
        mock_driver = MagicMock()

        # Call the function under test
        result_df = load_graph_data(driver=mock_driver, rules_list=rules_list)

        # Apply strip_brick_prefix to the result_df
        result_df.loc[:, 'class'] = result_df['class'].apply(strip_brick_prefix)

        # Prepare expected result dataframe (duplicates removed)
        expected_df = df_with_duplicates.drop_duplicates()
        expected_df.loc[:, 'class'] = expected_df['class'].apply(strip_brick_prefix)

        # Assert the result dataframe matches expected dataframe
        pd.testing.assert_frame_equal(
            result_df.reset_index(drop=True), expected_df.reset_index(drop=True)
        )

    @patch('afdd.db.load_component_data')
    def test_load_graph_data_empty_rules_list(self, mock_load_component_data):
        # Empty rules_list
        rules_list = []

        # Call the function under test
        result_df = load_graph_data(driver=MagicMock(), rules_list=rules_list)

        # Assert load_component_data was never called
        mock_load_component_data.assert_not_called()

        # Assert the result is an empty dataframe
        self.assertTrue(result_df.empty)

    @patch('afdd.db.load_component_data')
    def test_load_graph_data_exception_handling(self, mock_load_component_data):
        # Prepare mock rules_list
        class Rule:
            def __init__(self, component_type):
                self.component_type = component_type

        rules_list = [Rule(component_type='ComponentA')]

        # Mock load_component_data to raise an exception
        mock_load_component_data.side_effect = Exception("Database error")

        # Mock driver
        mock_driver = MagicMock()
        mock_driver.close = MagicMock()

        # Call the function under test and expect it to handle the exception
        with self.assertRaises(Exception):
            load_graph_data(driver=mock_driver, rules_list=rules_list)

        # Assert driver.close was called
        mock_driver.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
