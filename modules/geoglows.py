import s3fs
import xarray as xr
import numpy as np
import pandas as pd

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
        df = ds['Qout'].sel(rivid=comids).to_dataframe().reset_index()
        df_pivot = df.pivot(index='time', columns='rivid', values='Qout')
        df_monthly = df_pivot.resample('ME').mean()
        return df_monthly