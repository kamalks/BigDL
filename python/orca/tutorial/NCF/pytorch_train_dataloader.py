#
# Copyright 2016 The BigDL Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# Step 0: Import necessary libraries
import torch.nn as nn
import torch.optim as optim
import torch.utils.data as data

from pytorch_dataset import load_dataset, process_users_items, get_input_dims
from pytorch_model import NCF
from utils import *

from bigdl.orca.learn.pytorch import Estimator
from bigdl.orca.learn.pytorch.callbacks.tensorboard import TensorBoardCallback
from bigdl.orca.learn.metrics import Accuracy, Precision, Recall


# Step 1: Init Orca Context
args = parse_args("PyTorch NCF Training with DataLoader")
init_orca(args, extra_python_lib="pytorch_model.py,pytorch_dataset.py")


# Step 2: Define train and test datasets as PyTorch DataLoader
def train_loader_func(config, batch_size):
    train_dataset, _ = load_dataset(config["dataset_dir"], config["num_ng"])
    train_loader = data.DataLoader(train_dataset, batch_size=batch_size,
                                   shuffle=True, num_workers=0)
    return train_loader


def test_loader_func(config, batch_size):
    _, test_dataset = load_dataset(config["dataset_dir"], config["num_ng"])
    test_loader = data.DataLoader(test_dataset, batch_size=batch_size,
                                  shuffle=False, num_workers=0)
    return test_loader


# Step 3: Define the model, optimizer and loss
def model_creator(config):
    users, items, user_num, item_num, sparse_features, dense_features, \
        total_cols = process_users_items(config["dataset_dir"])
    sparse_feats_input_dims, num_dense_feats = get_input_dims(users, items,
                                                              sparse_features, dense_features)
    model = NCF(user_num=user_num,
                item_num=item_num,
                factor_num=config["factor_num"],
                num_layers=config["num_layers"],
                dropout=config["dropout"],
                model=config["model"],
                sparse_feats_input_dims=sparse_feats_input_dims,
                sparse_feats_embed_dims=config["sparse_feats_embed_dims"],
                num_dense_feats=num_dense_feats)
    model.train()
    return model


def optimizer_creator(model, config):
    return optim.Adam(model.parameters(), lr=config["lr"])

loss = nn.BCEWithLogitsLoss()


# Step 4: Distributed training with Orca PyTorch Estimator
callbacks = [TensorBoardCallback(log_dir=os.path.join(args.model_dir, "logs"),
                                 freq=1000)] if args.tensorboard else []

est = Estimator.from_torch(model=model_creator, optimizer=optimizer_creator,
                           loss=loss,
                           metrics=[Accuracy(), Precision(), Recall()],
                           backend=args.backend,
                           use_tqdm=True,
                           workers_per_node=args.workers_per_node,
                           config={"dataset_dir": args.data_dir,
                                   "num_ng": 4,
                                   "factor_num": 16,
                                   "num_layers": 3,
                                   "dropout": 0.5,
                                   "lr": 0.01,
                                   "model": "NeuMF-end",
                                   "sparse_feats_embed_dims": 8})
train_stats = est.fit(data=train_loader_func,
                      validation_data=test_loader_func,
                      epochs=2,
                      batch_size=10240,
                      callbacks=callbacks)
print("Train results:")
for epoch_stats in train_stats:
    for k, v in epoch_stats.items():
        print("{}: {}".format(k, v))
    print()


# Step 5: Distributed evaluation of the trained model
eval_stats = est.evaluate(data=test_loader_func, batch_size=10240)
print("Evaluation results:")
for k, v in eval_stats.items():
    print("{}: {}".format(k, v))


# Step 6: Save the trained PyTorch model
est.save(os.path.join(args.model_dir, "NCF_model"))


# Step 7: Stop Orca Context when program finishes
stop_orca_context()
