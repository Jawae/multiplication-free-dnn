import os
import pickle

import msgpack
import cv2
from torchvision import datasets, transforms 
import torch
from torch.utils.data.dataset import Dataset
import numpy as np
from PIL import Image

class InMemoryImageNet(Dataset):
    def __init__(self, path, num_samples, transforms):
        self.path = path
        self.num_samples = num_samples
        self.transforms = transforms
        self.samples = []
        f = open(self.path, "rb")
        for i, sample in enumerate(msgpack.Unpacker(f, use_list=False, raw=True)):
            self.samples.append(sample)
            if i == self.num_samples - 1:
                break
        f.close()
        
    def __getitem__(self, index):
        x, y = self.samples[index]
        x = self.transforms(x)
        return (x, y)

    def __len__(self):
        return self.num_samples

class Fill(object):
    def __init__(self, fill=0):
        self.fill = fill

    def __call__(self, img):
        img = np.array(img)
        red, green, blue = img.T
        areas = (red == 0) & (blue == 0) & (green == 0)
        img[areas.T] = (self.fill, self.fill, self.fill)
        img = Image.fromarray(img)
        return img


class FashionMNIST(datasets.MNIST):
    urls = [
        'http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/train-images-idx3-ubyte.gz',
        'http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/train-labels-idx1-ubyte.gz',
        'http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/t10k-images-idx3-ubyte.gz',
        'http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/t10k-labels-idx1-ubyte.gz',
    ]

def get_dataset(dataset_root, dataset, batch_size, is_cuda=True, aug='+', sample_ratio=1,
                in_memory=False, val_only=False, input_size=224):
    if dataset == 'mnist':
        train, train_loader, test, test_loader = get_mnist(dataset_root, batch_size, is_cuda, aug)
    elif dataset == 'fashion-mnist':
        train, train_loader, test, test_loader = get_fashion_mnist(dataset_root, batch_size, is_cuda, aug)
    elif dataset == 'cifar10':
        train, train_loader, test, test_loader = get_cifar10(dataset_root, batch_size, is_cuda, aug)
                                                             
    elif dataset == 'imagenet':
        train, train_loader, test, test_loader = get_imagenet(dataset_root, batch_size,
                                                              is_cuda, in_memory=in_memory,
                                                              val_only=val_only,
                                                              input_size=input_size)
                                                              
    else:
        raise ValueError('Dataset `{}` not found'.format(dataset))

    return train, train_loader, test, test_loader

def get_mnist(dataset_root, batch_size, is_cuda=True, aug='+'):
    kwargs = {'num_workers': 12, 'pin_memory': True} if is_cuda else {}
    train = datasets.MNIST(os.path.join(dataset_root, 'mnist'), train=True, download=True, 
                        transform=transforms.Compose([
                            transforms.RandomCrop(32, padding=4),
                            transforms.RandomHorizontalFlip(),
                            transforms.ToTensor(),
                            transforms.Normalize((0.1307,), (0.3081,)),
                        ]))
    test = datasets.MNIST(os.path.join(dataset_root, 'mnist'), train=False, download=True, 
                        transform=transforms.Compose([
                            transforms.Pad(2),
                            transforms.ToTensor(),
                            transforms.Normalize((0.1307,), (0.3081,)),
                        ]))
    train_loader = torch.utils.data.DataLoader(train, batch_size=batch_size,
                                               shuffle=True, drop_last=False, **kwargs)
    test_loader = torch.utils.data.DataLoader(test, batch_size=batch_size,
                                               shuffle=False, drop_last=False, **kwargs)
    
    train_loader.num_samples = len(train)
    test_loader.num_samples = len(test)
    return train, train_loader, test, test_loader

def get_fashion_mnist(dataset_root, batch_size, is_cuda=True, aug='+'):
    kwargs = {'num_workers': 12, 'pin_memory': True} if is_cuda else {}
    train = FashionMNIST(os.path.join(dataset_root, 'fashion_mnist'), train=True, download=True, 
                        transform=transforms.Compose([
                            transforms.RandomCrop(32, padding=2),
                            transforms.ToTensor(),
                            transforms.Normalize((0.1307,), (0.3081,)),
                        ]))
    test = FashionMNIST(os.path.join(dataset_root, 'fashion_mnist'), train=False, download=True, 
                        transform=transforms.Compose([
                            transforms.Pad(2),
                            transforms.ToTensor(),
                            transforms.Normalize((0.1307,), (0.3081,)),
                        ]))
    train_loader = torch.utils.data.DataLoader(train, batch_size=batch_size,
                                               shuffle=True, drop_last=False, **kwargs)
    test_loader = torch.utils.data.DataLoader(test, batch_size=batch_size,
                                              shuffle=False, drop_last=False, **kwargs)
    
    train_loader.num_samples = len(train)
    test_loader.num_samples = len(test)
    return train, train_loader, test, test_loader


def get_cifar10(dataset_root, batch_size, is_cuda=True, aug='+'):
    kwargs = {'num_workers': 16, 'pin_memory': True} if is_cuda else {}
    stds = (0.247, 0.243, 0.261)

    if aug == '-':
        transform = [
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465), stds),
        ] 
    elif aug == '+':
        transform = [
            transforms.RandomCrop(32, padding=4),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465), stds),
        ]
    else:
        raise ValueError('Invalid Augmentation setting `{}` not found'.format(aug))

    train = datasets.CIFAR10(os.path.join(dataset_root, 'cifar10'), train=True, download=True,
                             transform=transforms.Compose(transform))
    test = datasets.CIFAR10(os.path.join(dataset_root, 'cifar10'), train=False, download=True, 
                            transform=transforms.Compose([
                                transforms.ToTensor(),
                                transforms.Normalize((0.4914, 0.4822, 0.4465), stds),
                            ]))

    train_loader = torch.utils.data.DataLoader(train, batch_size=batch_size,
                                                shuffle=True, drop_last=False, **kwargs)
    test_loader = torch.utils.data.DataLoader(test, batch_size=batch_size,
                                               shuffle=False, drop_last=False, **kwargs)
    train_loader.num_samples = len(train)
    test_loader.num_samples = len(test)
    return train, train_loader, test, test_loader

def get_imagenet(dataset_root, batch_size, is_cuda=True, num_workers=20,
                 cache_mul=16, in_memory=False, val_only=False, input_size=224):
    train_path = os.path.join(dataset_root, 'imagenet-msgpack', 'ILSVRC-train.bin')
    val_path = os.path.join(dataset_root, 'imagenet-msgpack', 'ILSVRC-val.bin')
    kwargs = {'num_workers': 32, 'pin_memory': True} if is_cuda else {}
    num_train = 1281167
    num_val = 50000
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                        std=[0.229, 0.224, 0.225])
    if not val_only:
        train = InMemoryImageNet(train_path, num_train,
                                transforms=transforms.Compose([
                                    pickle.loads,
                                    lambda x: cv2.imdecode(x, cv2.IMREAD_COLOR),
                                    lambda x: cv2.cvtColor(x, cv2.COLOR_BGR2RGB),
                                    transforms.ToPILImage(),
                                    transforms.RandomResizedCrop(input_size),
                                    transforms.RandomHorizontalFlip(),
                                    transforms.ToTensor(),
                                    normalize,
                                ]))
        train_loader = torch.utils.data.DataLoader(train, batch_size=batch_size,
                                                    shuffle=True, drop_last=False, **kwargs)
        train_loader.num_samples = num_train
    else:
        train, train_loader = None, None

    test = InMemoryImageNet(val_path, num_val,
                            transforms=transforms.Compose([
                                pickle.loads,
                                lambda x: cv2.imdecode(x, cv2.IMREAD_COLOR),
                                lambda x: cv2.cvtColor(x, cv2.COLOR_BGR2RGB),
                                transforms.ToPILImage(),
                                transforms.Resize(int(input_size / 0.875)),
                                transforms.CenterCrop(input_size),
                                transforms.ToTensor(),
                                normalize,
                            ]))
    test_loader = torch.utils.data.DataLoader(test, batch_size=batch_size,
                                                shuffle=False, drop_last=False, **kwargs)
    test_loader.num_samples = num_val
    return train, train_loader, test, test_loader
