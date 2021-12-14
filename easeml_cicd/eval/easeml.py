from keras import backend as K
import os
import shutil


def eval_accuracy(y_data, y_pred, func):
    # defining the api-endpoint 
    with open('libs/id.txt') as f:
        proj_id = f.read().splitlines()[0]
    acc = K.eval(100 * K.sum(func(y_data, y_pred)) / len(y_pred))

    print("@##Your score {}".format(acc))

    outpath = '/data/' + proj_id
    if os.path.exists(outpath) is True:
        print("The {0} directory already exists.".format(outpath))
    else:
        print("Creating the {0} directory.".format(outpath))
        os.makedirs(outpath, exist_ok=True)

    with open(outpath + '/results.txt', 'w') as f:
        f.write(str(acc))
