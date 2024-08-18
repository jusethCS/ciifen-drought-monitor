import s3fs
import xarray
import numpy as np
import pandas as pd

bucket_uri = 's3://geoglows-v2-retrospective/retrospective.zarr'
region_name = 'us-west-2'
s3 = s3fs.S3FileSystem(anon=True, client_kwargs=dict(region_name=region_name))
s3store = s3fs.S3Map(root=bucket_uri, s3=s3, check=False)
ds = xarray.open_zarr(s3store)

ds_comids = ds.rivid.values.tolist()
ec_comids = pd.read_csv("files/drainage.csv").comid.to_list()
comids = list(set(ds_comids) & set(ec_comids))[0]

df = ds['Qout'].sel(rivid=comids).to_dataframe()
df = df.reset_index().set_index('time').pivot(columns='rivid', values='Qout')


