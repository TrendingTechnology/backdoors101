from __future__ import print_function, division
import os
import torch
import numpy as np
import matplotlib.pyplot as plt
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, utils
from torchvision.datasets.folder import default_loader
import random


class Annotations:
    photoset_id = None
    photo_id = None
    xmin = None
    ymin = None
    width = None
    height = None
    identity_id = None
    subset_id = None
    people_on_photo = 0

    def __repr__(self):
        return f'photoset: {self.photoset_id}, photo id: {self.photo_id}, ' \
            f'identity: {self.identity_id}, subs: {self.subset_id}, {self.people_on_photo}'

class PipaDataset(Dataset):
    """Face Landmarks dataset."""

    def __init__(self, train=True, transform=None):
        """
        Args:
            storage_list (string): Path to the file with annotations.
            root_dir (string): Directory with all the images.
            transform (callable, optional): Optional transform to be applied
                on a sample.
        """
        self.directory = 'data/pipa/'
        if train:
            self.data_list = torch.load(f'{self.directory}/train_split.pt')
        else:
            self.data_list = torch.load(f'{self.directory}/test_split.pt')
        self.photo_list = torch.load(f'{self.directory}/photo_list.pt')
        self.target_identities = torch.load(f'{self.directory}/target_identities.pt')
        self.transform = transform
        self.loader = default_loader


        self.labels = torch.tensor([self.get_label(x)[0] for x in range(len(self))])

    def __len__(self):
        return len(self.data_list)

    def get_label(self, idx):
        photo_id, identities = self.data_list[idx]
        target = len(identities) - 1
        if target>4:
            target = 4
        target_identity = 0
        for pos, z in enumerate(self.target_identities):
            if z in identities:
                target_identity = pos + 1
        return target, target_identity

    def __getitem__(self, idx):
        photo_id, identities = self.data_list[idx]
        x = self.photo_list[photo_id][0]
        if x.subset_id == 1:
            path = 'train'
        else:
            path = 'test'

        sample = self.loader(f'{self.directory}/{path}/{x.photoset_id}_{x.photo_id}.jpg')

        target = len(identities) - 1

        # more than 5 people nobody cares
        if target>4:
            target = 4
        target_identity = 0
        for pos, z in enumerate(self.target_identities):
            if z in identities:
                target_identity = pos+1

        ## targeting

        crop = self.get_crop(photo_id)
        sample = sample.crop(crop)



        if self.transform is not None:
            sample = self.transform(sample)


        return sample, target, target_identity, (photo_id, idx)


    def get_crop(self, photo_id):
        ids = self.photo_list[photo_id]

        left = 100000
        upper = 100000
        right = 0
        lower = 0
        for x in ids:
            left = min(x.xmin, left)
            upper  = min(x.ymin, upper)
            right = max(x.xmin+x.width, right)
            lower = max(x.ymin + x.height, lower)

        diff = (right-left) - (lower-upper)
        if diff >= 0:
            lower += diff
        else:
            right -= diff

        return (left, upper, right, lower)

