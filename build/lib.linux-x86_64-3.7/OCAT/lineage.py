from scipy.sparse import csr_matrix
import numpy as np
from sklearn.cluster import KMeans
import matplotlib
import matplotlib.pyplot as plt
#from matplotlib.path import Path
#import matplotlib.patches as patches
from scipy.spatial import distance
import networkx as nx
import time
#from scipy.interpolate import interp1d, UnivariateSpline
#from scipy.optimize import curve_fit
#from statsmodels.nonparametric.smoothers_lowess import lowess
#from scipy.spatial.transform import Rotation as R
#from mpl_toolkits.mplot3d import Axes3D
import pandas as pd

def estimate_num_cluster(Z):
    n_clusters = int(Z.shape[0]/10)
    thresh = 0.85
    pca = KMeans(n_clusters=n_clusters, n_init=20).fit(Z)
    cluster_label = pca.labels_
    ghost_cells = pca.cluster_centers_
    W = 1-distance.cdist(ghost_cells, ghost_cells, 'cosine')
    A = np.where(W>thresh, 1, 0)
    D = np.diag(A.sum(axis=1))
    L = D-A
    eigvals = np.linalg.eigvals(L)
    n_clusters_1 = np.sum(np.where(eigvals<2.76**-15, 1, 0))
    print(n_clusters_1)
    pca = KMeans(n_clusters=n_clusters_1, n_init=20).fit(Z)
    cluster_label = pca.labels_
    return cluster_label

def compute_lineage(Z, cluster_label = None, root_cluster = None, root_cell = None, reverse = 1, name = None):
    # Sparse matrix
    if cluster_label is None:
        cluster_label = estimate_num_cluster(Z)
    num_cluster = len(np.unique(cluster_label))
    uni_lab = np.unique(cluster_label)
    num_cell, _ = Z.shape
    CC_adjacent = np.zeros((num_cluster,num_cluster))
    for i in range(num_cluster):
        for j in range(i+1,num_cluster):
            ind_i = np.where(cluster_label==uni_lab[i])
            ind_j = np.where(cluster_label==uni_lab[j])
            ni = len(ind_i[0])
            nj = len(ind_j[0])
            X_i = Z[ind_i[0],:]
            X_j = Z[ind_j[0],:]
            #X = np.dot(X_i, X_j.T)
            #sum_ij = np.sum(X)
            sum_ij = np.sum(distance.cdist(X_i, X_j, 'cosine'))
            #sum_ij = np.sum(cc_dis_un[ind_i[0],:][:,ind_j[0]])
            # NEED TO CHANGE THIS
            #CC_adjacent[i,j] = 1-(sum_ij/(ni*nj))
            CC_adjacent[i,j] = sum_ij/(ni*nj)
    # construct Cluster to Cluster graph
    #CC_adjacent = CC_adjacent + CC_adjacent.transpose()
    CC_Graph = nx.from_numpy_matrix(CC_adjacent)
    print(CC_adjacent)
    if root_cluster is None:
        #find the root cluster
        a1, a2 = np.where(CC_adjacent == np.max(CC_adjacent))
        print(a1, a2)
        print('Root cluster candidates:')
        print('C',uni_lab[a1[0]],'  &  C',uni_lab[a2[0]])
        # infer root_cell based on inferred root_cluster
        if reverse == 1:
            print('Using Root cluster:')
            print('C',uni_lab[a1[0]])
            root_cluster = uni_lab[a1[0]]
        else:
            print('Using Root cluster:')
            print('C',uni_lab[a2[0]])
            root_cluster = uni_lab[a2[0]]
    else:
        print('Using user defined Root cluster:')
        print('C',root_cluster)

    Tree = nx.minimum_spanning_tree(CC_Graph,weight = 'weight')
    pred = np.zeros(num_cluster).astype(int) -2
    pred[uni_lab == root_cluster] = -1
    node_count = 1
    while node_count < num_cluster:
        for edge in Tree.edges:
            if (pred[edge[0]] == -2 and pred[edge[1]] != -2):
                pred[edge[0]] = edge[1]
                node_count += 1
            elif (pred[edge[1]] == -2 and pred[edge[0]] != -2):
                pred[edge[1]] = edge[0]
                node_count += 1
    return pred, root_cluster, cluster_label, Tree

def compute_ptime(Z, cluster_label, lineage, root_cluster, latent, root_cell=None):
    t1 = time.time()
    uni_lab = np.unique(cluster_label)
    num_cluster = len(uni_lab)
    pred = lineage
    n_cells = len(cluster_label)
    rootedTree = nx.DiGraph()
    for i in range(len(np.where(pred!=-1)[0])):
        rootedTree.add_edge(uni_lab[pred[pred != -1][i]], uni_lab[np.where(pred!=-1)[0][i]])
    if root_cell is None:
        rootcc_idx = np.where(cluster_label==root_cluster)
        tau_score = np.zeros(len(rootcc_idx[0]))
        Ave_ptime_cc = np.zeros((len(rootcc_idx[0]),num_cluster))
        for jj in range(len(rootcc_idx[0])):
            index = rootcc_idx[0][jj]
            temp = 1-np.dot(Z[index,:], Z.T)/n_cells
            #temp = cc_dis_un[index,:].flatten()
            Ptimejj = np.array(np.argsort(temp)).flatten()
            # Average ptime for each cluster
            for kk in range(num_cluster):
                Ave_ptime_cc[jj,kk] = np.mean(Ptimejj[cluster_label==uni_lab[kk]])
            Ave_ptime_cc[jj,:] = Ave_ptime_cc[jj,:]/np.max(Ave_ptime_cc[jj,:])
            temp = (pred.transpose()+1)/np.max(pred.transpose()+1)
            temp2=Ave_ptime_cc[jj,:].transpose()
            tau_score[jj] = np.corrcoef(temp,temp2)[0,1]
        root_cell_ind = np.argmax(tau_score)
        root_cell = rootcc_idx[0][root_cell_ind]
        print('Inferred root cell is:')
        print('cell', root_cell)
    else:
        print('Using user defined root cell:')
        print('cell', root_cell)
    # Compute CC MST
    # array to keep track of cell distance
    cell_dis = np.zeros(cluster_label.shape)
    # array to keep track of root cells in each cluster
    lab_idx_dict = dict(zip(uni_lab, np.arange(num_cluster)))
    root_cell_list = np.zeros(num_cluster)
    # array to keep track of distance between root cells in each cluster
    # as we traverse the graph
    root_cell_dist = np.zeros(num_cluster)
    index_list = np.arange(len(cluster_label))
    root_cell_list[lab_idx_dict.get(root_cluster)] = root_cell
    #cluster_marked = []
    #cluster_marked.append(root_cluster)
    cluster_to_explore = []
    cluster_to_explore.append(root_cluster)
    while(len(cluster_to_explore) != 0):
        curr_cluster = cluster_to_explore.pop(0)
        curr_cluster_idx = lab_idx_dict.get(curr_cluster)
        curr_root_cell_idx = root_cell_list[curr_cluster_idx]
        curr_root_cell = np.expand_dims(Z[int(curr_root_cell_idx),:], axis=0)
        curr_index_list = (cluster_label==curr_cluster)
        cell_dis[curr_index_list] = cell_dis[curr_index_list] + distance.cdist(Z[curr_index_list,:], curr_root_cell).flatten()
        for i in rootedTree.neighbors(curr_cluster):
            i_idx = lab_idx_dict.get(i)
            i_index_list = (cluster_label==i)
            #sim = np.dot(curr_root_cell, Z[curr_index_list,:].T)
            sim = distance.cdist(curr_root_cell, Z[i_index_list,:])
            i_root_index = index_list[i_index_list][np.argmin(sim)]
            root_cell_list[i_idx] = i_root_index
            i_root_cell = np.expand_dims(Z[i_root_index, :], axis=0)
            root_cell_dist[i_idx] = root_cell_dist[curr_cluster_idx] + distance.cdist(curr_root_cell, i_root_cell)[0]
            cell_dis[i_index_list] = root_cell_dist[i_idx]
            cluster_to_explore.append(i)
    Ptime = (cell_dis-np.min(cell_dis))/(np.max(cell_dis)-np.min(cell_dis))
    return Ptime, root_cell_list
