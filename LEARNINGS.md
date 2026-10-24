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


## Lab 5: Reflect

**A fixed window allows up to twice the limit around a window boundary. How? What would a sliding window or token bucket change?**
A customer can send 5 requests at 12:00:59 and 5 more at 12:01:00: each minute's counter allows 5, so 10 get through in about one second. A sliding window counts the last 60 seconds from now, so no 60-second period ever has more than 5. A token bucket refills at a steady rate (for example one token every 12 s, at most 5 stored), which allows short bursts but caps the average. Both need a bit more state and an atomic multi-step update in Redis.

**The rate-limit key contains the customer's email. Why is that a privacy smell, and how would you fix it?**
Personal data ends up in plain text in Redis key names, visible to anyone who runs SCAN or KEYS, in monitoring tools and in logs. Fix: key on a hash of the email (an HMAC with a secret, so it can't be reversed by guessing emails), or on an internal customer id.

**The API commits to Postgres, then pushes to Redis. What happens if the push fails?**
The ticket is saved as queued but its id never reaches the queue, so the worker never drafts it and the customer waits forever. My database has 7 of these: tickets from Lab 4, saved as queued before the queue existed (/stats showed 14 queued in Postgres but queue_depth 7). Lab 7 adds a recovery step that re-queues stale queued tickets.

**Why put the queue in Redis rather than a Postgres table? What would a Postgres-backed queue give you?**
Redis gives fast push/pop, a blocking pop (BRPOP) so workers wait instead of polling, and keeps queue churn off the source-of-truth database. A Postgres queue (SELECT … FOR UPDATE SKIP LOCKED) could enqueue in the same transaction as the ticket insert, so a ticket can never be saved without its job, and it means one less system to run, at the cost of more load on the database.


## Lab 6: Reflect

**Why claim a ticket with one conditional UPDATE ... WHERE status = 'queued' instead of reading the status and then writing it?**
With read-then-write, two workers (or a duplicate queue entry) can both read "queued" before either writes, and both draft the ticket. One UPDATE with the condition inside is atomic: only one worker can change the row from queued to processing, and rowcount (1 or 0) tells each worker whether it won. A worker that gets 0 skips the ticket.

**Why does the exec form of CMD matter for graceful shutdown?**
docker stop sends SIGTERM to the container's main process. With exec form that process is Python, so my signal handler runs: the worker finishes the current draft and exits ("signal 15 ... worker stopped cleanly", 5 s). In shell form the main process is a shell that may not forward the signal, so Docker would wait the full 60 s grace period and then kill the worker, possibly mid-draft, leaving a ticket stuck in processing.

**Ten drafts, read critically.**
None of the five distinct drafts could be sent as is (CPU float32 and GPU float16 gave identical text, because greedy decoding is deterministic). Two had placeholders, two ignored "at most 5 sentences", one misspelled the brand, and three said something the policy doesn't: it admitted fault for a damaged bag, promised a flight change without the 50 EUR fee, and told a customer whose flight was cancelled by the airline that there is no refund, when the policy offers a full refund or free rebooking.

**How could the system catch that automatically?**
Rules (square brackets, sentence count, brand name) catch the noisy failures, 3 of 5. They miss the dangerous ones: the refund draft's only number is in the policy, so a numbers check passes it. A second model as judge is possible but unreliable at this size. The real control is FR3: an agent approves every draft, ideally with the policy shown next to it.

**Benchmarks (GTX 1050, 4 GB):** float32 median 6.2 s and 2091 MiB; float16 about 2x slower but 1035 MiB; CPU 11.4 s. float16 halves memory but is slower on this Pascal card, so float32 stays. One worker handles about 9.7 drafts/min, enough on average and with no headroom at peak.

**Bugs found along the way:**
- redis-py 8 defaults to a 5 s socket timeout, equal to my 5 s BRPOP wait, so the worker crash-looped. Fix: socket_timeout=15 on the worker's client. fakeredis can't reveal network timeouts.
- len(inputs) counts the dictionary's entries (2), not the prompt tokens: the reply would have echoed the whole prompt without crashing. Only reading real output catches it.
- A plain pip install torch gives the CUDA 13 build, which dropped Pascal. The worker image installs torch 2.14.1 from the cu126 index.
- python -m takes a dotted module name, never a file name with .py.
- Shell commands in a Dockerfile RUN are case-sensitive (MKDIR), and a directory used by a non-root user needs chown.

**Prompt experiments (placeholders in the drafts):**
Three attempts to remove "[Customer's Name]" and "[Your Name]" failed: a prohibition naming the strings in the system prompt, a positive "no greeting, no sign-off" rule, and the same rule at the end of the user message. The two baggage replies kept both placeholders every time (2 of 5), so a 0.5B model does not reliably follow format rules. Lessons: (1) a prompt change is a code change that the unit tests cannot see, so it needs a rebuild and a re-measurement; (2) the reply cache key does not include the prompt, so old replies hide the change until the cache is flushed (the fix is to add a hash of the system prompt to the key); (3) benchmark numbers describe one specific prompt, so the committed prompt must be the measured one. I kept the original prompt, and a code-side check (flagging drafts with square brackets) is the next step beyond this lab.