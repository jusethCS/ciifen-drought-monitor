import sys
import os
import pandas as pd


def main():
    # Set up paths and call module
    root = os.path.dirname(__file__)
    module_path = os.path.abspath(os.path.join(root, '..', 'modules'))
    sys.path.append(module_path)
    from geoglows import Geoglows
    from nalbantis import Nalbantis

    # Instantiate the Geoglows class and retrieve the data bucket
    glw = Geoglows()
    dataset = glw.get_bucket()

    # Verify COMIDs for data downloading
    comids_path = os.path.join(root, '..', 'assets', 'ecuador.csv')
    comids = glw.verify_comids(ds=dataset, csv=comids_path)

    # Download data for the first 10 COMIDs
    hs_data = glw.get_data(ds=dataset, comids=comids[0])

    # Parse to data
    hs_data.columns = ["value"]
    hs_data = pd.DataFrame({
        'year': hs_data.index.year,
        'month': hs_data.index.month,
        'day': hs_data.index.day,
        'value': hs_data['value']
    })
    hs_data = hs_data.reset_index()
    hs_data.drop(['time'], axis=1, inplace=True)

    # Compute and save the Stremflow Drought Index
    nlb = Nalbantis()
    sdi = nlb.compute_overall(hs_data)
    out_path = os.path.abspath(os.path.join(root, '..', 'outputs', "nalbantis_test.csv"))
    sdi.to_csv(out_path, sep=",")


if __name__ == "__main__":
    main()












# Set up paths and call module
#root = os.path.dirname(__file__)
#module_path = os.path.abspath(os.path.join(root, '..', 'modules'))
#sys.path.append(module_path)
#from geoglows import Geoglows
#from nalbantis import Nalbantis

## Instantiate the Geoglows class and retrieve the data bucket
#glw = Geoglows()
#dataset = glw.get_bucket()
## Verify COMIDs for data downloading
#comids_path = os.path.join('assets', 'ecuador.csv')
#comids = glw.verify_comids(ds=dataset, csv=comids_path)
## Download data for the first COMID
#hs_data = glw.get_data(ds=dataset, comids=comids[0])

#hs_data = pd.read_csv("outputs/620036106.csv")
#hs_data = hs_data.set_index("time")
#hs_data.index = pd.to_datetime(hs_data.index)


# Parse to data
#hs_data.columns = ["value"]
#hs_data = pd.DataFrame({
#    'year': hs_data.index.year,
#    'month': hs_data.index.month,
#    'day': hs_data.index.day,
#    'value': hs_data['value']
#})
#hs_data = hs_data.reset_index()
#hs_data.drop(['time'], axis=1, inplace=True)


# Compute the Stremflow Drought Index
#nlb = Nalbantis()
#sdi = nlb.compute_overall(hs_data)
#sdi.to_csv("test.csv", sep=",")
#print(sdi)


