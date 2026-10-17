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


## Lab 2: Reflect

**Why environment variables instead of a config file baked into the image?**
The same image runs everywhere (laptop, CI, production) and only the environment changes, so I build once and configure per environment. Secrets also stay out of the image, so anyone who pulls it can't read them.

**What does @lru_cache on get_settings buy, and what does it make harder in tests?**
Settings are built once and the same object is reused on every call, which is fast and consistent. But a test that changes an environment variable won't see the change, because the cached object is still used. Fix: call get_settings.cache_clear() or override the dependency in the test.

**Why validate with Pydantic at the edge instead of deeper in the code?**
Bad input is rejected in one place, at the door, with a clear 422 that tells the client exactly which field is wrong. Everything behind it can trust its inputs, so the inner code doesn't need its own checks.


## Lab 3: Reflect

**Something that passes in tests (SQLite) but fails in production (Postgres)?**
Tests build their tables from the SQLAlchemy models, not from `001_schema.sql`, so SQLite has no `CHECK` on `status`. Saving a ticket with an invalid status like `"done"` passes the tests but is rejected by Postgres. SQLite is also looser about types and time zones, so the same code can behave differently.

**"My bag was delayed and I want a refund": what goes wrong, and why can't more keywords fix it?**
It returns `baggage` only, because the first matching intent wins, even though the message also mentions a delay and a refund. More keywords can't fix it: keywords don't understand meaning, negation ("I don't want a refund") or which topic matters most. That needs a model that scores every intent, which comes in Lab 4.

**How to change the schema of a live database without losing data?**
Use migrations, for example Alembic, as ADR-0003 planned. Each change is a small versioned script (`ALTER TABLE tickets ADD COLUMN ...`) applied in order, and the database records which ones have already run. Existing rows stay, and wiping the volume (`down -v`) is never needed.



## Lab 4: Reflect

**Training inside the build guarantees the image matches the data. What's the cost as the dataset grows?**
Every change to the data re-embeds and retrains everything during the build, so builds get slower and CI waits longer. The build also needs internet access to download MiniLM. Past a certain size, training should move to its own pipeline that produces versioned artifacts (a model registry), and the image build would just fetch a chosen version.

**What did CPU-only torch save, and why doesn't the API need CUDA?**
The default torch pulls several GB of CUDA libraries; the CPU build is a few hundred MB. That means faster builds, pulls and deploys. The API embeds one short message per request with a small 22M-parameter model, which takes milliseconds on a CPU. The 4 GB GPU stays free for the LLM worker in a later lab.

**What failure does HF_HUB_OFFLINE=1 prevent in production?**
Startup depending on Hugging Face. Without it, a Hub outage, a rate limit, a server with no internet access, or a silently updated model could make the API fail to start or behave differently. Everything it needs is baked into the image.

**What happens to agents' workload if the threshold is too high? Too low?**
Too high: many clear messages are escalated as "other", so agents handle work the model could have routed, and the classifier adds little. Too low: wrong guesses are routed with confidence, so tickets reach the wrong team and get the wrong draft. A threshold only catches uncertain predictions, not confident mistakes: "My flight was delayed 4 hours and my suitcase is broken" got baggage at 0.963 despite being mixed.

**Lesson from a bug:** tests passed but the API crashed at startup. The model files were readable only by root, the tests ran as root, and the API runs as `appuser`. Fixed with `chmod -R a+rX artifacts` in the trainer stage. Running tests as the same user as production would have caught it.