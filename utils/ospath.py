import os
def checkdirs(root, folders):
    for f in folders:
        fabs = "{}/{}".format(root, f)
        if not os.path.isdir(fabs):
            os.makedirs(fabs)
