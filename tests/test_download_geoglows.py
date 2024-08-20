import sys
import os

def main():
    # Set up paths and call module
    root = os.path.dirname(__file__)
    module_path = os.path.abspath(os.path.join(root, '..', 'modules'))
    sys.path.append(module_path)
    from geoglows import Geoglows

    # Instantiate the Geoglows class and retrieve the data bucket
    glw = Geoglows()
    dataset = glw.get_bucket()

    # Verify COMIDs for data downloading
    comids_path = os.path.join(root, '..', 'assets', 'ecuador.csv')
    comids = glw.verify_comids(ds=dataset, csv=comids_path)

    # Download data for the first 10 COMIDs
    hs_data = glw.get_data(ds=dataset, comids=comids[0:10])

    # Set output path
    out_path = os.path.abspath(os.path.join(root, '..', 'outputs'))

    # Save data in both overall and individual formats
    glw.save_data(data=hs_data, save_type="overall", dir_path=out_path)
    glw.save_data(data=hs_data, save_type="individual", dir_path=out_path)


if __name__ == "__main__":
    main()
