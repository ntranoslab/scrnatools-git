"""
Calculates DE marker genes for data clusters
From scrnatools package

Created on Mon Jan 10 15:57:46 2022

@author: joe germino (joe.germino@ucsf.edu)
"""

# external imports
from anndata import AnnData
from pandas import DataFrame
from typing import Optional, Dict
from scvi.model import SCVI

# scrnatools package imports
from .._configs import configs
from .._utils import debug, check_path

logger = configs.create_logger(__name__.split('_', 1)[1])


# -------------------------------------------------------function----------------------------------------------------- #


@debug(logger, configs)
def cluster_de(
        adata: AnnData,
        model: SCVI,
        cluster_key: str,
        lfc_mean_threshold: int = 0,
        bayes_factor_threshold: int = 3,
        non_zeroes_proportion_threshold: int = 0.1,
        save_path: Optional[str] = None,
        subset: bool = True,
) -> Dict[str, DataFrame]:
    """
    Calculates DE marker genes for data clusters

    Parameters
    ----------
    adata
        The data to analyze
    model
        The scVI model for 'adata'
    cluster_key
        The column name of the cluster data in 'adata.obs'
    lfc_mean_threshold
        The minimum lfc_mean to filter de genes on (exclusive). Default 0
    bayes_factor_threshold
        The minimum bayes factor to filter de genes on (exclusive). Default 3
    non_zeroes_proportion_threshold
        The minimum proportion of cells with non-zero expression filter de genes on (exclusive). Default 0.1
    save_path
        The path to save the marker gene lists to. Default None
    subset
        Whether to subset the DE gene list based on thresholds or return all genes in data. Default True

    Returns
    -------
    A dictionary with keys equal to the categories of the cluster column in 'adata.obs' (i.e. cell types) linked to
    DataFrames of the filtered (or unfiltered but sorted) DE marker genes for that cluster

    Raises
    -------
    ValueError
        If 'cluster_key' is not a valid column in 'adata.obs.columns'
    """
    if cluster_key not in adata.obs.columns:
        raise ValueError(f"{cluster_key} is not a valis column in 'adata.obs'")
    de_df = model.differential_expression(groupby=cluster_key, )
    cats = adata.obs[cluster_key].cat.categories
    markers = {}
    for i, c in enumerate(cats):
        cid = f"{c} vs Rest"
        cell_type_df = de_df.loc[de_df.comparison == cid]
        if subset:
            cell_type_df = cell_type_df[cell_type_df.lfc_mean > lfc_mean_threshold]
            cell_type_df = cell_type_df[cell_type_df["bayes_factor"] > bayes_factor_threshold]
            cell_type_df = cell_type_df[cell_type_df["non_zeros_proportion1"] > non_zeroes_proportion_threshold]
        markers[c] = cell_type_df
    if save_path is not None:
        check_path(save_path)
        for cluster, marker_genes in markers.items():
            if save_path[-1] == "/":
                save_path = save_path[:-1]
            check_path(save_path)
            marker_genes.to_csv(f"{save_path}/{cluster}.csv")
    return markers
