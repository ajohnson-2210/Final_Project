import ast

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _compile(source: str) -> str:
    processed = PseudocodeProfileProcessor().process(source, PseudocodeProfile.AJ_DIALECT_STRICT)
    parsed = AJParserFacade().parse(processed.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success, compiled.message
    ast.parse(compiled.source_code)
    return compiled.source_code


def test_numpy_and_matplotlib_adapter_calls_lower_to_real_python_modules():
    source = '''FUNCTION demo ACCEPTS(x, y, mask)
    a <- CALL numpy_method_array(LIST [x, y], STRING("float"))
    b <- CALL numpy_method_random_uniform(0, 10)
    c <- CALL numpy_method_random_rand(2)
    d <- CALL numpy_method_linalg_norm(a, 1)
    e <- CALL numpy_method_where(mask)
    f <- CALL numpy_method_zeros(2)
    g <- CALL numpy_method_dot(a, a)
    h <- CALL numpy_method_empty(TUPLE(0, 2))
    figure_axes <- CALL matplotlib_method_subplots(TUPLE(6, 6))
    circle <- CALL matplotlib_method_Circle(a, 8, STRING("red"))
    animation <- CALL matplotlib_animation_method_FuncAnimation(figure_axes[0], demo, demo, 20, 40, BOOLEAN(FALSE))
    CALL matplotlib_method_show()
    RETURN a
ENDFUNCTION
'''
    code = _compile(source)
    assert "import numpy as np" in code
    assert "import matplotlib.pyplot as plt" in code
    assert "from matplotlib.animation import FuncAnimation" in code
    assert "np.array([x, y], dtype='float')" in code
    assert "np.random.uniform(0, 10)" in code
    assert "np.random.rand(2)" in code
    assert "np.linalg.norm(a, axis=1)" in code
    assert "np.where(mask)" in code
    assert "np.zeros(2)" in code
    assert "np.dot(a, a)" in code
    assert "np.empty((0, 2))" in code
    assert "plt.subplots(figsize=(6, 6))" in code
    assert "plt.Circle(a, 8, color='red')" in code
    assert "FuncAnimation(figure_axes[0], demo, init_func=demo, frames=20, interval=40, blit=False)" in code
    assert "plt.show()" in code
    assert "numpy_method_" not in code
    assert "matplotlib_method_" not in code
    assert "matplotlib_animation_method_" not in code


def test_external_support_is_not_injected_into_unrelated_programs():
    code = _compile('OUTPUT STRING("ok")\n')
    assert "import numpy as np" not in code
    assert "import matplotlib.pyplot as plt" not in code
    assert "FuncAnimation" not in code


def test_external_numeric_visual_program_executes_headlessly_when_dependencies_are_available(tmp_path):
    import importlib.util
    import pytest
    from aj_test_harness import AJTestHarness, TestCase

    if importlib.util.find_spec("numpy") is None or importlib.util.find_spec("matplotlib") is None:
        pytest.skip("optional numpy/matplotlib dependencies are not installed")

    source = '''point <- CALL numpy_method_array(LIST [1, 2], STRING("float"))
figure_axes <- CALL matplotlib_method_subplots(TUPLE(2, 2))
circle <- CALL matplotlib_method_Circle(point, 1, STRING("red"))
figure_axes[1].add_patch(circle)
CALL matplotlib_method_show()
'''
    code = _compile(source)
    program = tmp_path / "external_program.py"
    program.write_text(code, encoding="utf-8")
    report = AJTestHarness().run(
        program,
        [TestCase(
            name="headless",
            expected_output=[],
            expected_return_code=0,
            timeout_seconds=8.0,
            environment={"MPLBACKEND": "Agg"},
            requires_modules=["numpy", "matplotlib"],
            random_seed=104729,
        )],
    )
    assert report.success, report.to_json()
