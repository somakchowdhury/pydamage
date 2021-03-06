import numpy as np
import os
import sys
import shutil
from statsmodels.stats.multitest import multipletests
import pandas as pd


def check_extension(filename):
    """Check alignment file format to give correct open mode

    Args:
        filename (str): Path to alignment file

    Returns:
        str: opening mode

    Raises:
        Exception: Extension not supported
    """
    extension = filename.split(".")[-1]
    modes = {'bam': 'rb', 'sam': 'r', 'cram': 'rc'}
    try:
        return(modes[extension])
    except KeyError:
        raise Exception(f"{extension} file extension not supported")


def makedir(dirpath, confirm=True, force=False):
    """Make directory if user confirms overwritting

    Args:
        dirpath (str): Path to directory
        confirm (bool, optional): Ask the user to confirm. Defaults to True.
        force (bool, optional): Always create directory. Defaults to False.
    """
    if os.path.exists(dirpath):
        if confirm and force == False:
            print(
                f"Result directory, {dirpath}, already exists, it will be overwritten")
            if input('Do You Want To Continue? (y|n) ').lower() != 'y':
                sys.exit()
        shutil.rmtree(dirpath)

    os.makedirs(dirpath)


def pandas_processing(res_dict, outdir):
    """Performs Pandas processing of Pydamage results

    Args:
        res_dict (dict): Result dictionary of Vuong's closeness test
        outdir (str): Path to output directory
    """
    df = pd.DataFrame(res_dict)
    if len(res_dict) == 0:
        return(df)
    qvalues = pd.Series(multipletests(df['pvalue'].dropna(), method='fdr_bh')[
                        1], index=df['pvalue'].dropna().index, name='qvalue')
    df = df.merge(qvalues, left_index=True, right_index=True, how='outer')
    df = df[['unif_pmin', 'unif_pmin_stdev',
             'geom_p', 'geom_p_stdev',
             'geom_pmin', 'geom_pmin_stdev',
             'geom_pmax', 'geom_pmax_stdev',
             'pvalue',
             'qvalue',
             'RMSE',
             'reference',
             'nb_reads_aligned',
             'coverage'] +
            [f"CtoT-{i}" for i in range(df['qlen'].max())] +
            [f"GtoA-{i}" for i in range(df['qlen'].max())]]
    df.sort_values(by=['qvalue'], inplace=True)
    df.set_index("reference", inplace=True)
    df.dropna(axis=1, how='all', inplace=True)

    df.to_csv(f"{outdir}/pydamage_results.csv")
    return(df)


def sort_dict_by_keys(adict):
    """Sort dictonary by keys

    Args:
        adict (dict): dictorary to sort
    Returns:
        dict: dictionary sorted on keys
    """
    res = {}
    for k in sorted(adict.keys()):
        res[k] = adict[k]
    return(res)


def RMSE(residuals):
    """Computes Root Mean Square Error

    Args:
        residuals (np.array(float)): Array of residuals
    Returns:
        float: RMSE
    """
    return(np.sqrt(np.mean(residuals**2)))


def create_ct_cc_dict(ct_data, cc_data, wlen):
    """Creates C bases positions dictionnary

    For C->T transitions
    For C in reference and in query

    Args:
        ct_data (list of int): List of positions where CtoT transitions were observed
        cc_data (list of int): List of positions where C in ref and query
    Returns:
        dict{int:int}: {position: number of CtoT transitions at position}
        dict{int:int}: {position: number of C match at position}
    """
    c2t_pos, c2t_counts = np.unique(np.sort(ct_data), return_counts=True)
    c2c_pos, c2c_counts = np.unique(np.sort(cc_data), return_counts=True)
    c2t = dict(zip(c2t_pos, c2t_counts))
    c2c = dict(zip(c2c_pos, c2c_counts))
    c2t_dict = {}
    c2c_dict = {}

    for i in range(wlen):
        if i in c2c or i in c2t:
            if i in c2t:
                c2t_dict[i] = c2t[i]
            else:
                c2t_dict[i] = 0
            if i in c2c:
                c2c_dict[i] = c2c[i]
            else:
                c2c_dict[i] = 0

    return(c2t_dict, c2c_dict)
