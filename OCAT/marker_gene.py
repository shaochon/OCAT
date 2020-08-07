import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def calculate_marker_gene(data, labels, topn, num_cluster, gene_labels, save_fig = None, save_csv = None):
    #TODO: add labels for the genes
    #data gene expression matrix gene x cell
    num_gene, num_cell = data.shape
    cluster_order = []
    gene_idxv = []
    num_cells_inC = []

    #calculate mean of gene expression for each cluster
    #gene x cluster
    gene_mean = np.zeros((num_gene,num_cluster))
    gene_DE_score = np.zeros((num_gene,num_cluster))
    for i in range(num_cluster):
        ind = np.where(labels.flatten() == np.unique(labels)[i])
        gene_mean[:,i] = np.mean(data[:,ind[0]], axis=1).flatten()
        cluster_order = np.append(cluster_order,ind).astype(int)
        num_cells_inC = np.append(num_cells_inC, len(ind[0])).astype(int)
    #find out which cluster expressed the most for each gene
    gene_value_idx = np.argmax(gene_mean,axis = 1)
    #compute DE score for each gene
    for i in range(num_cluster):
        diff = abs( np.matmul(gene_mean[:,i].reshape((num_gene,1)),np.ones((1,num_cluster))) - gene_mean)
        gene_DE_score[:,i] = np.sum( diff, axis = 1)

    #top k for each cluster based on DE score
    gclusters = []
    gscore = []
    for i in range(num_cluster):
        zz_idx = np.where(gene_value_idx == i ) # find genes' DE score in cluster i
        zz_DEscore = gene_DE_score[zz_idx,i].flatten() * (-1)
        zzvalue = np.sort(zz_DEscore, axis = 0) * (-1)
        zz1 = np.argsort(zz_DEscore, axis = 0).astype(int)
        gene_idxv = np.append(gene_idxv, zz_idx[0][zz1[0:topn]] ).astype(int)
        gclusters = np.append(gclusters, i*np.ones((topn,1)) )
        gscore = np.append(gscore, zzvalue[0:topn] )
    #GL500 = np.array([gene_idxv,gclusters,gscore]).transpose()

    #datav number of cluster * top n x number of cells
    #column vector, for each cell, the top 10 genes for each cluster that
    #differentiats the most
    if save_csv:
        gene_labels_save = gene_labels[gene_idxv]
        gene_labels_save = np.reshape(gene_labels_save, [num_cluster, topn])
        cluster_labels_save = ['C_{}'.format(i+1) for i in range(num_cluster)]
        genes_df = pd.DataFrame(gene_labels_save, index=cluster_labels_save)
        genes_df.to_csv(save_csv)

    if save_fig:
        _, idx = np.unique(gene_idxv, return_index=True)
        gene_idxv_u = gene_idxv[np.sort(idx)]
        datav = data[gene_idxv_u,:][:,cluster_order]
        gene_labels = gene_labels[gene_idxv_u]
        gene_len = gene_labels.shape[0]
        #center is num_cluster * top n column vector, each value corresponds the average expression
        #for a gene across all num_cells
        center = np.mean(datav, axis = 1)
        #standard deviation
        scale = np.std(datav, axis = 1)
        #Check for zeros and set them to 1 so not to scale them.
        scale_ind = np.where(scale == 0)
        scale[scale_ind] = 1
        #(data - mean)/scale deviation
        sdata = np.divide(np.subtract(datav,center.reshape((gene_len,1))),scale.reshape((gene_len,1)))
        thresh = 3
        plot_marker_genes(sdata, gene_labels, num_cells_inC, thresh, save_fig)
    return

def plot_marker_genes(sdata, gene_labels, num_cells_inC, thresh, save_fig):
    num_cluster = len(num_cells_inC)
    num_cell = sdata.shape[1]
    gene_len = sdata.shape[0]
    #plot color map
    fig = plt.figure(figsize=(16,16))
    plt.imshow(sdata,cmap='RdBu_r',vmin=-thresh, vmax=thresh, aspect='auto')
    #plt.colorbar()
    xtkval = np.cumsum(num_cells_inC)
    xtkval1 = np.zeros(num_cluster)
    xtllab = []
    for i in range(num_cluster):
        #plt.axhline(y=i*topn, color='w')
        if i == 0:
            xtkval1[i] = 0.5*num_cells_inC[i]
            xtllab = np.append(xtllab, "C1")
            plt.axhline(xmin=0, xmax=xtkval[i]/num_cell, y=gene_len, linewidth=4, color='C'+str(i))
        else:
            xtkval1[i] = 0.5*num_cells_inC[i] +  xtkval[i-1]
            xtllab = np.append(xtllab, "C"+str(i+1))
            plt.axhline(xmin=xtkval[i-1]/num_cell, xmax=xtkval[i]/num_cell, y=gene_len,linewidth=4, color='C'+str(i%9))
    plt.xticks(xtkval1,xtllab)
    if gene_labels is None:
        plt.yticks(np.arange(gene_len))
    else:
        plt.yticks(np.arange(gene_len),gene_labels.flatten())
    #filename='marker_gene_{}_{}.png'.format(num_cluster, topn)
    plt.savefig(save_fig)
    return
