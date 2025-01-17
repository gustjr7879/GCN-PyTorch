import  torch
from    torch import nn
from    torch import optim
from    torch.nn import functional as F

import  numpy as np
from    data import load_data, preprocess_features, preprocess_adj
from    model import GCN
from    config import  args
from    utils import masked_loss, masked_acc
import time
'''
seed = 123
np.random.seed(seed)
torch.random.manual_seed(seed)
'''

for i in range(100):
    adj, features, y_train, y_val, y_test, train_mask, val_mask, test_mask= load_data(args.dataset) # adj is new adj , graph is new graph

    #G = nx.from_dict_of_lists(new_graph)
    #G.remove_edges_from(nx.selfloop_edges(G)) 
    features = preprocess_features(features) # [49216, 2], [49216], [2708, 1433]
    supports = preprocess_adj(adj)

    device = torch.device('cuda')
    train_label = torch.from_numpy(y_train).long().to(device)
    num_classes = train_label.shape[1]
    train_label = train_label.argmax(dim=1)
    train_mask = torch.from_numpy(train_mask.astype(np.int32)).to(device)
    val_label = torch.from_numpy(y_val).long().to(device)
    val_label = val_label.argmax(dim=1)
    val_mask = torch.from_numpy(val_mask.astype(np.int32)).to(device)
    test_label = torch.from_numpy(y_test).long().to(device)
    test_label = test_label.argmax(dim=1)
    test_mask = torch.from_numpy(test_mask.astype(np.int32)).to(device)

    i = torch.from_numpy(features[0]).long().to(device)
    v = torch.from_numpy(features[1]).to(device)
    feature = torch.sparse.FloatTensor(i.t(), v, features[2]).float().to(device)

    i = torch.from_numpy(supports[0]).long().to(device)
    v = torch.from_numpy(supports[1]).to(device)
    support = torch.sparse.FloatTensor(i.t(), v, supports[2]).float().to(device)

    #print('x :', feature)
    #print('sp:', support)
    num_features_nonzero = feature._nnz()
    feat_dim = feature.shape[1]


    net = GCN(feat_dim, num_classes, num_features_nonzero)
    net.to(device)
    optimizer = optim.Adam(net.parameters(), lr=args.learning_rate)

    start = time.time()
    net.train()
    for epoch in range(args.epochs):

        out = net((feature, support))
        out = out[0]
        loss = masked_loss(out, train_label, train_mask)
        loss += args.weight_decay * net.l2_loss()

        acc = masked_acc(out, train_label, train_mask)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        #if epoch % 10 == 0:

            #print(epoch, loss.item(), acc.item())

    net.eval()
    end = time.time()
    check_time = end - start

    out = net((feature, support))
    out = out[0]
    acc = masked_acc(out, test_label, test_mask)
    print('test:', acc.item(),'time:',check_time)

