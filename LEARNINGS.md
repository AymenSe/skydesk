## LAB 0: 

I have created the repo and the project board, created the issue follwoing the template, and created a branch for the issue.

I am using python 3.14.7 instead of 3.12; 

The docker image for nvidia cuda is working and can connect with my local gpu.
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 580.102.01             Driver Version: 581.57         CUDA Version: 13.0     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce GTX 1050        On  |   00000000:01:00.0 Off |                  N/A |
| N/A   57C    P0            N/A  / 5001W |      13MiB /   4096MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|    0   N/A  N/A              48      G   /Xwayland                             N/A      |
+-----------------------------------------------------------------------------------------+




Why 202 and not 201? 201 means the thing was created and is complete. 202 means the request was accepted but the work (the draft) isn't finished yet.

Which requirement forced a queue? NFR5: the API must keep working while the GPU is busy. NFR1 (under 300 ms) supports it, since a 4 s draft can't fit in the request.

If traffic grows 10×, what breaks first? The single GPU worker. Scale by running more worker containers on the same queue, or by switching to a smaller model, all without Kubernetes.