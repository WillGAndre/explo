## gitrojan
#### Remote module importing from a custom loader abstract base class  


### Sources
- [`python_importlib`](https://www.grumpymetalguy.com/programming/python_importlib/)
- [importlib abstract base class, 3.13.1 Doc.](https://docs.python.org/3/library/importlib.html#module-importlib.abc)
- [`importlib.util.spec_from_loader`, 3.13.1 Doc.](https://docs.python.org/3/library/importlib.html#importlib.util.spec_from_loader)
- [`exec_module`, 3.13.1 Doc.](https://docs.python.org/3/library/importlib.html#importlib.abc.Loader.exec_module)
- [`find_spec`, 3.13.1 Doc.](https://docs.python.org/3/library/importlib.html#importlib.abc.Loader.exec_module)
- [`sys.meta_path`, 3.13.1 Doc.](https://docs.python.org/3/library/sys.html#sys.meta_path)

### Structure:	

	./config -> Config files uniquely identified for each instance
	    - def.json (default config file)


	./modules -> Code to execute
	    Current Modules:
	        * Directory lister (dir_lister)
	        * List environment variables (get_env_var)


	./data -> Collected data

----

A module can be abstracted to a file containing Python definitions that can be imported at runtime using Python's import sub-system. [`gitrojan`](gitrojan.py) showcases dynamic module importing using `importlib`. The Python library, `github3.py` was used as the storage layer for both module code (that will be imported) as well as the module code execution results, which are delivered to `data/` once all modules complete.

----

`GitImporter` is created by subclassing `importlib.abc.Loader` and is used both as a module finder and loader. Modules are located using finder objects stored in `sys.meta_path`. `GitImporter` is added to this list (on initialization) so that it can intercept `import`/`__import__` statement executions, to simultaneously locate and execute the desired modules.

When subclassing a `Loader`, at a minimum, an override of `exec_module` is required. In this context, module execution refers to interpreting and running the module's code within its own namespace (`__dict__`), populating it with variables, functions, and classes, so that the module is ready for runtime use.

<pre>
0: sys.meta_path.insert(0, self)              | Register custom finder obj.
1: __import__(module_name)                    | Trigger module import
2: find_spec(self, fullname, path, target)    | Find module specification                 (IP0)
3: create_module(self, spec)                  | Default module creation method            (IP1)
4: exec_module(self, module)                  | Load and exec. module's code to memory    (IP2)
5: run_module(self, module)                   | Run methods within the mod. namespace
</pre>

`IPX` illustrates the import process for modules once they are triggered for import (`1`). Assuming `IP2` completes successfully the module's code should be referable and promptly executed (`5`). Without `0`, the module import method referencing (and overide) from `1` to `2` would not be achievable.

----

Finding modules, requires an abstract method of `find_spec` in order to locate import-related module information. Modules contents are located in `modules/`, where each module content is fetched using `github3`.

Since `GitImporter` is both a finder object and a module loader, the factory method `importlib.util.spec_from_loader` serves ideally for creating module specifications dynamically and then importing them directly within a single class specification (IP1 & IP2). 

----

DISCLAIMER:
This script is provided for educational purposes only. It is intended to
demonstrate dynamic module importing and execution techniques. The author
does not condone or support the use of this script for malicious purposes,
such as unauthorized access or exploitation.

Use this script responsibly and only in environments where you have explicit
authorization. The author is not liable for any misuse or legal consequences
arising from the use of this code.
