from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for _component_name in (
    "parser components",
    "compiler components",
    "flow diagram components",
    "pipeline components",
    "study components",
    "cli components",
):
    _component_path = str(PROJECT_ROOT / _component_name)
    if _component_path not in sys.path:
        sys.path.insert(0, _component_path)
import argparse
from aj_parser import AJParserFacade

def main():
    p=argparse.ArgumentParser(description='AJ_24038155 Dialect v1.5 AST parser')
    p.add_argument('source',type=Path)
    p.add_argument('--ast-json',type=Path)
    p.add_argument('--report-json',type=Path)
    a=p.parse_args(); result=AJParserFacade().parse(a.source.read_text(encoding='utf-8'))
    print(result.report.pretty())
    if result.adjacency_list:
        print('\nAST ADJACENCY LIST\n'+result.adjacency_list.pretty())
        if a.ast_json:a.ast_json.write_text(result.adjacency_list.to_json(),encoding='utf-8')
    if a.report_json:a.report_json.write_text(result.report.to_json(),encoding='utf-8')
    return 0 if result.success else 1
if __name__=='__main__': raise SystemExit(main())
