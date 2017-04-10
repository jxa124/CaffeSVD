import os
import numpy as np

def GetSVDProto(r):
    filename = "./proto/SVD/cifar10_SVD%d.prototxt" % r
    if not os.path.exists(filename):
        fin = open("./proto/cifar10_SVD.template", "r")
        fout = open(filename, "w")
        for line in fin.readlines():
            fout.write(line.replace("$", str(r)))
        fin.close()
        fout.close()

    return filename

def get_comfusion_matrix(label, pre, k):
    # TP, FN
    # FP, TN
    wlabel = (label == k)
    wpre = (pre == k)
    TP = np.sum(wlabel & wpre)
    FN = np.sum(wlabel & ~wpre)
    FP = np.sum(~wlabel & wpre)
    TN = np.sum(~wlabel & ~wpre)
    return np.matrix([[TP, FN], [FP, TN]])

def eval_result_k(label, pre, k):
    cm = get_comfusion_matrix(label, pre, k) 
    print ("Confusion Matrix: TP, FN; FP, TN")
    print (cm)
    acc = (cm[0,0] + cm[1,1]) * 1.0 / np.sum(cm)
    precision = cm[0,0] * 1.0 / np.sum(cm[:, 0])
    recall = cm[0,0] * 1.0 / np.sum(cm[0, :])
    F = 2.0 * recall * precision / (recall + precision)
    print ("Accuracy: %f" % acc, "Precision: %f" % precision)
    print ("Recall: %f" % recall, "F-measure: %f" % F)
    return acc, precision, recall, F

def eval_result(label, pre, num_kinds):
    n = len(label)
    s_acc = 0.0
    s_precision = 0.0
    s_recall = 0.0
    s_F = 0.0
    for k in range(num_kinds):
        print ("Kind: %d" % k)
        acc, precision, recall, F = eval_result_k(label, pre, k)
        s_acc += acc
        s_precision += precision
        s_recall += recall
        s_F += F
        print ("========")

    acc = np.sum(pre == label) * 1.0 / n
    print ("Totally:")
    print ("Accuracy: %f" % acc)
    print ("Mean Accuracy: %f" % (s_acc / num_kinds))
    print ("Mean Precision: %f" % (s_precision / num_kinds))
    print ("Mean Recall: %f" % (s_recall / num_kinds))
    print ("Mean F: %f" % (s_F / num_kinds))