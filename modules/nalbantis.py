import numpy as np
import pandas as pd

class Nalbantis:
    """
    A class for computing and managing the Streamflow Drought Index (SDI) 
    proposed by Nalbantis (2008).
    """

    def aggregate_data(self, streamflow: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregates streamflow data by calculating rolling means over different
        periods (3, 6, 9, and 12 months).

        Args:
            streamflow (pd.DataFrame): A dataframe containing streamflow data 
            with at least a 'value' column representing streamflow values.

        Returns:
            pd.DataFrame: The modified dataframe with additional columns for 
            the rolling means and NaN values removed.
        """
        for months in [1, 3, 6, 9, 12]:
            streamflow[f"value_{months}m"] = streamflow['value'].rolling(
                window=months).mean()
        
        return streamflow.dropna() #streamflow[streamflow['year'] > 1980].dropna()
    
    
    def compute_sdi(self, streamflow: pd.DataFrame, column: str) -> pd.DataFrame:
        """
        Computes the Streamflow Drought Index (SDI) for a specific rolling 
        mean column.

        Args:
            streamflow (pd.DataFrame): A dataframe with streamflow values.
            column (str): The column name for which to compute SDI (e.g., 
            'value', 'value_3m').

        Returns:
            pd.DataFrame: A dataframe with an additional SDI column for the 
            specific rolling mean.
        """
        monthly_stats = streamflow.groupby('month')[column].agg(
            ['mean', 'std']).reset_index()
        streamflow = streamflow.merge(monthly_stats, on='month', how='left')
        streamflow[f"sdi_{column}"] = (
            streamflow[column] - streamflow['mean']) / streamflow['std']
        return streamflow.drop(['mean', 'std'], axis=1)
    

    def compute_overall(self, streamflow: pd.DataFrame) -> pd.DataFrame:
        """
        Compute the Streamflow Drought Index (SDI) for 1 month, 3 months, 6 
        months, 9 months, and 12 months using the method proposed by Nalbantis 
        (2008).

        Args:
            streamflow (pd.DataFrame): A dataframe with columns: year, month, 
            day, value.

        Returns:
            pd.DataFrame: A dataframe containing the SDI values for each period
            (1m, 3m, 6m, 9m, 12m).
        """
        streamflow = self.aggregate_data(streamflow)

        # Compute SDI for each period (1m, 3m, 6m, 9m, 12m)
        for months in [1, 3, 6, 9, 12]:
            streamflow = self.compute_sdi(streamflow, f'value_{months}m') 
        streamflow = streamflow.drop(
            ["value_1m","value_3m","value_6m","value_9m","value_12m"], axis=1)
        return streamflow
