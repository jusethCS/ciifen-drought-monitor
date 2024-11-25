import os
import s3fs
import xarray as xr
import numpy as np
import pandas as pd
from datetime import datetime

class Geoglows:
    """
    A class for downloading and managing streamflow data from the ECMWF global 
    hydrological model (GEOGLOWS).
    """

    def __init__(self) -> None:
        """
        Initializes the Geoglows object by setting up the connection to the S3
        bucket containing the GEOGLOWS retrospective simulation dataset.
        """
        self.s3store = self._initialize_s3store()

    def _initialize_s3store(self) -> s3fs.S3Map:
        """
        Initializes the S3 store for accessing the GEOGLOWS dataset.

        Returns:
            s3fs.S3Map: An S3Map object that links to the specified GEOGLOWS 
                        dataset.
        """
        params = {'region_name': 'us-west-2'}
        url = 's3://geoglows-v2-retrospective/retrospective.zarr'
        s3 = s3fs.S3FileSystem(anon=True, client_kwargs=params)
        return s3fs.S3Map(root=url, s3=s3, check=False)

    def get_bucket(self) -> xr.Dataset:
        """
        Opens and retrieves the GEOGLOWS dataset from the S3 bucket.

        Returns:
            xarray.Dataset: The GEOGLOWS retrospective dataset.
        """
        return xr.open_zarr(self.s3store)

    def verify_comids(self, ds: xr.Dataset, csv: str) -> list:
        """
        Verifies which COMIDs (Catchment Object Identifiers) are available 
        both in the dataset and in the provided CSV file.

        Args:
            ds (xarray.Dataset): The GEOGLOWS dataset containing river IDs.
            csv (str): The path to the CSV file containing the list of 
                       COMIDs to check.

        Returns:
            list: A list of COMIDs that are present both in the dataset and
                  in the CSV file.
        """
        ds_comids = set(ds.rivid.values)
        ec_comids = set(pd.read_csv(csv)['comid'])
        return list(ds_comids.intersection(ec_comids))

    def get_data(self, ds: xr.Dataset, comids: list) -> pd.DataFrame:
        """
        Retrieves and structures streamflow data for the specified COMIDs.

        Args:
            ds (xarray.Dataset): The GEOGLOWS dataset containing streamflow data
            comids (list): A list of COMIDs to extract data for.

        Returns:
            pd.DataFrame: A DataFrame where each column represents the streamflow
            data for a specific COMID, indexed by time.
        """
        batch_size = 200
        result_frames = []

        # Process COMIDs in batches
        for i in range(0, len(comids), batch_size):
            batch_comids = comids[i:i + batch_size]
            
            # Extract data for the current batch of COMIDs
            df = ds['Qout'].sel(rivid=batch_comids).to_dataframe().reset_index()
            df_pivot = df.pivot(index='time', columns='rivid', values='Qout')
            result_frames.append(df_pivot)
            print("Downloaded batch data")

        # Combine all batch results into a single DataFrame
        combined_df = pd.concat(result_frames, axis=1)

        # Resample to monthly means
        df_monthly = combined_df.resample('MS').mean()

        # Define date filters: start from January 1991 and end at the previous month
        start_date = '1991-01-01'
        end_date = (datetime.now().replace(day=1) - pd.DateOffset(months=1)).strftime('%Y-%m-%d')

        # Filter the DataFrame for the date range
        df_filtered = df_monthly.loc[start_date:end_date]
        return df_filtered
    

    def save_data(self, data: pd.DataFrame, save_type: str, dir_path: str) -> None:
        """
        Saves the given DataFrame based on the specified save type.

        Parameters:
        - data (pd.DataFrame): The DataFrame containing the data to be saved.
        - save_type (str): Specifies how to save the data. Options are:
            - "overall": Saves the entire DataFrame to a single CSV file.
            - "individual": Saves each column of the DataFrame as a separate CSV file.
        - dir_path (str): The directory path where the files should be saved.

        Raises:
        - ValueError: If the save_type is not 'overall' or 'individual'.
        """
        if save_type == "overall":
            data.to_csv(os.path.join(dir_path, "historical_simulation.csv"))
        elif save_type == "individual":
            for column in data.columns:
                temp_data = data[[column]].copy()
                temp_data.to_csv(os.path.join(dir_path, f'{column}.csv'))
        else:
            raise ValueError("save_type must be 'overall' or 'individual'!")
        
    def save_format_data(self, data: pd.DataFrame, save_type: str, dir_path: str) -> None:
        """
        Saves the given DataFrame based on the specified save type.

        Parameters:
        - data (pd.DataFrame): The DataFrame containing the data to be saved.
        - save_type (str): Specifies how to save the data. Options are:
            - "overall": Saves the entire DataFrame to a single CSV file.
            - "individual": Saves each column of the DataFrame as a separate CSV file.
        - dir_path (str): The directory path where the files should be saved.

        Raises:
        - ValueError: If the save_type is not 'overall' or 'individual'.
        """
        if save_type == "overall":
            data.to_csv(os.path.join(dir_path, "historical_simulation.csv"))
        elif save_type == "individual":
            for column in data.columns:
                temp_data = data[[column]].copy()
                temp_data['year'] = temp_data.index.strftime('%Y')
                temp_data['month'] = temp_data.index.strftime('%m')
                temp_data = temp_data[['year', 'month', column]]
                temp_data.to_csv(os.path.join(dir_path, f'{column}.csv'), sep='\t', header=False, index=False)
        else:
            raise ValueError("save_type must be 'overall' or 'individual'!")

