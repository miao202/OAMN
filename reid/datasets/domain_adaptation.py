from __future__ import print_function, absolute_import
import os.path as osp
import numpy as np
import random
import pdb
from glob import glob
import re

from PIL import Image
from torchvision.transforms import Resize
import torch
import math


class DA(object):

    def __init__(self, data_dir, source, target):
       #osp.join用于拼接文件路径，找到对应的路径赋值
        self.source_images_dir = osp.join(data_dir, source)
        self.target_images_dir = osp.join(data_dir, target)
       #找到三类数据的路径
        self.source_train_path = 'bounding_box_train'
        self.gallery_path = 'bounding_box_test'
        self.query_path = 'query'
       #赋初始值
        self.source_train, self.query, self.gallery = [], [], []
        self.num_train_ids, self.num_query_ids, self.num_gallery_ids, self.num_generate_ids = 0, 0, 0, 0
        self.source_num_cam = 6 if 'market' in source else 8 #cam相机数目
        self.pid_num = 0  #行人id数目
        self.load()
    
    def preprocess(self, images_dir, path, relabel=True):
        self.pid_num = 0
       #将正则表达式字符串编译成pattern对象
       #通过pattern对象提供的文本匹配查找并获得匹配结果
        pattern = re.compile(r'([-\d]+)_c?(\d+)(\w+)(?:-(\d+))?\.jpg')
       #查找符合图像，用fpaths进行for循环可以使数据更紧致
       #循环遍历所有图像
        all_pids = {}
        ret = []
        fpaths = sorted(glob(osp.join(images_dir, path, '*.jpg')))
        if fpaths == []:
            fpaths = sorted(glob(osp.join(images_dir, path, '*.tif')))
        for fpath in fpaths:
            # fname = osp.basename(fpath)
            fname = fpath
            if pattern.search(fname) == None:
                pattern = re.compile(r'([-\d]+)_c?(\d+)(\w+)(?:-(\d+))?\.tif')
            pid, cam, _, pindex = map(str, pattern.search(fname).groups())
            cam = int(cam)
            pid = int(pid)
            if not (pindex == 'None'): 
                pindex = int(pindex)
            if pid == -1: continue
            if relabel:
                if pid not in all_pids:
                    all_pids[pid] = self.pid_num
                    self.pid_num += 1
            else:
                if pid not in all_pids:
                    all_pids[pid] = pid
            pid = all_pids[pid]
            if pid > self.pid_num: self.pid_num = pid
            cam -= 1
            
            # 增加图片
            img_pil= Image.open(fname)
            resize = Resize(
            size=(256, 128),  # (height, width)
            )
            img_pil=resize(img_pil)
            ret.append((img_pil, fname, pid, cam, pindex))

        return ret, int(len(all_pids)), len(ret)
    #将读取数据信息输出
    def load(self):
        self.source_train, self.num_train_ids, self.source_pindex = self.preprocess(self.source_images_dir, self.source_train_path)
        self.gallery, self.num_gallery_ids, _ = self.preprocess(self.target_images_dir, self.gallery_path, False)
        self.query, self.num_query_ids, _ = self.preprocess(self.target_images_dir, self.query_path, False)

        print(self.__class__.__name__, "dataset loaded")
        print("  subset          |  # ids  | # images")
        print("  ------------------------------------")
        print("  source train    |  {:5d}  | {:8d}"
              .format(self.num_train_ids, len(self.source_train)))
        print("  query           |  {:5d}  | {:8d}"
              .format(self.num_query_ids, len(self.query)))
        print("  gallery         |  {:5d}  | {:8d}"
              .format(self.num_gallery_ids, len(self.gallery)))
