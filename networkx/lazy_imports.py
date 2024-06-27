import importlib
import importlib.util
import inspect
import os
import sys
import types
from utils.branch_coverage import branch_c
lazyImportBranch = branch_c("lazyImportBranch.txt")


__all__ = ["attach", "_lazy_import"]


def attach(module_name, submodules=None, submod_attrs=None):
    attachBranch = lazyImportBranch.branch_function(lazyImportBranch, "attach", 3)

    if submod_attrs is None:
        submod_attrs = {}
        attachBranch.addFlag("branch 1") 

    if submodules is None:
        submodules = set()
        attachBranch.addFlag("branch 2")
    else:
        submodules = set(submodules)
        attachBranch.addFlag("branch 3")

    attr_to_modules = {
        attr: mod for mod, attrs in submod_attrs.items() for attr in attrs
    }

    __all__ = list(submodules | attr_to_modules.keys())

    def __getattr__(name):
        getattrBranch = lazyImportBranch.branch_function(lazyImportBranch, "getattr", 3)
        if name in submodules:
            getattrBranch.addFlag("branch 1")
            return importlib.import_module(f"{module_name}.{name}")
        elif name in attr_to_modules:
            getattrBranch.addFlag("branch 2")
            submod = importlib.import_module(f"{module_name}.{attr_to_modules[name]}")
            return getattr(submod, name)
        else:
            getattrBranch.addFlag("branch 3")
            raise AttributeError(f"No {module_name} attribute {name}")

    def __dir__():
        dirBranch = lazyImportBranch.branch_function(lazyImportBranch, "dir", 1)
        return __all__
    if os.environ.get("EAGER_IMPORT", ""):
        dirBranch.addFlag("branch 1")
        for attr in set(attr_to_modules.keys()) | submodules:
            __getattr__(attr)

    return __getattr__, __dir__, list(__all__)


class DelayedImportErrorModule(types.ModuleType):
    def __init__(self, frame_data, *args, **kwargs):
        self.__frame_data = frame_data
        super().__init__(*args, **kwargs)

    def __getattr__(self, x):
        getattrBranch = lazyImportBranch.branch_function(lazyImportBranch, "getattr2", 2)
        if x in ("__class__", "__file__", "__frame_data"):
            getattrBranch.addFlag("branch 1")
            super().__getattr__(x)
        else:
            fd = self.__frame_data
            getattrBranch.addFlag("branch 2")
            raise ModuleNotFoundError(
                f"No module named '{fd['spec']}'\n\n"
                "This error is lazily reported, having originally occurred in\n"
                f'  File {fd["filename"]}, line {fd["lineno"]}, in {fd["function"]}\n\n'
                f'----> {"".join(fd["code_context"] or "").strip()}'
            )
            


def _lazy_import(fullname):
    lazy_importBranch = lazyImportBranch.branch_function(lazyImportBranch, "lazy_import", 1)
    
    try:
        return sys.modules[fullname]
    except:
        pass

    # Not previously loaded -- look it up
    spec = importlib.util.find_spec(fullname)

    if spec is None:
        lazy_importBranch.addFlag("branch 1")
        try:
            parent = inspect.stack()[1]
            frame_data = {
                "spec": fullname,
                "filename": parent.filename,
                "lineno": parent.lineno,
                "function": parent.function,
                "code_context": parent.code_context,
            }
            return DelayedImportErrorModule(frame_data, "DelayedImportErrorModule")
        finally:
            del parent

    module = importlib.util.module_from_spec(spec)
    sys.modules[fullname] = module

    loader = importlib.util.LazyLoader(spec.loader)
    loader.exec_module(module)

    return module
