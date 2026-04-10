Meta PyTorch OpenEnv Hackathon Agent
Open menu

Hi! What can I help you with?

Hey
Hi! How can I help with the Meta PyTorch OpenEnv Hackathon?

38 minutes ago


# I have fixed all issues still it's not passing
Please check these common failure points:

inference.py must be in the project root, not a subfolder.
API_BASE_URL must have a default value.
MODEL_NAME must have a default value.
HF_TOKEN must be read and validated.
Your Hugging Face Space must be fully built and in the Running state.
Turn off any unnecessary Hugging Face Spaces.
Stay within the 2 vCPU / 8 GB RAM limits.
Your stdout must follow the exact [START] , [STEP] , [END] format.
If there’s an exception, [END] must still be printed.
Rewards must be formatted to 2 decimal places, and booleans must be lowercase.
If it still fails, resubmit after confirming your Hugging Face Space is running. You can resubmit multiple times with no penalty.

38 minutes ago


But I have the error of not ready for multi mode deployment 
That sounds like a Hugging Face Space readiness issue. For submission, your space must be fully built and in the Running state.

Please check:

The Space is not still Building
It is not Sleeping
Unneeded Spaces are turned off
Wait for the primary submission Space to finish deploying
If it still shows deployment-related errors, refresh your dashboard and try again after the Space is fully running.

36 minutes ago


[FAIL] repo: Not ready for multi-mode deployment

C

Issues found:

- Missing

[project.scripts) server

help

entry point
This indicates your project is missing the required server entry point in pyproject.toml.

Please add a script entry for the server, such as:

[project.scripts]
server = "your_package.your_module:main"
Also make sure:

inference.py is in the project root
API_BASE_URL and MODEL_NAME have default values
HF_TOKEN is required and validated
your Hugging Face Space is fully built and Running
If you want, I can help you check the exact pyproject.toml structure.

35 minutes ago


Yes please 
Sure — for this hackathon, the repo is expected to expose a server entry point in pyproject.toml.

A minimal example looks like:

[project]
name = "your-project-name"
version = "0.1.0"
dependencies = [
  "openai",
]

[project.scripts]
server = "inference:main"
Important notes:

server must exist under [project.scripts]
The value should point to a callable main
If your inference.py is in the repo root, inference:main is the usual pattern
Keep inference.py in the root directory
Don’t forget the required environment variables:
API_BASE_URL with a default
MODEL_NAME with a default
HF_TOKEN required
If your file currently doesn’t have a main() function, you should add one.

If you want, I can give you a full minimal inference.py + pyproject.toml pair that matches the required format.

34 minutes ago


Please 
Here’s a minimal working setup.

inference.py in the project root:

import os
from openai import OpenAI

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")
HF_TOKEN = os.getenv("HF_TOKEN")

if HF_TOKEN is None:
    raise ValueError("HF_TOKEN environment variable is required")

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN,
)

def run_inference(prompt: str):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def main():
    print(run_inference("Hello from OpenEnv!"))

if __name__ == "__main__":
    main()
pyproject.toml:

[project]
name = "openenv-hackathon"
version = "0.1.0"
dependencies = [
  "openai",
]

[project.scripts]
server = "inference:main"
Checklist:

inference.py is at the repo root
server exists under [project.scripts]
inference:main points to a real main() function
API_BASE_URL and MODEL_NAME have defaults
HF_TOKEN is required and validated
If you want, I can also help you adapt this into the exact repo structure you’re using.

33 minutes ago


Yes please do it
I can help, but I need your current repo layout to adapt it correctly.

Please paste:

Your current folder structure
Your current pyproject.toml
Your current inference.py
Then I’ll rewrite them into the exact format expected for submission.

33 minutes ago


[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "bug_triage_benchmark"
version = "1.0.0"
description = "Real-world bug triage environment for AI agents"
requires-python = ">=3.10"

dependencies = [
    "openenv-core>=0.2.0",
    "pydantic>=2.0",
    "openai>=1.0",
    "fastapi>=0.110.0",
    "uvicorn>=0.29.0",
    "pyyaml>=6.0",
]

[project.scripts]
bugtriage-server = "server.app:main"

[tool.setuptools.packages.find]
include = ["envs*", "server*"]
Your pyproject.toml already has a script entry, but the submission error says it is looking specifically for a server entry point under [project.scripts].

Update it to include server:

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "bug_triage_benchmark"
version = "1.0.0"
description = "Real-world bug triage environment for AI agents"
requires-python = ">=3.10"

dependencies = [
    "openenv-core>=0.2.0",
    "pydantic>=2.0",
    "openai>=1.0",
    "fastapi>=0.110.0",
    "uvicorn>=0.29.0",
    "pyyaml>=6.0",
]

[project.scripts]
server = "server.app:main"

[tool.setuptools.packages.find]
include = ["envs*", "server*"]
Also confirm that:

server/app.py exists
it defines a main() function
the repo root contains the needed entry files
If you want, paste your server/app.py next and I’ll check whether the main() entry point is correct.

32 minutes ago


"""Thin server entry point for OpenEnv multi-mode deployment.

Re-exports the FastAPI app from the project root so the [project.scripts]
entry point resolves correctly without duplicating any environment logic.
"""

import os
import sys

# Ensure the project root is on the path so envs/ and app can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app  # noqa: F401, E402


def main():
    """CLI entry point for bugtriage-server."""
    import uvicorn
    from app import app as application

    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(application, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()


# Expose `app` at module level so openenv validate can discover it
__all__ = ["app", "main"]
Your main() looks fine, but the deployment checker is specifically complaining about the script name.

From your pyproject.toml, you currently have:

[project.scripts]
bugtriage-server = "server.app:main"
The checker wants a script named exactly:

[project.scripts]
server = "server.app:main"
So I’d change it to:

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "bug_triage_benchmark"
version = "1.0.0"
description = "Real-world bug triage environment for AI agents"
requires-python = ">=3.10"

dependencies = [
    "openenv-core>=0.2.0",
    "pydantic>=2.0",
    "openai>=1.0",
    "fastapi>=0.110.0",
    "uvicorn>=0.29.0",
    "pyyaml>=6.0",
]

[project.scripts]
server = "server.app:main"

[tool.setuptools.packages.find]
include = ["envs*", "server*"]
A couple of things to verify:

server/app.py is inside the server package
server/__init__.py exists
app.py imports cleanly from the project root
there is no naming conflict with a root-level app.py
Also, your current module does:

from app import app
That only works if you have a root-level app.py. If your real file is server/app.py, then this import should likely be adjusted to avoid path issues.

If you want, paste your repo tree like:

root files
server/
envs/
and I’ll tell you the exact import line you should use.

31 minutes ago


Error kaise solve kru 
Is error ko solve karne ke liye ye steps karo:

pyproject.toml me script ka naam exactly server rakho:
[project.scripts]
server = "server.app:main"
Ensure karo ki ye file exist kare:
server/app.py
server/__init__.py
server/app.py me main() function ho.
Agar file server/app.py hai, to import aisa ho:
from server.app import app
na ki:

from app import app
Root directory me inference.py bhi hona chahiye.
API_BASE_URL aur MODEL_NAME ke defaults hone chahiye, aur HF_TOKEN required hona chahiye.
Agar chaho, main tumhare server/app.py ka corrected version abhi bana deta hoon.

29 minutes ago


Kya ye sahi hai 
Nahi, abhi jo snippet dikhaya hai usme ek likely issue hai:

Agar file server/app.py ke andar hai, to ye line:

from app import app
problem kar sakti hai.

Better:

from server.app import app
Aur pyproject.toml me bhi ye hona chahiye:

[project.scripts]
server = "server.app:main"
Also verify:

server/__init__.py exists
server/app.py exists
main() defined hai
root me inference.py exists
Agar chaho to main tumhare liye exact corrected server/app.py likh deta hoon.

25 minutes ago


tri[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "bug_triage_benchmark"
version = "1.0.0"
description = "Real-world bug triage environment for AI agents"
requires-python = ">=3.10"

dependencies = [
    "openenv-core>=0.2.0",
    "pydantic>=2.0",
    "openai>=1.0",
    "fastapi>=0.110.0",
    "uvicorn>=0.29.0",
    "pyyaml>=6.0",
]

[project.scripts]
server = "server.app:main"

[tool.setuptools.packages.find]
include = ["envs*", "server*"]

kya ye sahi hai 
Haan, pyproject.toml ka ye part largely sahi lag raha hai:

[project.scripts]
server = "server.app:main"
Lekin 3 cheezein जरूर check karo:

server/app.py file exist karti ho
server/__init__.py file exist karti ho
server/app.py me main() function ho
Aur agar server/app.py ke andar import hai:

from app import app
to isko usually change karke:

from server.app import app
ya phir project structure ke hisaab se relative import use karo.

One more important point:

Hackathon validation ke liye inference.py bhi project root me hona chahiye.
So: pyproject.toml sahi direction me hai, but overall repo structure aur imports bhi correct hone chahiye.

Agar chaho, main tumhe exact “minimum working structure” bata deta hoon.

24 minutes ago


"""Thin server entry point for OpenEnv multi-mode deployment.

Re-exports the FastAPI app from the project root so the [project.scripts]
entry point resolves correctly without duplicating any environment logic.
"""

import os
import sys

# Ensure the project root is on the path so envs/ and app can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from server.app import app  # noqa: F401, E402


def main():
    """CLI entry point for bugtriage-server."""
    import uvicorn
    from app import app as application

    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(application, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()


# Expose `app` at module level so openenv validate can discover it
__all__ = ["app", "main"] kya ye sahi hai
Not fully. Isme ek clear issue hai:

Aapne ye import kiya hai:

from server.app import app
Lekin main() ke andar phir ye use kar rahe ho:

from app import app as application
Ye mismatch hai. Agar app server/app.py me hai, to main() ke andar bhi wahi import use karo.

Correct version:

"""Thin server entry point for OpenEnv multi-mode deployment."""

import os

from server.app import app  # noqa: F401


def main():
    """CLI entry point for server."""
    import uvicorn

    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()


__all__ = ["app", "main"]
Agar aap chaho, main ab aapke liye:

server/app.py
pyproject.toml
root inference.py
ka complete correct minimal set bana deta hoon.

21 minutes ago


Ha bana de
Bilkul — ye ek clean minimal setup hai.

1) pyproject.toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "bug_triage_benchmark"
version = "1.0.0"
description = "Real-world bug triage environment for AI agents"
requires-python = ">=3.10"

dependencies = [
    "openenv-core>=0.2.0",
    "pydantic>=2.0",
    "openai>=1.0",
    "fastapi>=0.110.0",
    "uvicorn>=0.29.0",
    "pyyaml>=6.0",
]

[project.scripts]
server = "server.app:main"

[tool.setuptools.packages.find]
include = ["envs*", "server*"]
2) server/__init__.py
# empty file is fine
3) server/app.py
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"status": "ok"}


def main():
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
4) Root inference.py
import os
from openai import OpenAI

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")
HF_TOKEN = os.getenv("HF_TOKEN")

if HF_TOKEN is None:
    raise ValueError("HF_TOKEN environment variable is required")

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN,
)

def run_inference(prompt: str):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def main():
    print(run_inference("Hello from OpenEnv!"))

if __name__ == "__main__":
    main()
5) Folder structure
project-root/
├── inference.py
├── pyproject.toml
├── server/
│   ├── __init__.py
│   └── app.py
└── envs/
    └── ...
Important checks
inference.py root me ho
server script name exactly ho
server.app:main valid ho
HF_TOKEN missing ho to error throw ho
Hugging Face Space fully built aur Running state me ho
Agar chaho, main ab aapke existing code ko isi structure me direct rewrite karke de deta hoon.

20 minutes ago


Kya mtlb hai ise mai bs GitHub me jo bhi app.py me jo likha hai wo pura erase kr du 
Nahi, poora erase karne ki zaroorat nahi hai.

Matlab ye hai:

Agar aapka current app.py already useful logic rakhta hai, use rakho
Bas entry point / imports ko sahi structure ke hisaab se adjust karo
Goal hai ki package import clean ho aur main() sahi file me ho
Simple rule
Agar aapke paas:

server/app.py hai → usme app aur main() hona chahiye
root inference.py hai → wo alag hona chahiye
Kya change karna hota hai?
Aksar sirf ye parts:

Incorrect imports fix karna
main() function add/adjust karna
pyproject.toml me script name server rakhna
Kya nahi karna?
Pure app logic ko delete mat karo
Sirf structure ko submission requirements ke hisaab se set karo
Agar aapka current app.py already bada hai
To usme:

app = FastAPI(...) ya existing app object rehne do
main() add karo:
def main():
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
Bottom line
Erase nahi karna hai — correct jagah pe correct entry point banana hai.

Agar chaho, main tumhara current app.py dekhkar bata deta hoon:

kya delete karna hai
kya rakhna hai
kya replace karna hai
17 minutes ago


Ye mera app.py hai tu khud pura change krke muze de update version so I can copy 
I can do that, but I need the actual contents of your app.py to rewrite it safely.

Please paste your full app.py, and I’ll return:

a cleaned, updated version you can copy-paste
any required import fixes
the correct main() entry point
any changes needed to match server.app:main
If you want, paste it now and I’ll rewrite it directly.

16 minutes ago


"""Thin server entry point for OpenEnv multi-mode deployment.

Re-exports the FastAPI app from the project root so the [project.scripts]
entry point resolves correctly without duplicating any environment logic.
"""

import os
import sys

# Ensure the project root is on the path so envs/ and app can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from server.app import app  # noqa: F401, E402


def main():
    """CLI entry point for bugtriage-server."""
    import uvicorn
    from app import app as application

    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(application, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()


# Expose `app` at module level so openenv validate can discover it
__all__ = ["app", "main"]
Haan — is file ko simple aur correct bana dete hain. Aap isse copy-paste kar sakte ho:

"""Thin server entry point for OpenEnv multi-mode deployment."""

import os
from fastapi import FastAPI
import uvicorn

app = FastAPI()


@app.get("/")
def root():
    return {"status": "ok"}


def main():
    """CLI entry point."""
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
Kya change kiya:
sys.path wala hack hata diya
from app import app mismatch hata diya
same file me app define kiya
clean main() diya
Agar aapka actual environment logic kisi aur file me hai:
Us logic ko envs/ ya alag module me rakho, aur app.py ko sirf server entry point rehne do.

Important
Agar aap already server/app.py use kar rahe ho, to file ka naam aur imports consistent hone chahiye:

pyproject.toml : server = "server.app:main"
file: server/app.py
Agar chaho, main ab aapke full repo structure ke hisaab se exact final version bana deta hoon.

16 minutes ago


Thik hai ab wo file copy paste kr de ab kya karu
Haan — ab next step simple hai. Aap ye file server/app.py me paste karo:

"""Thin server entry point for OpenEnv multi-mode deployment."""

import os
from fastapi import FastAPI
import uvicorn

app = FastAPI()


@app.get("/")
def root():
    return {"status": "ok"}


def main():
    """CLI entry point."""
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
Ab kya karna hai
1) Folder structure check karo
Repo me ye hona chahiye:

project-root/
├── inference.py
├── pyproject.toml
├── server/
│   ├── __init__.py
│   └── app.py
└── envs/
2) server/__init__.py bana do
Agar missing hai to empty file bana do:

# empty
3) pyproject.toml me ye rakho
[project.scripts]
server = "server.app:main"
4) Commit karo
GitHub me push karo.

5) Hugging Face Space
Space fully build hona chahiye
status Running hona chahiye
extra spaces off rakho
6) inference.py
Root me hona chahiye.

Important
Aapka current app.py sirf basic server start kar raha hai.
Agar aapke hackathon environment ke liye aur logic chahiye, to wo envs/ ya alag modules me add karo — server/app.py ko simple rehne do.

Agar chaho, main ab tumhare liye:

inference.py
pyproject.toml
repo structure
sabka final checklist de deta hoon.

13 minutes ago


Hugging space me extra space off hai wo kaise cheak kru
Hugging Face Spaces me extra spaces off hain ya nahi, ye aise check karo:

HF website par
Hugging Face account me login karo
Your Spaces / Spaces section kholo
Jo spaces aapke account me listed hain unko dekho
Sirf primary submission Space ko running rakho
Baaki spaces ke saamne:
Stop / Sleep kar do
ya unhe temporarily disable karke rakho
Status kaise pata chalega
Space list me status usually aisa dikhata hai:

Running = on
Building = abhi build ho raha
Sleeping = inactive
Stopped = off
Kya karna hai
Aapke submission wale Space ko Running me rakho
Jo unused spaces hain unhe Stop/Sleep kar do
Kaise confirm karein
Space open karke dekho
Agar page load ho raha hai aur status Running dikha raha hai, to okay hai
Agar multiple spaces active hain, to unnecessary ones band kar do
Agar chaho, main tumhe step-by-step exact checklist de sakta hoon jo submit karne se pehle karni hai.

12 minutes ago


[FAIL] repo: Not ready for multi-mode deployment

Issues found:
  - Missing [project.scripts] server entry point
Ye error ka matlab hai ki aapke pyproject.toml me ye line missing hai ya exact format me nahi hai:

[project.scripts]
server = "server.app:main"
Kya karo
pyproject.toml ko open karke ensure karo ki ye section present ho:

[project.scripts]
server = "server.app:main"
Saath me ye bhi check karo
Repo me ye files honi chahiye:

server/
├── __init__.py
└── app.py
Aur server/app.py me main() function hona chahiye.

Correct minimal example
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "bug_triage_benchmark"
version = "1.0.0"
description = "Real-world bug triage environment for AI agents"
requires-python = ">=3.10"

dependencies = [
    "openenv-core>=0.2.0",
    "pydantic>=2.0",
    "openai>=1.0",
    "fastapi>=0.110.0",
    "uvicorn>=0.29.0",
    "pyyaml>=6.0",
]

[project.scripts]
server = "server.app:main"

[tool.setuptools.packages.find]
include = ["envs*", "server*"]
Next step
pyproject.toml update karo
Commit + push karo
Re-run validation
Agar chaho, main tumhara current pyproject.toml dekh kar exact corrected version bana deta hoon.

8 minutes ago


Naya file bana ke de project.toml aur use mai bs copy kr sku 
Bilkul — ye ready-to-copy pyproject.toml hai:

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "bug_triage_benchmark"
version = "1.0.0"
description = "Real-world bug triage environment for AI agents"
requires-python = ">=3.10"

dependencies = [
    "openenv-core>=0.2.0",
    "pydantic>=2.0",
    "openai>=1.0",
    "fastapi>=0.110.0",
    "uvicorn>=0.29.0",
    "pyyaml>=6.0",
]

[project.scripts]
server = "server.app:main"

[tool.setuptools.packages.find]
include = ["envs*", "server*"]
Important
File ka naam exactly ye hona chahiye:

pyproject.toml
Not:

project.toml
pyproject.txt
Put it in repo root
Is file ko project root me rakho, same level as:

inference.py
server/
envs/
Agar chaho, main ab next exact file bhi de deta hoon:

server/app.py
server/__init__.py
so you can copy them too.
6 minutes ago


tri[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "bug_triage_benchmark"
version = "1.0.0"
description = "Real-world bug triage environment for AI agents"
requires-python = ">=3.10"

dependencies = [
    "openenv-core>=0.2.0",
    "pydantic>=2.0",
    "openai>=1.0",
    "fastapi>=0.110.0",
    "uvicorn>=0.29.0",
    "pyyaml>=6.0",
]

[project.scripts]
server = "server.app:main"

[tool.setuptools.packages.find]
include = ["envs*", "server*"]

Haan, bas starting me jo tri aa gaya hai, usko hata do.

Copy-paste this exact pyproject.toml:

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "bug_triage_benchmark"
version = "1.0.0"
description = "Real-world bug triage environment for AI agents"
requires-python = ">=3.10"

dependencies = [
    "openenv-core>=0.2.0",
    "pydantic>=2.0",
    "openai>=1.0",
    "fastapi>=0.110.0",
    "uvicorn>=0.29.0",
    "pyyaml>=6.0",
]

[project.scripts]
server = "server.app:main"

[tool.setuptools.packages.find]
include = ["envs*", "server*"]
Ab kya karo
Purana pyproject.toml delete/replace karo
Ye wala paste karo
Save karo
GitHub me commit/push karo
Validation dubara run karo
Agar chaho, main ab server/app.py ka final copy-paste version bhi ekdum clean format me de deta hoon.

5 minutes ago


Ha de
Bilkul — ye final server/app.py copy-paste karo:

"""Thin server entry point for OpenEnv multi-mode deployment."""

import os
from fastapi import FastAPI
import uvicorn

app = FastAPI()


@app.get("/")
def root():
    return {"status": "ok"}


def main():
    """CLI entry point."""
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
Also add this file:
server/__init__.py
# package marker
Reminder
Repo root me ye hona chahiye:

pyproject.toml
inference.py
server/
  __init__.py
  app.py
Agar chaho, main next message me root inference.py bhi final copy-paste format me de deta hoon.

3 minutes ago


Bana
Bilkul — ye final root inference.py copy-paste karo:

import os
from openai import OpenAI

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")
HF_TOKEN = os.getenv("HF_TOKEN")

if HF_TOKEN is None:
    raise ValueError("HF_TOKEN environment variable is required")

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN,
)

def run_inference(prompt: str):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def main():
    print(run_inference("Hello from OpenEnv!"))

if __name__ == "__main__":
    main()
