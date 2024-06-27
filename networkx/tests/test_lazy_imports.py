import importlib
import sys
import types

import pytest
from unittest.mock import Mock, patch
import networkx.lazy_imports as lazy
import os


def test_lazy_import_basics():
    math = lazy._lazy_import("math")
    anything_not_real = lazy._lazy_import("anything_not_real")

    # Now test that accessing attributes does what it should
    assert math.sin(math.pi) == pytest.approx(0, 1e-6)
    # poor-mans pytest.raises for testing errors on attribute access
    try:
        anything_not_real.pi
        assert False  # Should not get here
    except ModuleNotFoundError:
        pass
    assert isinstance(anything_not_real, lazy.DelayedImportErrorModule)
    # see if it changes for second access
    try:
        anything_not_real.pi
        assert False  # Should not get here
    except ModuleNotFoundError:
        pass


def test_lazy_import_impact_on_sys_modules():
    math = lazy._lazy_import("math")
    anything_not_real = lazy._lazy_import("anything_not_real")

    assert type(math) == types.ModuleType
    assert "math" in sys.modules
    assert type(anything_not_real) == lazy.DelayedImportErrorModule
    assert "anything_not_real" not in sys.modules

    # only do this if numpy is installed
    np_test = pytest.importorskip("numpy")
    np = lazy._lazy_import("numpy")
    assert type(np) == types.ModuleType
    assert "numpy" in sys.modules

    np.pi  # trigger load of numpy

    assert type(np) == types.ModuleType
    assert "numpy" in sys.modules


def test_lazy_import_nonbuiltins():
    sp = lazy._lazy_import("scipy")
    np = lazy._lazy_import("numpy")
    if isinstance(sp, lazy.DelayedImportErrorModule):
        try:
            sp.special.erf
            assert False
        except ModuleNotFoundError:
            pass
    elif isinstance(np, lazy.DelayedImportErrorModule):
        try:
            np.sin(np.pi)
            assert False
        except ModuleNotFoundError:
            pass
    else:
        assert sp.special.erf(np.pi) == pytest.approx(1, 1e-4)


def test_lazy_attach():
    name = "mymod"
    submods = ["mysubmodule", "anothersubmodule"]
    myall = {"not_real_submod": ["some_var_or_func"]}

    locls = {
        "attach": lazy.attach,
        "name": name,
        "submods": submods,
        "myall": myall,
    }
    s = "__getattr__, __lazy_dir__, __all__ = attach(name, submods, myall)"

    exec(s, {}, locls)
    expected = {
        "attach": lazy.attach,
        "name": name,
        "submods": submods,
        "myall": myall,
        "__getattr__": None,
        "__lazy_dir__": None,
        "__all__": None,
    }
    assert locls.keys() == expected.keys()
    for k, v in expected.items():
        if v is not None:
            assert locls[k] == v


def test_getattr():
    module_name = "networkx.lazy_imports"
    submodules = ["submod1", "submod2"]
    submod_attrs = {"submod3": ["attr1", "attr2"]}

    __getattr__, __lazy_dir__, __all__ = lazy.attach(module_name, submodules, submod_attrs)

    # Mock importlib.import_module to track calls
    with patch("importlib.import_module") as mock_import_module:
        # Test importing a submodule
        mock_import_module.return_value = Mock()
        result = __getattr__("submod1")
        mock_import_module.assert_called_once_with(f"{module_name}.submod1")
        assert isinstance(result, Mock)

        # Test importing an attribute from a submodule
        mock_import_module.reset_mock()
        mock_submod = Mock()
        mock_import_module.return_value = mock_submod
        result = __getattr__("attr1")
        mock_import_module.assert_called_once_with(f"{module_name}.submod3")
        assert result == mock_submod.attr1

        # Test raising an AttributeError for a non-existent attribute
        try:
            __getattr__("non_existent_attr")
            assert False  # Should not get here
        except AttributeError as e:
            assert str(e) == f"No {module_name} attribute non_existent_attr"


def test_lazy_import_module_loading():
    module_name = "mockmodule"
    
    # Create a mock for the module spec and loader
    mock_spec = Mock()
    mock_loader = Mock()
    mock_module = Mock()
    
    mock_spec.loader = mock_loader
    
    with patch("importlib.util.find_spec", return_value=mock_spec) as mock_find_spec, \
         patch("importlib.util.module_from_spec", return_value=mock_module) as mock_module_from_spec, \
         patch("importlib.util.LazyLoader", return_value=mock_loader) as mock_lazy_loader, \
         patch("sys.modules", new_callable=dict) as mock_sys_modules:
        
        # Call the function to test
        loaded_module = lazy._lazy_import(module_name)
        
        # Assertions to ensure the mocks were called correctly
        mock_find_spec.assert_called_once_with(module_name)
        mock_module_from_spec.assert_called_once_with(mock_spec)
        mock_lazy_loader.assert_called_once_with(mock_spec.loader)
        mock_loader.exec_module.assert_called_once_with(mock_module)
        
        # Check if the module is correctly set in sys.modules
        assert mock_sys_modules[module_name] == mock_module
        assert loaded_module == mock_module



"""

def test_attach_function():
    module_name = "test_module"
    submodules = ["submod1", "submod2"]
    submod_attrs = {"submod3": ["attr1", "attr2"]}

    # Test the basic functionality of attach
    __getattr__, __dir__, __all__ = lazy.attach(module_name, submodules, submod_attrs)

    assert set(__all__) == {"submod1", "submod2", "attr1", "attr2"}

    # Mock importlib.import_module to track calls
    with patch("importlib.import_module") as mock_import_module:
        # Test importing a submodule
        mock_import_module.return_value = Mock()
        result = __getattr__("submod1")
        mock_import_module.assert_called_once_with(f"{module_name}.submod1")
        assert isinstance(result, Mock)

        # Test importing an attribute from a submodule
        mock_import_module.reset_mock()
        mock_submod = Mock()
        mock_import_module.return_value = mock_submod
        result = __getattr__("attr1")
        mock_import_module.assert_called_once_with(f"{module_name}.submod3")
        assert result == getattr(mock_submod, "attr1")

        # Test raising an AttributeError for a non-existent attribute
        try:
            __getattr__("non_existent_attr")
            assert False  # Should not get here
        except AttributeError as e:
            assert str(e) == f"No {module_name} attribute non_existent_attr"

    # Test __dir__
    dir_result = __dir__()
    assert set(dir_result) == set(__all__)

    # Test eager import
    with patch.dict('os.environ', {'EAGER_IMPORT': '1'}):
        with patch("importlib.import_module") as mock_import_module:
            mock_import_module.return_value = Mock()
            __getattr__, __dir__, __all__ = lazy.attach(module_name, submodules, submod_attrs)

            # Ensure that each module and attribute is imported eagerly
            mock_import_module.assert_any_call(f"{module_name}.submod1")
            mock_import_module.assert_any_call(f"{module_name}.submod2")
            mock_import_module.assert_any_call(f"{module_name}.submod3")
            
            expected_calls = {
                f"{module_name}.submod1",
                f"{module_name}.submod2",
                f"{module_name}.submod3"
            }

            actual_calls = {call.args[0] for call in mock_import_module.mock_calls}
            assert actual_calls == expected_calls
            assert len(actual_calls) == 3

"""