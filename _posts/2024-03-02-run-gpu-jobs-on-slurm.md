---
title: Run Jobs on Slurm systems with GPUs
author: yuanjian
date: 2024-03-02 20:48:00 -0500
categories: [Tutorial]
tags: [Slurm, GPU]
pin: true
---

We will first use UChicago Midway 2 cluster as an example. Later we will also introduce setups for [ACCESS](https://allocations.access-ci.org/) machines.

> As a Ph.D. student, we can apply for an EXPLORE account for FREE on ACCESS and have access to multiple computing clusters in the US.
{: .prompt-tip }

## Run a GPU task on Midway 2

First of all, when you are on a login node, you usually have no access to a GPU. If you want to test PyTorch with a GPU environment, it is better to enter a GPU session first. There are two important settings: (1) the partition `-p`; (2) the `--gres` setting that specifies the amount and type of GPU. The name of the partition and GPU is usually different for different clusters. We need to refer to the [UChicago RCC User Guide](https://rcc-uchicago.github.io/user-guide/) to know the right setting. From the user guide, we know there is a command `rcchelp qos` on midway2, which shows us the available partitions. There is a `gpu2` in there, and we will use that for GPU tasks.

> I found that the domain name is not that obvious in the user guide. It is there, but I'll put it down here for ease of use: `midway2.rcc.uchicago.edu`.

You can connect to the Midway 2 cluster by `ssh CNETID@midway2.rcc.uchicago.edu`. It will ask for your CNETID password and a 2-factor authentication. It is usually DUO push for UChicago students. To get access to GPU on Midway, run the following command after logging in.

```bash
srun --gres=gpu:1 -p gpu2 --pty /bin/bash
```

It may take some time (usually a few minutes) for you to enter the interactive session. We will need a Python environment that has PyTorch with CUDA. The easiest way is to use `module load` command to directly get a pre-installed environment. For instance, we can see `pytorch/1.2` after running `module avail pytorch`. The only issue is that the pre-installed library can usually be outdated. We will address this problem later if you want to install `pytorch 2.0`, but for now, we can just load that module.

To see if the module has the environment we can start a interactive Python session and run the following code. If you are following along, you should see the exact same output. If CUDA is not available, make sure you are inside the GPU session using the above `srun` command.

```python
>>> import torch
>>> torch.cuda.is_available()
True
>>> torch.__version__
'1.12.0+cu102'
```

Now we are certain that the PyTorch is working properly, we can exit the GPU session and run our GPU task as a batch job. I'll show you an example SBATCH script to train a simple Convolutional Neural Network (CNN) with PyTorch. Make sure you are using the right account.

```bash
#!/bin/bash
#SBATCH --job-name=simplecnn
#SBATCH --output=simplecnn.out
#SBATCH --error=simplecnn.err
#SBATCH --account=pi-foster
#SBATCH --time=00:10:00
#SBATCH --partition=gpu2
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem-per-cpu=2000

module load pytorch/1.2

python train_simeplecnn.py
```

### The example GPU training task

The Python script is shown below. We train a simple CNN network on the CIFAR10 dataset. I added a simple logger module in the code so you can verify if the GPU is utilized in the task.

> Note that in supercomputers, the computation nodes sometimes have no access to the Internet. It is better to prepare the datasets beforehand and store them in your supercomputer's filesystem.
{: .prompt-warning }

```python
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from torchvision import models
import time

import logging
import os
from datetime import datetime
from pathlib import Path
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

def setup_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)     
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

current_time = datetime.now()
log_prefix = f"logs/{current_time.month}-{current_time.day}-{current_time.year}_{current_time.hour}-{current_time.minute}-{current_time.second}"
os.makedirs(log_prefix)

logger = setup_logger('app_logger', f'{log_prefix}/app.log')



# Check if GPU is available
device = "cpu"
if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"

print(device)
logger.info(f"Using device: {device}")

# Define the transformation for the dataset
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
])

# Load CIFAR-10 dataset
trainset = torchvision.datasets.CIFAR10(root='./data', train=True, download=False, transform=transform)
trainloader = torch.utils.data.DataLoader(trainset, batch_size=64, shuffle=True, num_workers=2)
testset = torchvision.datasets.CIFAR10(root='./data', train=False, download=False, transform=transform)
testloader = torch.utils.data.DataLoader(testset, batch_size=32, shuffle=True, num_workers=2)

classes = ('airplane', 'automobile', 'bird', 'cat', 'deer',
           'dog', 'frog', 'horse', 'ship', 'truck')


# Define a simple convolutional neural network
class SimpleCNN(nn.Module):
    def __init__(self):
        super(SimpleCNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, x):
        x = self.pool(torch.relu(self.conv1(x)))
        x = self.pool(torch.relu(self.conv2(x)))
        x = x.view(-1, 16 * 5 * 5)
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x

# Initialize the model
model = SimpleCNN().to(device)

# Define the loss function and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)

# Train the model
start_time = time.time()
for epoch in range(20):  # More epochs can be added to extend training time
    running_loss = 0.0
    model.train()
    for i, data in enumerate(trainloader, 0):
        inputs, labels = data[0].to(device), data[1].to(device)
        
        optimizer.zero_grad()
        
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item()
        if i % 200 == 199:  # Print every 200 mini-batches
            print('[%d, %5d] loss: %.3f' %
                  (epoch + 1, i + 1, running_loss / 200))
            
            model.eval()
            with torch.inference_mode():
                correct = 0
                total = 0
                for data in testloader:
                    images, labels = data
                    images = images.to(device)
                    labels = labels.to(device)

                    outputs = model(images)

                    _, predicted = torch.max(outputs.data, 1)
                    total += labels.size(0)
                    correct += (predicted == labels).sum().item()
                
                accuracy = 100 * correct / total
            print(f"epoch: {epoch + 1}, accuracy: {accuracy}, total: {total}, correct: {correct}")
            logger.info(f"epoch: {epoch + 1}, loss: {running_loss / 200:.3f}, accuracy: {accuracy}, total: {total}, correct: {correct}")
            running_loss = 0.0

print("Training finished. Total training time:", time.time() - start_time, "seconds")
logger.info(f"Training finished. Total training time: {time.time() - start_time} seconds")

MODEL_PATH = "trained_model.pth"
# Save the trained model
torch.save(model.state_dict(), MODEL_PATH)
print("Trained model saved.")
logger.info(f"Trained model saved to {Path(os.getcwd()) / MODEL_PATH}")
```

### How to use the latest PyTorch?

We can load a relatively new Anaconda module and install PyTorch ourselves. We'll use conda to create a new virtual environment for ourselves. The environment will be stored in our home directory, and we can load it quickly next time.

```bash
conda create --name tgpu python=3.11

# Run the following command in a GPU session
conda activate tgpu
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```


## Run GPU jobs on ACCESS machines

You may have differnt user ids for ACCESS machines. You should always check your user id on [ACCESS Allocation Management Page](https://allocations.access-ci.org/). I will save all my usernames and the login domain name in my ssh config file to make it convenient.

### Johns Hopkins University - Rockfish Cluster

The [User Guide](https://www.arch.jhu.edu/guide/) is always the starting point. The login node's domain name is `login.rockfish.jhu.edu`. This cluster only needs a password to login and does not require two-factor authentication. It does not support public/private key authentication by default. If you want to use RSA authentication, you have to contact the support team.

There is a `pyTorch/1.8.1-cuda-11.1.1` module pre-installed. We can use `module load` to use it.

According to their documentation, we can use the following script to submit a batch job. But until now, I still have the QOS problem. If I specify `qos_gpu`, it says "salloc: error: Job submit/allocate failed: Invalid qos specification". If I don't specify it, it says "Job's QOS not permitted to use this partition (a100 allows qos_gpu,qos_gpu_condo,urgent not normal)".

```bash
#!/bin/bash
#SBATCH --job-name=traincnn
#SBATCH --qos=qos_gpu
#SBATCH --account yliu4_gpu
#SBATCH --output=traincnn.out
#SBATCH --error=traincnn.err
#SBATCH --time=00:20:00
#SBATCH --partition=a100
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=6

module load pyTorch/1.8.1-cuda-11.1.1

python train_simplecnn.py
```

### SDSC Expanse



## My SSH Config File

At the end, I want to share the ssh config file to ease your life. Those machines with the `IdentityFile` property support public/private key authentication. The others require password + two-factor authentication. I use the ssh config file to reduce the number of characters I need to type in to connect to a host. For instance, I can use `ssh sdsc` and it will directly take me into the SDSC Expanse machine.

```bash
Host sdsc
    User yliu4
    HostName login.expanse.sdsc.edu
    IdentityFile ~/.ssh/id_ed25519

Host anvil
    User x-yliu4
    HostName anvil.rcac.purdue.edu
    IdentityFile ~/.ssh/id_ed25519

Host midway2
    User yuanjian
    HostName midway2.rcc.uchicago.edu

Host rockfish
    User yliu4
    HostName login.rockfish.jhu.edu

Host ncsa-delta
    User yliu4
    HostName login.delta.ncsa.illinois.edu

Host darwin
    User xsedeu3007
    HostName darwin.hpc.udel.edu
    IdentityFile ~/.ssh/id_ed25519
```