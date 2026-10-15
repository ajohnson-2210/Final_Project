from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor
from aj_parser import AJParserFacade


def process(source: str):
    return PseudocodeProfileProcessor().process(source=source, profile=PseudocodeProfile.AJ_DIALECT_STRICT)


def test_reserved_binding_is_propagated_into_string_placeholder():
    result = process('string <- STRING("")\nOUTPUT STRING("{string}")')
    assert '__reserved_keyword__string <- STRING("")' in result.processed_source
    assert 'STRING("{__reserved_keyword__string}")' in result.processed_source
    assert AJParserFacade().parse(result.processed_source).success


def test_reserved_external_member_name_after_dot_is_escaped_without_pre_mangling():
    result = process('os <- CALL __import__(STRING("os"))\nfull_path <- os.path.join(folder, item)')
    assert 'os.path.__reserved_keyword__join(folder, item)' in result.processed_source


def test_reserved_method_declaration_and_invocation_step_are_escaped():
    source = '''CLASS Swarm\n    METHOD step ACCEPTS(target)\n        OUTPUT target\n    ENDMETHOD\nENDCLASS\nswarm <- CALL Swarm()\nswarm.step(INTEGER(1))'''
    result = process(source)
    assert 'METHOD __reserved_keyword__step ACCEPTS(target)' in result.processed_source
    assert 'swarm.__reserved_keyword__step(INTEGER(1))' in result.processed_source
    assert AJParserFacade().parse(result.processed_source).success


def test_reserved_method_alias_survives_python_private_name_mangling():
    from aj_python_compiler import AJPythonCompiler
    from flow_diagram import FlowDiagramEncoder

    source = '''CLASS Bucket
    METHOD append ACCEPTS(value)
        OUTPUT value
    ENDMETHOD
ENDCLASS
bucket <- CALL Bucket()
bucket.append(INTEGER(7))'''
    result = process(source)
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    assert "setattr(Bucket, '__reserved_keyword__append'" in compiled.source_code

    namespace = {}
    exec(compiled.source_code, namespace, namespace)
