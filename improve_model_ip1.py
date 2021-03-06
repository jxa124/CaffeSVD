#coding=utf-8
# test decompress ip1 layer
import caffe
from caffe import layers as L, params as P, to_proto
from caffe.proto import caffe_pb2
import lmdb
import numpy as np
import os
import sys
from numpy import linalg as la
import matplotlib.pyplot as plt 
from base import *
from mcluster import *

CAFFE_HOME = "/opt/caffe/"
RESULT_DIR = "./result/"

SVD_R = 6 # 64 x 1024 
deploySVD = GetIP1SVDProto(SVD_R)
iter_num = 20000

train_db = CAFFE_HOME + "examples/cifar10/cifar10_train_lmdb"
test_db = CAFFE_HOME + "examples/cifar10/cifar10_test_lmdb"
mean_proto = CAFFE_HOME + "examples/cifar10/mean.binaryproto"
mean_npy = "./mean.npy"
mean_pic = np.load(mean_npy)

def read_db(db_name):
    lmdb_env = lmdb.open(db_name)
    lmdb_txn = lmdb_env.begin()
    lmdb_cursor = lmdb_txn.cursor()
    datum = caffe.proto.caffe_pb2.Datum()

    X = []
    y = []
    cnts = {}
    for key, value in lmdb_cursor:
        datum.ParseFromString(value)
        label = datum.label
        data = caffe.io.datum_to_array(datum)
        #data = data.swapaxes(0, 2).swapaxes(0, 1)
        X.append(data)
        y.append(label)
        if label not in cnts:
            cnts[label] = 0
        cnts[label] += 1
        #plt.imshow(data)
        #plt.show()
    return X, np.array(y), cnts

testX, testy, cnts = read_db(test_db)
#testX, testy, cnts = read_db(train_db)
print ("#train set: ", len(testX))
print ("the size of sample:", testX[0].shape)
print ("kinds: ", cnts)

if not os.path.exists("label.npy"):
    np.save("label.npy", testy)

# 生成配置文件
# CAFFE_HOME
example_dir = CAFFE_HOME + "examples/cifar10/"
build_dir = "./build_ip1/"

# 加载新的模型
if len(sys.argv) == 1:
    print ("NO MODEL :-(")
    sys.exit(1)
else:
    new_model = sys.argv[1]

#new_model = "./new/ip1_SVD%d/ip1_SVD%d_iter_%d.caffemodel.h5" % (SVD_R,SVD_R, iter_num) 
nn = caffe.Net(deploySVD, new_model, caffe.TEST)

#np.save("ip1_SVD%d_ipZ.npy" % SVD_R, data)

Z = nn.params["ipZ"][0].data
Z = get_cluster_mat(Z, 16)
Z = get_round_mat(Z, 4)
nn.params["ipZ"][0].data[...] = Z

U = nn.params["ipU"][0].data
U = get_cluster_mat(U, 16)
U = get_round_mat(U, 4)
nn.params["ipU"][0].data[...] = U

ip2 = nn.params["ip2"][0].data
ip2 = get_cluster_mat(ip2, 16)
ip2 = get_round_mat(ip2, 4)
nn.params["ip2"][0].data[...] = ip2

n = len(testX)
pre = np.zeros(testy.shape)
print ("N = %d" % n)
for i in range(n):
    nn.blobs["data"].data[...] = testX[i] - mean_pic 
    nn.forward()
    prob = nn.blobs["prob"].data
    pre[i] = prob.argmax() 
    print ("%d / %d" % (i + 1, n))
right = np.sum(pre == testy) 
print ("Accuracy: %f" % (right * 1.0 / n))


model_name = new_model.split("/")[-1] 
np.save(RESULT_DIR + "%s_cluster16_f4_all.npy" % (model_name), pre)
