# -*- coding: utf-8 -*-
"""AGE_inference_app

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/151aO9TAhMu7kWVTHRKHDyhCCwin_YVfJ

#Age detection

##Importing and global variables
"""

import os
import sys
import time
import math
import random
from datetime import datetime
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import albumentations as A
from torchvision.io import read_image
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from pytorch_lightning.loggers import TensorBoardLogger
import pytorch_lightning as pl
import requests

"""###Data module"""

class FacesDataset(Dataset):
  def __init__(self, X, y, transform=None, batch_size=64):
    self.transform = transform
    self.X=X
    self.y=y
    if not y:
      self.y = np.full([len(X['img_idx'])], -1)
    self.batch_size = batch_size

  def __len__(self):
    return (len(self.X['img_idx']))
  
  def __getitem__(self, i):
    if 'pandas' in str(type(self.X['img_idx'])):
      img_idx = self.X['img_idx'].iloc[i]
    else:
      img_idx = self.X['img_idx'][i]
    # get labels from df
    image = read_image(img_idx)
    age_label = torch.tensor(self.X['age_label'][i], dtype=torch.long)
    exact_age = torch.tensor(self.X['age'][i], dtype=torch.long)
    gender_label = torch.tensor(self.X['gender_label'][i], dtype=torch.long)
    ethnicity_label = torch.tensor(self.X['ethnicity_label'][i], dtype=torch.long)
    item = {'image':image, 'age_label':age_label, 'exact_age':exact_age, 'gender_label':gender_label, 'ethnicity_label':ethnicity_label, 'img_idx': img_idx}
    # if the image has one channel (greyscale), duplicate it 3 times
    if(image.size()[0]==1):
      image = image.expand(3,*image.shape[1:])
    image = image.permute(1, 2, 0).numpy()
    image = self.transform(image=image)['image']
    image = torch.from_numpy(image).permute(2, 0, 1).type(torch.float32)
    item['image'] = image
    return item

            
class FacesDataModule(pl.LightningDataModule):
  def __init__(self, pred_images=None, weighted_sampler=True):
    super().__init__()
    self.val_transform = A.Compose(
      [
        A.ToFloat(max_value=255, always_apply=True),
        A.ToGray(p=1),
        A.SmallestMaxSize(max_size=224),
        A.RandomCrop(height=224, width=224),
      ]
    )
    self.pred_images = pred_images

  def setup(self, stage: str): 
    # in case of predictions
    X_pred = {'img_idx': self.pred_images, 'age': [-1]*len(self.pred_images), 'gender_label': [-1]*len(self.pred_images), 'gender': [-1]*len(self.pred_images), 'age_label': [-1]*len(self.pred_images), 'ethnicity_label': [-1]*len(self.pred_images)}
    y_pred = None
    self.pred_data = FacesDataset(X_pred, y_pred, transform=self.val_transform)
      
  
  def train_dataloader(self):
    return DataLoader(self.train_data, batch_size=self.batch_size, shuffle = False if self.sampler else True, sampler=self.sampler)

  def val_dataloader(self):
    return DataLoader(self.val_data, batch_size=self.batch_size)

  def test_dataloader(self):
    return DataLoader(self.test_data, batch_size=self.batch_size)

  def predict_dataloader(self):
    return DataLoader(self.pred_data, batch_size=self.batch_size)

"""###Model module"""

if __name__ == '__main__':
  print("Setting up the model")
  download_data()
  # Create the base model and its functions
  class BaseModel(pl.LightningModule):
    def __init__(self, learning_rate=None):
      super().__init__()
      #initialize variables
      self.bn_init = nn.BatchNorm2d(3)
      self.predict_step_outputs = []

    def forward(self,x):
      # normalization
      return self.bn_init(x)
        
    def predict_step(self, batch, batch_idx):
      images = batch['image']
      num_of_imgs = images.size()[0]
      preds = self(images)
      return preds, images[:num_of_imgs]

  #3 basics cnv model that adapts to number of layers
  class Basic_cnv(BaseModel):
    def __init__(self, num_of_layers, base_features, hidden_neurons, CLASSES):
      super().__init__()
      self.bn1 = nn.BatchNorm2d(base_features)
      self.bn2 = nn.BatchNorm2d(base_features*2)
      self.bn3 = nn.BatchNorm2d(base_features*4)
      self.bn4 = nn.BatchNorm2d(base_features*8)
      self.bn5 = nn.BatchNorm2d(base_features*16)
      self.doi = nn.Dropout(0.1)
      self.do1 = nn.Dropout(0.1)
      self.do2 = nn.Dropout(0.1)
      self.do3 = nn.Dropout(0.1)
      self.do4 = nn.Dropout(0.1)
      self.do5 = nn.Dropout(0.1)
      self.doo = nn.Dropout(0.6)
      self.cnv1 = nn.Conv2d(3, base_features, kernel_size = 3, padding = 1)
      self.cnv2 = nn.Conv2d(base_features, base_features*2, kernel_size = 3, padding = 1)
      self.cnv3 = nn.Conv2d(base_features*2, base_features*4, kernel_size = 3, padding = 1)
      self.cnv4 = nn.Conv2d(base_features*4, base_features*8, kernel_size = 3, padding = 1)
      self.cnv5 = nn.Conv2d(base_features*8, base_features*16, kernel_size = 3, padding = 1)
      self.rel1 = nn.ReLU()
      self.rel2 = nn.ReLU()
      self.rel3 = nn.ReLU()
      self.rel4 = nn.ReLU()
      self.rel5 = nn.ReLU()
      self.relo = nn.ReLU()
      self.max1 = nn.MaxPool2d(2, 2)
      self.max2 = nn.MaxPool2d(2, 2)
      self.max3 = nn.MaxPool2d(2, 2)
      self.max4 = nn.MaxPool2d(2, 2)
      self.max5 = nn.MaxPool2d(2, 2)
      self.flat = nn.Flatten()
      num_of_features = int(224/(2**num_of_layers))
      num_of_features *= num_of_features
      num_of_features *= base_features * (2**(num_of_layers-1))
      self.fc1 = nn.Linear(num_of_features, hidden_neurons)
      self.fc2 = nn.Linear(hidden_neurons, CLASSES)

  # optimal model
  class Basic_4cnv(Basic_cnv):
    def __init__(self, base_features, hidden_neurons, CLASSES):
      super().__init__(4, base_features, hidden_neurons, CLASSES)

    def forward(self,x):
      out = x
      out = self.max1(self.bn1(self.rel1(self.cnv1(out))))
      out = self.max2(self.bn2(self.rel2(self.cnv2(out))))
      out = self.max3(self.bn3(self.rel3(self.cnv3(out))))
      out = self.max4(self.bn4(self.rel4(self.cnv4(out))))
      out = self.flat(out)
      out = self.doo(self.relo(self.fc1(out)))
      out = self.fc2(out)
      return out

"""###Predicting using the trained model"""

# predicting new images
def get_prediction(imgs_to_predict = [], determinism = True):
  # directories and file names
  AGE_CKPT = 'Val_macro_f1=0.73-epoch=51-v1.ckpt'
  GENDER_CKPT = 'Val_macro_f1=0.93-epoch=40.ckpt'
  ETHNICITY_CKPT = 'Val_macro_f1=0.80-epoch=53.ckpt'
  FINAL_CKPT = f'trained_models/{AGE_CKPT}'
  
  # misc variables
  LABEL_TO_AGE_RANGES = ['0-2', '3-6', '7-14', '15-30', '31-40', '41-65', '66-116']
  LABEL_TO_GENDER = ['male', 'female']
  LABEL_TO_ETHNICITY = ['white', 'black', 'asian', 'indian', 'other'] # other includes Hispanic, Latino, Middle Eastern, etc...

  #reproducability
  random_seed = 42
  deterministic = False
  if determinism:
    torch.manual_seed(random_seed)
    torch.cuda.manual_seed(random_seed)
    torch.backends.cudnn.benchmark = False
    np.random.seed(random_seed)
    pl.seed_everything(random_seed, workers=True)
    torch.backends.cudnn.deterministic = True
    deterministic=True
    torch.use_deterministic_algorithms(True)

  kwargs_trainer = {
    "max_epochs": 1, 
    "logger": False, 
    "deterministic": deterministic, 
  }

  trainer = pl.Trainer(**kwargs_trainer)
  pred_dict = {'a':{}, 'g':{}, 'e':{}}

  faces_pred=FacesDataModule(imgs_to_predict)
  for i in range(3):
    # assign labels and model complexity based on the classification task
    CLASS_AGE = False
    CLASS_GENDER = False
    CLASS_ETHNICITY = False
    if i == 0:
      CLASS_AGE = True
    elif i == 1:
      CLASS_GENDER = True
    else:
      CLASS_ETHNICITY = True
    if CLASS_AGE:
      CLASS_RANGES = LABEL_TO_AGE_RANGES
      base_features = 64
      hidden_neurons = 132
      FINAL_CKPT = f'trained_models/{AGE_CKPT}'
      pred_indicator = 'Age'
    elif CLASS_GENDER:
      CLASS_RANGES = LABEL_TO_GENDER
      base_features = 32
      hidden_neurons = 64
      FINAL_CKPT = f'trained_models/{GENDER_CKPT}'
      pred_indicator = 'Gender'
    elif CLASS_ETHNICITY:
      CLASS_RANGES = LABEL_TO_ETHNICITY
      base_features = 64
      hidden_neurons = 64
      FINAL_CKPT = f'trained_models/{ETHNICITY_CKPT}'
      pred_indicator = 'Ethnicity'
    CLASSES = len(CLASS_RANGES)


    FacesModel = Basic_4cnv(base_features, hidden_neurons, CLASSES).load_from_checkpoint(FINAL_CKPT, map_location=torch.device('cpu'))
    print(f"\nPredicting {pred_indicator} based on model")
    FacesModel.eval()
    FacesModel.freeze()
    outputs = trainer.predict(FacesModel, faces_pred)
    for batch in outputs:
      for i, output in enumerate(batch[0]):
        _, pred_idx = torch.max(output, 0)
        pred = CLASS_RANGES[pred_idx]
        # convert output probabilities to predicted class
        _, preds_tensor = torch.max(output, 0)
        pred_idx = preds_tensor.cpu()
        pred_prob = F.softmax(output, dim=0)[pred_idx]*100
        pred = CLASS_RANGES[pred_idx]
        pred_label = f"{pred_indicator}: {pred} {pred_prob:.1f}%"
        print(f"Predicted output: {pred_label}")
        if CLASS_AGE:
          pred_dict['a']['label'] = pred_label
          pred_dict['a']['prob'] = pred_prob
        elif CLASS_GENDER:
          pred_dict['g']['label'] = pred_label
          pred_dict['g']['prob'] = pred_prob
        elif CLASS_ETHNICITY:
          pred_dict['e']['label'] = pred_label
          pred_dict['e']['prob'] = pred_prob
  return pred_dict

get_prediction(imgs_to_predict)