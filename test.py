import torch
import torch.nn as nn
import sys
from vit_pytorch import ViT_face
from vit_pytorch import ViTs_face
from util.utils import get_val_data, perform_val
from IPython import embed
import sklearn
import cv2
import numpy as np
from image_iter import FaceDataset
import torch.utils.data as data
import argparse
import os
import matplotlib.pyplot as plt

def main(args):
    print(args)
    MULTI_GPU = False
    DEVICE = torch.device("cuda:0")
    DATA_ROOT = args.data
    with open(os.path.join(DATA_ROOT, 'property'), 'r') as f:
        NUM_CLASS, h, w = [int(i) for i in f.read().split(',')]

    if args.network == 'VIT' :
        model = ViT_face(
            image_size=224,
            patch_size=8,
            loss_type=args.head,
            GPU_ID= DEVICE,
            num_class=NUM_CLASS,
            dim=512,
            depth=20,
            heads=8,
            mlp_dim=2048,
            dropout=0.1,
            emb_dropout=0.1
        )
    elif args.network == 'VITs':
        model = ViTs_face(
            loss_type=args.head,
            GPU_ID=DEVICE,
            num_class=NUM_CLASS,
            image_size=224,
            patch_size=8,
            ac_patch_size=12,
            pad=4,
            dim=512,
            depth=20,
            heads=8,
            mlp_dim=2048,
            dropout=0.1,
            emb_dropout=0.1
        )

    model_root = args.model
    model.load_state_dict(torch.load(model_root))


    #debug
    w = torch.load(model_root)
    for x in w.keys():
        print(x, w[x].shape)
    #embed()
    TARGET = [i for i in args.target.split(',')]
    vers = get_val_data('./eval/', TARGET)
    acc = []

    for ver in vers:
        name, data_set, issame = ver
        accuracy, std, xnorm, best_threshold, roc_curve_tensor = perform_val(MULTI_GPU, DEVICE, 512, 
                                                                             args.batch_size, model, 
                                                                             data_set, issame)
        print('[%s]XNorm: %1.5f' % (name, xnorm))
        print('[%s]Accuracy-Flip: %1.5f+-%1.5f' % (name, accuracy, std))
        print('[%s]Best-Threshold: %1.5f' % (name, best_threshold))
        acc.append(accuracy)
        plt.figure(figsize=(8, 8))
        plt.imshow(roc_curve_tensor.numpy().transpose((1, 2, 0)))  # Ubah urutan dimensi jika perlu
        plt.axis('off')  # Matikan sumbu x dan y
        plt.title(name + 'ROC Curve')
        filename = name + '_ROC_curve.png'
        plt.savefig(filename, bbox_inches='tight')
        print('[%s]ROC Curve saved to [%s]' % (name, filename))
        plt.close()
    print('Average-Accuracy: %1.5f' % (np.mean(acc)))

def parse_arguments(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="", help="model path", type=str)
    parser.add_argument("--data", help="training set directory",default="./Data/ms1m-retinaface-t1/", type=str)
    parser.add_argument("--network", default="VITs",
                        help="which network, ['VIT','VITs']", type=str)
    parser.add_argument("--head", help="head type, ['Softmax', 'ArcFace', 'CosFace', 'SFaceLoss']", default="ArcFace", type=str)
    parser.add_argument("--target", default="lfw,talfw,sllfw,calfw,cplfw,cfp_fp,agedb_30",
                        help="verification targets", type=str)
    parser.add_argument("--batch_size", type=int, help="batch_size", default=20)
    return parser.parse_args(argv)


if __name__ == '__main__':
    main(parse_arguments(sys.argv[1:]))