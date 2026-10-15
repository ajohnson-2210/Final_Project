from __future__ import annotations
from abc import ABC
from dataclasses import dataclass, field, fields, asdict
from enum import Enum
from itertools import count
from typing import Any, Iterable
import json, re, time

class AJParserError(Exception): pass
class LexerError(AJParserError): pass
class ParserError(AJParserError): pass
class SemanticError(AJParserError): pass

class StageStatus(str, Enum):
    SUCCESS='SUCCESS'; FAILURE='FAILURE'; PARTIAL='PARTIAL'; NOT_RUN='NOT_RUN'

@dataclass(slots=True)
class StageResult:
    name:str; status:StageStatus; message:str; duration_ms:float=0.0; details:dict[str,Any]=field(default_factory=dict)
    def to_dict(self):
        d=asdict(self); d['status']=self.status.value; return d

@dataclass
class ProcessReport:
    stages:list[StageResult]=field(default_factory=list)
    def add(self,name,status,message,duration_ms=0.0,**details):
        self.stages.append(StageResult(name,status,message,round(duration_ms,3),details))
    @property
    def success(self): return bool(self.stages) and all(s.status==StageStatus.SUCCESS for s in self.stages)
    def to_dict(self): return {'success':self.success,'stages':[s.to_dict() for s in self.stages]}
    def to_json(self): return json.dumps(self.to_dict(),indent=2)
    def pretty(self):
        out=[]
        for s in self.stages:
            out.append(f'[{s.status.value:7}] {s.name:<26} {s.duration_ms:>8.3f} ms  {s.message}')
            for k,v in s.details.items(): out.append(f'           - {k}: {v}')
        return '\n'.join(out)

class TokenType(str,Enum):
    IDENT='IDENT'; INT='INT'; FLOAT='FLOAT'; STRING='STRING'; KEYWORD='KEYWORD'; OP='OP'; LP='LP'; RP='RP'; LB='LB'; RB='RB'; COMMA='COMMA'; DOT='DOT'; NEWLINE='NEWLINE'; EOF='EOF'; GET='GET'
@dataclass(frozen=True,slots=True)
class Token:
    type:TokenType; value:str; line:int; column:int
    def loc(self): return f'line {self.line}, column {self.column}'

class AJLexer:
    PHRASES=sorted({'REMOVE FIRST ITEM FROM','REMOVE LAST ITEM FROM','INTEGER DIVISION','FOR EACH','IN RANGE','LENGTH OF','EMPTY DICTIONARY','EMPTY STRING','EMPTY LIST','EMPTY SET','EMPTY TUPLE','ELSE IF','NOT IN','LIST OF','RANDOM INT','RANDOM FLOAT','RANDOM BOOLEAN'},key=len,reverse=True)
    WORDS={'FUNCTION','ACCEPTS','ENDFUNCTION','RETURN','CALL','IF','THEN','ELSE','ENDIF','WHILE','DO','ENDWHILE','FOR','TO','STEP','ENDFOR','IN','BREAK','STOP','QUIT','CONTINUE','OUTPUT','INPUT','APPEND','TRY','CATCH','ENDTRY','RAISE','INTEGER','FLOAT','STRING','CHAR','BOOLEAN','TRUE','FALSE','LIST','TUPLE','SET','JOIN','NOT','AND','OR','XOR','EXP','MODULUS','AS','COMMENT','CLASS','ENDCLASS','PROPERTY','CONSTRUCTOR','ENDCONSTRUCTOR','METHOD','ENDMETHOD','NONE','ISINSTANCE'}
    OPS=('<-','==','!=','<=','>=','+','-','*','/','<','>')
    def tokenise(self,source:str)->list[Token]:
        if not isinstance(source,str): raise LexerError('Source must be text.')
        tokens=[]
        lines=source.splitlines() or ['']
        for ln,line in enumerate(lines,1):
            comment_match = re.match(r"^(?P<indent>\s*)COMMENT(?:\s(?P<text>.*))?$", line, re.IGNORECASE)
            if comment_match:
                indent = comment_match.group("indent")
                text = comment_match.group("text")
                comment_column = len(indent) + 1
                tokens.append(Token(TokenType.KEYWORD, "COMMENT", ln, comment_column))
                if text is not None and text != "":
                    # COMMENT payload is deliberately opaque: preserve it verbatim
                    # rather than lexing punctuation/operators/quotes inside it.
                    text_column = comment_column + len("COMMENT") + 1
                    tokens.append(Token(TokenType.STRING, text, ln, text_column))
                tokens.append(Token(TokenType.NEWLINE, "\\n", ln, len(line)+1))
                continue

            i=0
            while i<len(line):
                if line[i].isspace(): i+=1; continue
                col=i+1; rem=line[i:]; up=rem.upper()
                phrase=next((p for p in self.PHRASES if up.startswith(p) and (len(rem)==len(p) or not (rem[len(p)].isalnum() or rem[len(p)]=='_'))),None)
                if phrase: tokens.append(Token(TokenType.KEYWORD,phrase,ln,col)); i+=len(phrase); continue
                if rem.startswith('~GET'): tokens.append(Token(TokenType.GET,'~GET',ln,col)); i+=4; continue
                op=next((o for o in self.OPS if rem.startswith(o)),None)
                if op: tokens.append(Token(TokenType.OP,op,ln,col)); i+=len(op); continue
                punct={'(':TokenType.LP,')':TokenType.RP,'[':TokenType.LB,']':TokenType.RB,',':TokenType.COMMA,'.':TokenType.DOT}
                if line[i] in punct: tokens.append(Token(punct[line[i]],line[i],ln,col)); i+=1; continue
                if line[i] in '\"\'':
                    q=line[i]; i+=1; chars=[]; esc=False
                    while i<len(line):
                        c=line[i]
                        if esc: chars.append({'n':'\n','t':'\t'}.get(c,c)); esc=False
                        elif c=='\\': esc=True
                        elif c==q: break
                        else: chars.append(c)
                        i+=1
                    if i>=len(line): raise LexerError(f'Unterminated string at line {ln}, column {col}.')
                    i+=1; tokens.append(Token(TokenType.STRING,''.join(chars),ln,col)); continue
                m=re.match(r'\d+\.\d+|\d+',rem)
                if m:
                    v=m.group(); tokens.append(Token(TokenType.FLOAT if '.' in v else TokenType.INT,v,ln,col)); i+=len(v); continue
                m=re.match(r'[A-Za-z_][A-Za-z0-9_]*',rem)
                if m:
                    v=m.group(); u=v.upper(); tokens.append(Token(TokenType.KEYWORD if u in self.WORDS else TokenType.IDENT,u if u in self.WORDS else v,ln,col)); i+=len(v); continue
                raise LexerError(f'Unrecognised character {line[i]!r} at line {ln}, column {col}.')
            tokens.append(Token(TokenType.NEWLINE,'\\n',ln,len(line)+1))
        tokens.append(Token(TokenType.EOF,'',len(lines)+1,1)); return tokens

_ids=count(1)
@dataclass
class ASTNode(ABC):
    line:int; node_id:str=field(default_factory=lambda:f'N{next(_ids)}',init=False)
    @property
    def kind(self): return type(self).__name__
    def children(self)->Iterable['ASTNode']:
        for f in fields(self):
            if f.name in {'line','node_id'}: continue
            v=getattr(self,f.name)
            if isinstance(v,ASTNode): yield v
            elif isinstance(v,list):
                for x in v:
                    if isinstance(x,ASTNode): yield x
    def attrs(self):
        d={}
        for f in fields(self):
            if f.name in {'line','node_id'}: continue
            v=getattr(self,f.name)
            if isinstance(v,ASTNode) or (isinstance(v,list) and any(isinstance(x,ASTNode) for x in v)): continue
            d[f.name]=v
        return d
@dataclass
class ProgramNode(ASTNode): body:list[ASTNode]
@dataclass
class BlockNode(ASTNode): statements:list[ASTNode]
@dataclass
class IdentifierNode(ASTNode): name:str
@dataclass
class LiteralNode(ASTNode): value:Any; data_type:str
@dataclass
class EmptyLiteralNode(ASTNode): empty_type:str
@dataclass
class ListLiteralNode(ASTNode): items:list[ASTNode]; declared_type:str|None=None
@dataclass
class SetLiteralNode(ASTNode): items:list[ASTNode]
@dataclass
class TupleLiteralNode(ASTNode): items:list[ASTNode]
@dataclass
class BinaryNode(ASTNode): operator:str; left:ASTNode; right:ASTNode
@dataclass
class UnaryNode(ASTNode): operator:str; operand:ASTNode
@dataclass
class IndexNode(ASTNode): collection:ASTNode; index:ASTNode
@dataclass
class MemberAccessNode(ASTNode): object:ASTNode; member:str
@dataclass
class MemberCallNode(ASTNode): object:ASTNode; member:str; arguments:list[ASTNode]; resolved_intrinsic:str|None=None
@dataclass
class RemoveFirstExpressionNode(ASTNode): collection:ASTNode
@dataclass
class RemoveLastExpressionNode(ASTNode): collection:ASTNode
@dataclass
class CallNode(ASTNode): name:str; arguments:list[ASTNode]
@dataclass
class CastNode(ASTNode): target_type:str; expression:ASTNode
@dataclass
class IsInstanceNode(ASTNode): expression:ASTNode; type_names:list[str]
@dataclass
class InputNode(ASTNode): prompt:ASTNode
@dataclass
class LengthNode(ASTNode): expression:ASTNode
@dataclass
class JoinNode(ASTNode): collection:ASTNode; separator:ASTNode
@dataclass
class SetOperationNode(ASTNode): operation:str; left:ASTNode; right:ASTNode
@dataclass
class RandomExpressionNode(ASTNode): random_type:str; minimum:ASTNode|None=None; maximum:ASTNode|None=None
@dataclass
class GetNode(ASTNode): dictionary:ASTNode; key:ASTNode; default:ASTNode|None=None
@dataclass
class AssignmentNode(ASTNode): target:ASTNode; value:ASTNode
@dataclass
class OutputNode(ASTNode): expression:ASTNode
@dataclass
class ReturnNode(ASTNode): expression:ASTNode|None=None
@dataclass
class BreakNode(ASTNode): pass
@dataclass
class StopNode(ASTNode): pass
@dataclass
class QuitNode(ASTNode): pass
@dataclass
class ContinueNode(ASTNode): pass
@dataclass
class AppendNode(ASTNode): value:ASTNode; collection:ASTNode
@dataclass
class InsertNode(ASTNode): value:ASTNode; collection:ASTNode; index:ASTNode
@dataclass
class RemoveValueNode(ASTNode): value:ASTNode; collection:ASTNode
@dataclass
class RemoveFirstNode(ASTNode): collection:ASTNode
@dataclass
class RemoveLastNode(ASTNode): collection:ASTNode
@dataclass
class RaiseNode(ASTNode): expression:ASTNode
@dataclass
class ElseIfNode(ASTNode): condition:ASTNode; body:BlockNode
@dataclass
class IfNode(ASTNode): condition:ASTNode; then_body:BlockNode; else_if:list[ElseIfNode]; else_body:BlockNode|None=None
@dataclass
class WhileNode(ASTNode): condition:ASTNode; body:BlockNode
@dataclass
class ForEachNode(ASTNode): variable:IdentifierNode; collection:ASTNode; body:BlockNode
@dataclass
class ForRangeNode(ASTNode): variable:IdentifierNode; start:ASTNode; end:ASTNode; step:ASTNode|None; body:BlockNode
@dataclass
class TryCatchNode(ASTNode): try_body:BlockNode; error:IdentifierNode|None; catch_body:BlockNode
@dataclass
class ParameterNode(ASTNode): name:str; declared_type:str|None=None
@dataclass
class FunctionNode(ASTNode): name:str; parameters:list[ParameterNode]; body:BlockNode
@dataclass
class PropertyDeclarationNode(ASTNode): name:str; declared_type:str|None=None
@dataclass
class PropertyAssignmentNode(ASTNode): target:MemberAccessNode; value:ASTNode
@dataclass
class ConstructorNode(ASTNode): parameters:list[ParameterNode]; body:BlockNode
@dataclass
class MethodNode(ASTNode): name:str; parameters:list[ParameterNode]; body:BlockNode
@dataclass
class ClassNode(ASTNode): name:str; parameters:list[ParameterNode]; body:BlockNode
@dataclass
class CommentNode(ASTNode): text:str
@dataclass
class ImportDirectiveNode(ASTNode): directive_type:str; module:str; alias:str|None=None; names:list[str]=field(default_factory=list)

class AJParser:
    PREC={'OR':1,'XOR':2,'AND':3,'==':4,'!=':4,'<':4,'>':4,'<=':4,'>=':4,'IN':4,'NOT IN':4,'+':5,'-':5,'*':6,'/':6,'INTEGER DIVISION':6,'MODULUS':6,'EXP':7}
    def __init__(self,tokens): self.t=tokens; self.i=0; self.loop_depth=0; self.fn_depth=0; self.class_depth=0
    def parse(self):
        body=[]; self.skip_nl()
        while not self.check(TokenType.EOF): body.append(self.statement()); self.skip_nl()
        return ProgramNode(1,body)
    def statement(self):
        if self.kw('CLASS'): return self.class_decl()
        if self.kw('PROPERTY'): return self.property_statement()
        if self.kw('CONSTRUCTOR'): return self.constructor()
        if self.kw('METHOD'): return self.method()
        if self.kw('FUNCTION'): return self.function()
        if self.kw('IF'): return self.if_stmt()
        if self.kw('WHILE'): return self.while_stmt()
        if self.kw('FOR EACH'): return self.foreach()
        if self.kw('FOR'): return self.forrange()
        if self.kw('TRY'): return self.trycatch()
        if self.kw('OUTPUT'):
            s=self.prev(); e=self.expr(); self.eol(); return OutputNode(s.line,e)
        if self.kw('RETURN'):
            s=self.prev();
            if self.fn_depth==0: raise ParserError(f'RETURN outside function at {s.loc()}.')
            e=None if self.check(TokenType.NEWLINE) else self.expr(); self.eol(); return ReturnNode(s.line,e)
        if self.kw('BREAK'):
            s=self.prev();
            if not self.loop_depth: raise ParserError(f'BREAK outside loop at {s.loc()}.')
            self.eol(); return BreakNode(s.line)
        if self.kw('STOP'):
            s=self.prev(); self.eol(); return StopNode(s.line)
        if self.kw('QUIT'):
            s=self.prev(); self.eol(); return QuitNode(s.line)
        if self.kw('CONTINUE'):
            s=self.prev();
            if not self.loop_depth: raise ParserError(f'CONTINUE outside loop at {s.loc()}.')
            self.eol(); return ContinueNode(s.line)
        if self.kw('APPEND'):
            s=self.prev(); v=self.expr(); self.need_kw('TO'); c=self.expr(); self.eol(); return AppendNode(s.line,v,c)
        if self.is_contextual_kw('INSERT') and self.line_has_contextual_kw('INTO') and self.line_has_contextual_kw('AT'):
            s=self.contextual_kw('INSERT'); v=self.expr(); self.need_contextual_kw('INTO'); c=self.expr(); self.need_contextual_kw('AT'); i=self.expr(); self.eol(); return InsertNode(s.line,v,c,i)
        if self.kw('REMOVE FIRST ITEM FROM'):
            s=self.prev(); c=self.expr(); self.eol(); return RemoveFirstNode(s.line,c)
        if self.kw('REMOVE LAST ITEM FROM'):
            s=self.prev(); c=self.expr(); self.eol(); return RemoveLastNode(s.line,c)
        if self.is_contextual_kw('REMOVE') and self.line_has_contextual_kw('FROM'):
            s=self.contextual_kw('REMOVE'); v=self.expr(); self.need_contextual_kw('FROM'); c=self.expr(); self.eol(); return RemoveValueNode(s.line,v,c)
        if self.kw('RAISE'):
            s=self.prev(); e=self.expr(); self.eol(); return RaiseNode(s.line,e)
        if self.kw('COMMENT'):
            s=self.prev(); text=''
            while not self.check(TokenType.NEWLINE): text += (' ' if text else '') + self.advance().value
            self.eol()
            directive=self._parse_import_directive(text,s.line)
            if (
                directive is not None
                and directive.directive_type == "FROM_IMPORT"
                and directive.names == ["*"]
                and (self.fn_depth > 0 or self.class_depth > 0)
            ):
                raise ParserError(
                    f"Wildcard COMMENT from ... import * is permitted only at program scope at {s.loc()}."
                )
            return directive if directive is not None else CommentNode(s.line,text)
        start=self.peek(); left=self.expr()
        if self.op('<-'):
            if not isinstance(left,(IdentifierNode,IndexNode,MemberAccessNode)): raise ParserError(f'Invalid assignment target at {start.loc()}.')
            val=self.expr(); self.eol(); return AssignmentNode(start.line,left,val)
        if isinstance(left,(CallNode,MemberCallNode)): self.eol(); return left
        raise ParserError(f'Expected assignment or CALL statement at {start.loc()}.')
    @staticmethod
    def _parse_import_directive(text: str, line: int):
        """Parse AJ v1.5 executable import directives embedded in COMMENT.

        Only exact, deliberately narrow forms acquire executable semantics.
        Every other COMMENT remains ordinary non-executable comment text.
        """
        module = r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*"
        identifier = r"[A-Za-z_][A-Za-z0-9_]*"

        match = re.fullmatch(
            rf"\s*import\s+(?P<module>{module})(?:\s+AS\s+(?P<alias>{identifier}))?\s*",
            text,
            re.IGNORECASE,
        )
        if match:
            return ImportDirectiveNode(
                line,
                "IMPORT",
                match.group("module"),
                match.group("alias"),
                [],
            )

        match = re.fullmatch(
            rf"\s*from\s+(?P<module>{module})\s+import\s+(?P<names>\*|{identifier}(?:\s*,\s*{identifier})*)\s*",
            text,
            re.IGNORECASE,
        )
        if match:
            names_text = match.group("names")
            names = ["*"] if names_text == "*" else [part.strip() for part in names_text.split(",")]
            return ImportDirectiveNode(line, "FROM_IMPORT", match.group("module"), None, names)

        return None

    def _parameter_list_after_accepts(self, context: str):
        self.need(TokenType.LP, "Expected '('.")
        params=[]
        if not self.check(TokenType.RP):
            while True:
                p=self.need(TokenType.IDENT,f'Expected {context} parameter.')
                typ=None
                if self.kw('AS'):
                    type_token=self.advance()
                    if type_token.type not in {TokenType.KEYWORD,TokenType.IDENT}:
                        raise ParserError(f'Expected type name at {type_token.loc()}.')
                    typ=type_token.value
                params.append(ParameterNode(p.line,p.value,typ))
                if not self.match(TokenType.COMMA): break
        self.need(TokenType.RP,"Expected ')'.")
        return params

    def class_decl(self):
        s=self.prev()
        name=self.need(TokenType.IDENT,'Expected class name.')
        params=[]
        # Backwards compatibility: pre-v2.83 internal class syntax may carry
        # ACCEPTS(...). Canonical AJ v1.0 classes do not require it.
        if self.kw('ACCEPTS'):
            params=self._parameter_list_after_accepts('class')
        self.eol()
        self.class_depth+=1
        body=self.block({'ENDCLASS'})
        self.class_depth-=1
        self.need_kw('ENDCLASS')
        self.eol()
        return ClassNode(s.line,name.value,params,body)

    def property_statement(self):
        s=self.prev()
        if self.class_depth==0:
            raise ParserError(f'PROPERTY outside class at {s.loc()}.')

        first=self.need(TokenType.IDENT,'Expected property name or THIS after PROPERTY.')
        if first.value.upper()=='THIS' and self.match(TokenType.DOT):
            member=self.need(TokenType.IDENT,'Expected property name after THIS.')
            self.need_op('<-')
            value=self.expr()
            self.eol()
            target=MemberAccessNode(first.line,IdentifierNode(first.line,'THIS'),member.value)
            return PropertyAssignmentNode(s.line,target,value)

        declared_type=None
        if self.kw('AS'):
            type_token=self.advance()
            if type_token.type not in {TokenType.KEYWORD,TokenType.IDENT}:
                raise ParserError(f'Expected type name at {type_token.loc()}.')
            declared_type=type_token.value
        self.eol()
        return PropertyDeclarationNode(s.line,first.value,declared_type)

    def constructor(self):
        s=self.prev()
        if self.class_depth==0:
            raise ParserError(f'CONSTRUCTOR outside class at {s.loc()}.')
        self.need_kw('ACCEPTS')
        params=self._parameter_list_after_accepts('constructor')
        self.eol()
        self.fn_depth+=1
        body=self.block({'ENDCONSTRUCTOR'})
        self.fn_depth-=1
        self.need_kw('ENDCONSTRUCTOR')
        self.eol()
        return ConstructorNode(s.line,params,body)

    def method(self):
        s=self.prev()
        if self.class_depth==0:
            raise ParserError(f'METHOD outside class at {s.loc()}.')
        name=self.need(TokenType.IDENT,'Expected method name.')
        self.need_kw('ACCEPTS')
        params=self._parameter_list_after_accepts('method')
        self.eol()
        self.fn_depth+=1
        body=self.block({'ENDMETHOD'})
        self.fn_depth-=1
        self.need_kw('ENDMETHOD')
        self.eol()
        return MethodNode(s.line,name.value,params,body)

    def function(self):
        # AJ v1.2 makes lexical FUNCTION nesting canonical.  The ordinary
        # statement dispatcher therefore remains valid while fn_depth > 0;
        # no special AST node or hoisting step is required.
        s=self.prev(); name=self.need(TokenType.IDENT,'Expected function name.'); self.need_kw('ACCEPTS'); params=self._parameter_list_after_accepts('function'); self.eol(); self.fn_depth+=1; body=self.block({'ENDFUNCTION'}); self.fn_depth-=1; self.need_kw('ENDFUNCTION'); self.eol(); return FunctionNode(s.line,name.value,params,body)
    def if_stmt(self):
        s=self.prev(); cond=self.expr(); self.need_kw('THEN'); self.eol(); then=self.block({'ELSE IF','ELSE','ENDIF'}); clauses=[]
        while self.kw('ELSE IF'):
            c=self.prev(); ce=self.expr(); self.need_kw('THEN'); self.eol(); clauses.append(ElseIfNode(c.line,ce,self.block({'ELSE IF','ELSE','ENDIF'})))
        other=None
        if self.kw('ELSE'): self.eol(); other=self.block({'ENDIF'})
        self.need_kw('ENDIF'); self.eol(); return IfNode(s.line,cond,then,clauses,other)
    def while_stmt(self):
        s=self.prev(); c=self.expr(); self.need_kw('DO'); self.eol(); self.loop_depth+=1; b=self.block({'ENDWHILE'}); self.loop_depth-=1; self.need_kw('ENDWHILE'); self.eol(); return WhileNode(s.line,c,b)
    def foreach(self):
        s=self.prev(); v=self.need(TokenType.IDENT,'Expected iterator.'); self.need_kw('IN'); c=self.expr(); self.need_kw('DO'); self.eol(); self.loop_depth+=1; b=self.block({'ENDFOR'}); self.loop_depth-=1; self.need_kw('ENDFOR'); self.eol(); return ForEachNode(s.line,IdentifierNode(v.line,v.value),c,b)
    def forrange(self):
        s=self.prev(); v=self.need(TokenType.IDENT,'Expected iterator.'); self.need_op('<-'); self.need_kw('IN RANGE'); a=self.expr(); self.need_kw('TO'); z=self.expr(); step=None
        if self.kw('STEP'): step=self.expr()
        self.need_kw('DO'); self.eol(); self.loop_depth+=1; b=self.block({'ENDFOR'}); self.loop_depth-=1; self.need_kw('ENDFOR'); self.eol(); return ForRangeNode(s.line,IdentifierNode(v.line,v.value),a,z,step,b)
    def trycatch(self):
        s=self.prev(); self.eol(); tb=self.block({'CATCH'}); self.need_kw('CATCH'); err=None
        if self.check(TokenType.IDENT): x=self.advance(); err=IdentifierNode(x.line,x.value)
        self.eol(); cb=self.block({'ENDTRY'}); self.need_kw('ENDTRY'); self.eol(); return TryCatchNode(s.line,tb,err,cb)
    def block(self,ends):
        st=[]; self.skip_nl(); line=self.peek().line
        while not self.check(TokenType.EOF) and not (self.peek().type==TokenType.KEYWORD and self.peek().value in ends): st.append(self.statement()); self.skip_nl()
        if self.check(TokenType.EOF): raise ParserError(f'Unexpected end of file; expected one of {sorted(ends)}.')
        return BlockNode(line,st)
    def expr(self,minp=1):
        left=self.unary(); comparison_seen=False
        comparison_ops={'==','!=','<','>','<=','>=','IN','NOT IN'}
        while True:
            op=self.binop()
            if op is None or self.PREC[op]<minp: break
            if op in comparison_ops:
                if comparison_seen:
                    raise ParserError(
                        f'Chained comparisons are not canonical AJ at {self.peek().loc()}; '
                        'expand them with AND between adjacent comparisons.'
                    )
                comparison_seen=True
            tok=self.advance()
            right=self.expr(self.PREC[op] if op=='EXP' else self.PREC[op]+1); left=BinaryNode(tok.line,op,left,right)
        return left
    def unary(self):
        if self.kw('NOT'): s=self.prev(); return UnaryNode(s.line,'NOT',self.unary())
        if self.op('-'): s=self.prev(); return UnaryNode(s.line,'-',self.unary())
        return self.postfix()
    def postfix(self):
        n=self.primary()
        while True:
            if self.match(TokenType.LB): s=self.prev(); idx=self.expr(); self.need(TokenType.RB,"Expected ']'."); n=IndexNode(s.line,n,idx)
            elif self.match(TokenType.DOT):
                s=self.prev()
                member=self.advance()
                if not (member.type==TokenType.IDENT or (member.type==TokenType.KEYWORD and member.value=='GET')):
                    raise ParserError(f'Expected property or method name after dot. Found {member.value!r} at {member.loc()}.')
                if self.check(TokenType.LP):
                    arguments=self.sequence(TokenType.LP,TokenType.RP)
                    n=MemberCallNode(s.line,n,member.value,arguments)
                else:
                    n=MemberAccessNode(s.line,n,member.value)
            elif self.match(TokenType.GET):
                s=self.prev(); self.need(TokenType.LP,"Expected '('."); key=self.expr(); default=None
                if self.match(TokenType.COMMA): default=self.expr()
                self.need(TokenType.RP,"Expected ')'."); n=GetNode(s.line,n,key,default)
            else: break
        return n
    def primary(self):
        t=self.peek()
        if self.match(TokenType.INT): return LiteralNode(t.line,int(t.value),'INTEGER')
        if self.match(TokenType.FLOAT): return LiteralNode(t.line,float(t.value),'FLOAT')
        if self.kw('NONE'): return LiteralNode(t.line,None,'NONE')
        if self.is_contextual_kw('UNION') or self.is_contextual_kw('INTERSECTION') or self.is_contextual_kw('DIFFERENCE'):
            operation=self.peek().value.upper()
            if self.peek2().type==TokenType.LP:
                self.advance()
                args=self.sequence(TokenType.LP,TokenType.RP)
                if len(args)!=2:
                    raise ParserError(f'{operation} requires exactly two operands at {t.loc()}.')
                return SetOperationNode(t.line,operation,args[0],args[1])
        if self.kw('RANDOM INT'):
            args=self.sequence(TokenType.LP,TokenType.RP)
            if len(args)!=2:
                raise ParserError(f'RANDOM INT requires exactly two bounds at {t.loc()}.')
            return RandomExpressionNode(t.line,'INT',args[0],args[1])
        if self.kw('RANDOM FLOAT'):
            args=self.sequence(TokenType.LP,TokenType.RP)
            if len(args)!=2:
                raise ParserError(f'RANDOM FLOAT requires exactly two bounds at {t.loc()}.')
            return RandomExpressionNode(t.line,'FLOAT',args[0],args[1])
        if self.kw('RANDOM BOOLEAN'):
            args=self.sequence(TokenType.LP,TokenType.RP)
            if args:
                raise ParserError(f'RANDOM BOOLEAN requires zero arguments at {t.loc()}.')
            return RandomExpressionNode(t.line,'BOOLEAN')
        if self.match(TokenType.IDENT): return IdentifierNode(t.line,t.value)
        if self.match(TokenType.LP): n=self.expr(); self.need(TokenType.RP,"Expected ')'."); return n
        for kw,typ in [('EMPTY LIST','LIST'),('EMPTY DICTIONARY','DICTIONARY'),('EMPTY STRING','STRING'),('EMPTY SET','SET'),('EMPTY TUPLE','TUPLE')]:
            if self.kw(kw): return EmptyLiteralNode(t.line,typ)
        if self.kw('BOOLEAN'):
            self.need(TokenType.LP,"Expected '('.")
            if self.kw('TRUE'): v=True
            elif self.kw('FALSE'): v=False
            else: raise ParserError(f'Expected TRUE or FALSE at {self.peek().loc()}.')
            self.need(TokenType.RP,"Expected ')'."); return LiteralNode(t.line,v,'BOOLEAN')
        for typ in ('STRING','CHAR','INTEGER','FLOAT'):
            if self.kw(typ):
                self.need(TokenType.LP,"Expected '('."); x=self.advance()
                allowed={TokenType.STRING,TokenType.INT,TokenType.FLOAT,TokenType.IDENT}
                if x.type not in allowed: raise ParserError(f'Invalid {typ} literal at {x.loc()}.')
                self.need(TokenType.RP,"Expected ')'."); val=x.value
                if typ=='CHAR' and x.type==TokenType.IDENT:
                    return CallNode(t.line,'CHAR',[IdentifierNode(t.line,x.value)])
                if typ=='INTEGER' and x.type==TokenType.INT: val=int(val)
                if typ=='FLOAT' and x.type in {TokenType.INT,TokenType.FLOAT}: val=float(val)
                if typ=='CHAR' and len(str(val))!=1: raise ParserError(f'CHAR must contain one character at {t.loc()}.')
                return LiteralNode(t.line,val,typ)
        if self.kw('LIST') or self.kw('LIST OF'):
            declared=None
            if self.prev().value=='LIST OF' and self.peek().type in {TokenType.KEYWORD,TokenType.IDENT}: declared=self.advance().value
            return ListLiteralNode(t.line,self.sequence(TokenType.LB,TokenType.RB),declared)
        if self.kw('SET'): return SetLiteralNode(t.line,self.sequence(TokenType.LB,TokenType.RB))
        if self.kw('TUPLE'): return TupleLiteralNode(t.line,self.sequence(TokenType.LP,TokenType.RP))
        if self.kw('CALL'):
            # AJ v1.3 explicit runtime casts use the otherwise-reserved primitive
            # type keywords after CALL, keeping literal constructors unambiguous:
            # INTEGER(5) is a typed literal; CALL INTEGER(value) is a cast.
            if self.peek().type==TokenType.KEYWORD and self.peek().value in {'INTEGER','FLOAT','STRING'}:
                cast_token=self.advance()
                arguments=self.sequence(TokenType.LP,TokenType.RP)
                if len(arguments)!=1:
                    raise ParserError(
                        f'CALL {cast_token.value} requires exactly one argument at {cast_token.loc()}.'
                    )
                return CastNode(t.line,cast_token.value,arguments[0])
            # AJ v1.4 runtime type inspection is a dedicated intrinsic. Type
            # references are syntax, not ordinary expression values, so the
            # parser handles the second operand explicitly rather than making
            # INTEGER/FLOAT/STRING first-class values.
            if self.peek().type==TokenType.KEYWORD and self.peek().value=='ISINSTANCE':
                intrinsic=self.advance()
                self.need(TokenType.LP,"Expected '('.")
                value=self.expr()
                self.need(TokenType.COMMA,"Expected ',' between value and type reference.")
                type_names=self.type_reference_list()
                self.need(TokenType.RP,"Expected ')' after ISINSTANCE type reference.")
                return IsInstanceNode(t.line,value,type_names)
            name=self.need(TokenType.IDENT,'Expected called function name.'); return CallNode(t.line,name.value,self.sequence(TokenType.LP,TokenType.RP))
        if self.kw('INPUT'):
            self.need(TokenType.LP,"Expected '('."); p=self.expr(); self.need(TokenType.RP,"Expected ')'."); return InputNode(t.line,p)
        if self.kw('LENGTH OF'): return LengthNode(t.line,self.unary())
        if self.kw('REMOVE FIRST ITEM FROM'): return RemoveFirstExpressionNode(t.line,self.unary())
        if self.kw('REMOVE LAST ITEM FROM'): return RemoveLastExpressionNode(t.line,self.unary())
        if self.kw('JOIN'):
            self.need(TokenType.LP,"Expected '('."); a=self.expr(); self.need(TokenType.COMMA,"Expected ','."); b=self.expr(); self.need(TokenType.RP,"Expected ')'."); return JoinNode(t.line,a,b)
        raise ParserError(f'Expected expression at {t.loc()}, found {t.value!r}.')
    def type_reference_list(self):
        """Parse the type operand of canonical AJ v1.4 ISINSTANCE.

        Canonical examples are ``STRING`` and ``(INTEGER, FLOAT)``. Type
        names remain syntax-only references and are not promoted to ordinary
        first-class expression values.
        """
        builtin={'INTEGER','FLOAT','STRING','BOOLEAN','LIST','DICTIONARY','SET','TUPLE'}

        def one():
            token=self.peek()
            if token.type==TokenType.KEYWORD and token.value in builtin:
                self.advance(); return token.value
            if token.type==TokenType.IDENT:
                self.advance(); return token.value
            raise ParserError(
                f'Expected AJ type reference at {token.loc()}, found {token.value!r}.'
            )

        if self.match(TokenType.LP):
            names=[one()]
            while self.match(TokenType.COMMA):
                names.append(one())
            self.need(TokenType.RP,"Expected ')' after ISINSTANCE type list.")
            return names
        return [one()]

    def sequence(self,left,right):
        self.need(left,'Expected opening delimiter.'); xs=[]
        if not self.check(right):
            while True:
                xs.append(self.expr())
                if not self.match(TokenType.COMMA): break
        self.need(right,'Expected closing delimiter.'); return xs
    def binop(self):
        t=self.peek()
        if t.type in {TokenType.OP,TokenType.KEYWORD}:
            if t.value=='NOT' and self.peek2().value=='IN': return 'NOT IN'
            if t.value in self.PREC: return t.value
        return None
    def eol(self):
        if not self.match(TokenType.NEWLINE): raise ParserError(f'Expected end of line at {self.peek().loc()}.')
    def skip_nl(self):
        while self.match(TokenType.NEWLINE): pass
    def kw(self,v):
        if self.peek().type==TokenType.KEYWORD and self.peek().value==v: self.advance(); return True
        return False
    def is_contextual_kw(self,v):
        t=self.peek()
        return t.type in {TokenType.IDENT,TokenType.KEYWORD} and t.value.upper()==v
    def contextual_kw(self,v):
        if self.is_contextual_kw(v): return self.advance()
        return None
    def need_contextual_kw(self,v):
        token=self.contextual_kw(v)
        if token is None: raise ParserError(f'Expected {v!r} at {self.peek().loc()}, found {self.peek().value!r}.')
        return token
    def line_has_contextual_kw(self,v):
        j=self.i
        while j<len(self.t) and self.t[j].type not in {TokenType.NEWLINE,TokenType.EOF}:
            token=self.t[j]
            if token.type in {TokenType.IDENT,TokenType.KEYWORD} and token.value.upper()==v:
                return True
            j+=1
        return False
    def op(self,v):
        if self.peek().type==TokenType.OP and self.peek().value==v: self.advance(); return True
        return False
    def need_kw(self,v):
        if not self.kw(v): raise ParserError(f'Expected {v!r} at {self.peek().loc()}, found {self.peek().value!r}.')
    def need_op(self,v):
        if not self.op(v): raise ParserError(f'Expected operator {v!r} at {self.peek().loc()}.')
    def match(self,typ):
        if self.check(typ): self.advance(); return True
        return False
    def need(self,typ,msg):
        if self.check(typ): return self.advance()
        raise ParserError(f'{msg} Found {self.peek().value!r} at {self.peek().loc()}.')
    def check(self,typ): return self.peek().type==typ
    def advance(self):
        x=self.peek();
        if x.type!=TokenType.EOF: self.i+=1
        return x
    def peek(self): return self.t[self.i]
    def peek2(self): return self.t[min(self.i+1,len(self.t)-1)]
    def prev(self): return self.t[self.i-1]

class SemanticValidator:
    def validate(self,root:ProgramNode)->list[str]:
        warnings=[]
        self._resolve_member_intrinsics(root)
        self._validate_identifier_bindings(root)
        self._validate_function_call_arity(root)
        self._validate_member_call_arity(root)
        self._validate_constructor_returns(root)
        self._validate_explicit_types(root)
        self._validate_join_compatibility(root)
        self._validate_declared_type_entries(root)
        for n in self.walk(root):
            if isinstance(n,ForRangeNode) and isinstance(n.step,LiteralNode) and n.step.value==0: raise SemanticError(f'FOR STEP cannot be zero at line {n.line}.')
        return warnings

    def _validate_constructor_returns(self, root:ProgramNode):
        """Reject value-returning RETURN statements in constructors.

        AJ v1.2 says constructors should not return a value.  The generated
        Python target makes that restriction operationally necessary because
        ``__init__`` may return only ``None``.  A value-less RETURN remains
        valid as an early constructor exit.  Returns inside nested/local
        functions are checked in their own function context and therefore do
        not count as constructor returns.
        """

        def visit_block(block:BlockNode, in_constructor:bool=False):
            for statement in block.statements:
                if isinstance(statement,ReturnNode):
                    if in_constructor and statement.expression is not None:
                        raise SemanticError(
                            f"CONSTRUCTOR must not RETURN a value at line {statement.line}."
                        )
                    continue

                if isinstance(statement,IfNode):
                    visit_block(statement.then_body,in_constructor)
                    for clause in statement.else_if:
                        visit_block(clause.body,in_constructor)
                    if statement.else_body is not None:
                        visit_block(statement.else_body,in_constructor)
                    continue

                if isinstance(statement,(WhileNode,ForEachNode,ForRangeNode)):
                    visit_block(statement.body,in_constructor)
                    continue

                if isinstance(statement,TryCatchNode):
                    visit_block(statement.try_body,in_constructor)
                    visit_block(statement.catch_body,in_constructor)
                    continue

                if isinstance(statement,ConstructorNode):
                    visit_block(statement.body,True)
                    continue

                if isinstance(statement,(FunctionNode,MethodNode)):
                    # A nested routine establishes a new RETURN context.
                    visit_block(statement.body,False)
                    continue

                if isinstance(statement,ClassNode):
                    # Class members establish their own routine contexts;
                    # recurse so constructors nested in a class are checked.
                    visit_block(statement.body,False)

        visit_block(BlockNode(root.line,root.body),False)

    def _validate_function_call_arity(self, root:ProgramNode):
        """Enforce AJ v1.2 arity for lexically resolved free functions.

        Function declarations establish a routine signature in their lexical
        block.  Calls whose names resolve to one of those declarations must
        supply exactly the declared number of parameters.  Calls to external
        or otherwise undefined helpers are deliberately left alone because AJ
        has no supplied signature from which to infer their arity.  Member
        calls are likewise outside this free-function check; their resolution
        depends on receiver evidence.
        """

        def signatures_for(block:BlockNode, inherited:dict[str,int])->dict[str,int]:
            visible=dict(inherited)
            # A function declaration belongs to the lexical scope of its
            # containing block.  Collect the block first so recursion, sibling
            # calls, and forward references within the same lexical block use
            # the supplied declaration rather than runtime guesswork.
            for statement in block.statements:
                if isinstance(statement,FunctionNode):
                    visible[statement.name]=len(statement.parameters)
            return visible

        def validate_expression(node, signatures:dict[str,int]):
            if node is None:
                return
            if isinstance(node,(CastNode,IsInstanceNode)):
                validate_expression(node.expression,signatures)
                return
            if isinstance(node,CallNode):
                expected=signatures.get(node.name)
                if expected is not None and len(node.arguments)!=expected:
                    raise SemanticError(
                        f"Function {node.name!r} requires {expected} argument"
                        f"{'s' if expected != 1 else ''}, but {len(node.arguments)} "
                        f"{'were' if len(node.arguments) != 1 else 'was'} supplied at line {node.line}."
                    )
                for argument in node.arguments:
                    validate_expression(argument,signatures)
                return
            # MemberCallNode names are not free lexical function names, but
            # nested free CALL expressions in their receiver/arguments still
            # need validation.
            for child in node.children():
                validate_expression(child,signatures)

        def visit_block(block:BlockNode, inherited:dict[str,int]):
            visible=signatures_for(block,inherited)
            for statement in block.statements:
                if isinstance(statement,FunctionNode):
                    visit_block(statement.body,visible)
                    continue
                if isinstance(statement,ClassNode):
                    # Free lexical functions remain visible inside class
                    # bodies, methods, and constructors.  Method/constructor
                    # signatures themselves require member/constructor
                    # resolution and are therefore not guessed here.
                    class_visible=signatures_for(statement.body,visible)
                    for item in statement.body.statements:
                        if isinstance(item,FunctionNode):
                            visit_block(item.body,class_visible)
                        elif isinstance(item,(ConstructorNode,MethodNode)):
                            visit_block(item.body,class_visible)
                        else:
                            validate_expression(item,class_visible)
                    continue
                if isinstance(statement,(ConstructorNode,MethodNode)):
                    visit_block(statement.body,visible)
                    continue
                validate_expression(statement,visible)

        visit_block(BlockNode(root.line,root.body),{})

    def _validate_member_call_arity(self, root:ProgramNode):
        """Enforce method arity only when AJ supplies receiver-class evidence.

        AJ v1.2 distinguishes member invocation from free CALL syntax.  This
        pass therefore checks a MemberCallNode only when its receiver can be
        resolved without protocol inference: ``THIS`` inside a known class,
        an identifier with an explicit user-defined class type, or a chain of
        explicitly typed class properties.  Unknown/external receivers remain
        unchecked because no AJ method signature is available for them.
        """

        def normalise_type(name):
            if not name:
                return None
            text=str(name)
            protected_prefix='__reserved_keyword__'
            if text.lower().startswith(protected_prefix.lower()):
                text=text[len(protected_prefix):]
            return text

        classes={
            statement.name:statement
            for statement in root.body
            if isinstance(statement,ClassNode)
        }
        method_arities={
            class_name:{
                item.name:len(item.parameters)
                for item in class_node.body.statements
                if isinstance(item,MethodNode)
            }
            for class_name,class_node in classes.items()
        }
        property_types={
            class_name:{
                item.name:normalise_type(item.declared_type)
                for item in class_node.body.statements
                if isinstance(item,PropertyDeclarationNode) and item.declared_type
            }
            for class_name,class_node in classes.items()
        }

        if not classes:
            return

        def local_assignment_names(block:BlockNode)->set[str]:
            names=set()
            def visit(current:BlockNode):
                for statement in current.statements:
                    if isinstance(statement,AssignmentNode) and isinstance(statement.target,IdentifierNode):
                        names.add(statement.target.name)
                    elif isinstance(statement,IfNode):
                        visit(statement.then_body)
                        for clause in statement.else_if:
                            visit(clause.body)
                        if statement.else_body is not None:
                            visit(statement.else_body)
                    elif isinstance(statement,(WhileNode,ForEachNode,ForRangeNode)):
                        visit(statement.body)
                    elif isinstance(statement,TryCatchNode):
                        visit(statement.try_body)
                        visit(statement.catch_body)
                    # Nested routines/classes establish distinct local scopes.
            visit(block)
            return names

        def routine_types(parameters, inherited:dict[str,str], body:BlockNode)->dict[str,str]:
            visible=dict(inherited)
            # A simple assignment in a nested routine creates a local binding,
            # so it shadows any same-named typed value inherited lexically.
            for name in local_assignment_names(body):
                visible.pop(name,None)
            for parameter in parameters:
                visible.pop(parameter.name,None)
                declared=normalise_type(parameter.declared_type)
                if declared in classes:
                    visible[parameter.name]=declared
            return visible

        def receiver_class(node, visible_types:dict[str,str], current_class:str|None):
            if isinstance(node,IdentifierNode):
                if node.name.upper()=='THIS':
                    return current_class
                typ=visible_types.get(node.name)
                return typ if typ in classes else None
            if isinstance(node,MemberAccessNode):
                owner=receiver_class(node.object,visible_types,current_class)
                if owner is None:
                    return None
                typ=property_types.get(owner,{}).get(node.member)
                return typ if typ in classes else None
            return None

        def validate_expression(node, visible_types:dict[str,str], current_class:str|None):
            if node is None:
                return
            if isinstance(node,MemberCallNode):
                validate_expression(node.object,visible_types,current_class)
                for argument in node.arguments:
                    validate_expression(argument,visible_types,current_class)
                owner=receiver_class(node.object,visible_types,current_class)
                if owner is not None:
                    expected=method_arities.get(owner,{}).get(node.member)
                    if expected is not None and len(node.arguments)!=expected:
                        raise SemanticError(
                            f"Method {owner}.{node.member} requires {expected} argument"
                            f"{'s' if expected != 1 else ''}, but {len(node.arguments)} "
                            f"{'were' if len(node.arguments) != 1 else 'was'} supplied at line {node.line}."
                        )
                return
            for child in node.children():
                validate_expression(child,visible_types,current_class)

        def visit_block(block:BlockNode, visible_types:dict[str,str], current_class:str|None):
            for statement in block.statements:
                if isinstance(statement,FunctionNode):
                    child_types=routine_types(statement.parameters,visible_types,statement.body)
                    visit_block(statement.body,child_types,current_class)
                    continue
                if isinstance(statement,ClassNode):
                    class_types=routine_types(statement.parameters,visible_types,statement.body)
                    for item in statement.body.statements:
                        if isinstance(item,ConstructorNode):
                            child_types=routine_types(item.parameters,class_types,item.body)
                            visit_block(item.body,child_types,statement.name)
                        elif isinstance(item,MethodNode):
                            child_types=routine_types(item.parameters,class_types,item.body)
                            visit_block(item.body,child_types,statement.name)
                        elif isinstance(item,FunctionNode):
                            child_types=routine_types(item.parameters,class_types,item.body)
                            visit_block(item.body,child_types,statement.name)
                        else:
                            validate_expression(item,class_types,statement.name)
                    continue
                if isinstance(statement,(ConstructorNode,MethodNode)):
                    child_types=routine_types(statement.parameters,visible_types,statement.body)
                    visit_block(statement.body,child_types,current_class)
                    continue
                if isinstance(statement,IfNode):
                    validate_expression(statement.condition,visible_types,current_class)
                    visit_block(statement.then_body,dict(visible_types),current_class)
                    for clause in statement.else_if:
                        validate_expression(clause.condition,visible_types,current_class)
                        visit_block(clause.body,dict(visible_types),current_class)
                    if statement.else_body is not None:
                        visit_block(statement.else_body,dict(visible_types),current_class)
                    continue
                if isinstance(statement,WhileNode):
                    validate_expression(statement.condition,visible_types,current_class)
                    visit_block(statement.body,dict(visible_types),current_class)
                    continue
                if isinstance(statement,ForEachNode):
                    validate_expression(statement.collection,visible_types,current_class)
                    body_types=dict(visible_types)
                    body_types.pop(statement.variable.name,None)
                    visit_block(statement.body,body_types,current_class)
                    continue
                if isinstance(statement,ForRangeNode):
                    validate_expression(statement.start,visible_types,current_class)
                    validate_expression(statement.end,visible_types,current_class)
                    validate_expression(statement.step,visible_types,current_class)
                    body_types=dict(visible_types)
                    body_types.pop(statement.variable.name,None)
                    visit_block(statement.body,body_types,current_class)
                    continue
                if isinstance(statement,TryCatchNode):
                    visit_block(statement.try_body,dict(visible_types),current_class)
                    catch_types=dict(visible_types)
                    if statement.error is not None:
                        catch_types.pop(statement.error.name,None)
                    visit_block(statement.catch_body,catch_types,current_class)
                    continue
                validate_expression(statement,visible_types,current_class)

        visit_block(BlockNode(root.line,root.body),{},None)

    def _validate_explicit_types(self, root:ProgramNode):
        """Reject type errors that are provable from explicit AJ evidence.

        This is intentionally *not* a whole-program type-inference engine.
        Unknown/untyped values remain unknown.  The pass only propagates types
        supplied directly by typed literals/declarations, empty/collection
        literals, and expressions whose result is statically fixed by those
        known operands.  Control-flow joins keep an inferred local type only
        when every path that can reach the join agrees on it.

        The narrow contract follows AJ v1.2 static semantics:
        - operations must use compatible types;
        - IF/WHILE conditions must be Boolean;
        - LIST indexes must be INTEGER.
        """

        numeric_types={'INTEGER','FLOAT'}
        standard_types={
            'INTEGER','FLOAT','STRING','CHAR','BOOLEAN','LIST','TUPLE','SET',
            'DICTIONARY','NONE'
        }

        def normalise_type(name):
            if not name:
                return None
            text=str(name)
            protected_prefix='__reserved_keyword__'
            if text.lower().startswith(protected_prefix.lower()):
                text=text[len(protected_prefix):]
            return text.upper()

        def types_compatible(left, right):
            if left is None or right is None:
                return True
            left=normalise_type(left); right=normalise_type(right)
            if left==right:
                return True
            if left in numeric_types and right in numeric_types:
                return True
            # NONE is a sentinel value; equality/inequality against another
            # type is meaningful even though arithmetic with NONE is not.
            return False

        def arithmetic_result(operator, left, right, line):
            if left is None or right is None:
                # A known non-numeric operand is already enough to prove that
                # numeric-only operators cannot be valid.  For '+' STRING is
                # additionally an explicitly supported concatenation shape in
                # the accepted corpus/canonical pipeline.
                known=left if left is not None else right
                if operator=='+' and known=='STRING':
                    return None
                if known is not None and known not in numeric_types:
                    raise SemanticError(
                        f"Operator {operator!r} has incompatible operand type {known} at line {line}."
                    )
                return None

            if operator=='+':
                if left=='STRING' and right=='STRING':
                    return 'STRING'
                if left in numeric_types and right in numeric_types:
                    return 'FLOAT' if 'FLOAT' in {left,right} else 'INTEGER'
                raise SemanticError(
                    f"Operator '+' has incompatible operand types {left} and {right} at line {line}."
                )

            if left not in numeric_types or right not in numeric_types:
                raise SemanticError(
                    f"Operator {operator!r} requires numeric operands, found {left} and {right} at line {line}."
                )
            if operator=='/':
                return 'FLOAT'
            if operator in {'INTEGER DIVISION','MODULUS'}:
                # Keep the result exact only when both inputs are explicit
                # INTEGER values.  FLOAT acceptance/rejection for these two
                # operators is not further specified by v1.2, so do not invent
                # a stricter rule here.
                return 'INTEGER' if left==right=='INTEGER' else None
            return 'FLOAT' if 'FLOAT' in {left,right} else 'INTEGER'

        def comparison_result(operator, left, right, line):
            if operator in {'==','!='}:
                if left is not None and right is not None:
                    if 'NONE' not in {left,right} and not types_compatible(left,right):
                        raise SemanticError(
                            f"Comparison {operator!r} has incompatible operand types {left} and {right} at line {line}."
                        )
                return 'BOOLEAN'
            if operator in {'<','>','<=','>='}:
                if left is not None and right is not None and not types_compatible(left,right):
                    raise SemanticError(
                        f"Comparison {operator!r} has incompatible operand types {left} and {right} at line {line}."
                    )
                return 'BOOLEAN'
            if operator in {'IN','NOT IN'}:
                return 'BOOLEAN'
            return None

        def infer_expression(node, inferred:dict[str,str], declared:dict[str,str], property_types:dict[str,str]):
            if node is None:
                return None
            if isinstance(node,LiteralNode):
                return normalise_type(node.data_type)
            if isinstance(node,EmptyLiteralNode):
                return normalise_type(node.empty_type)
            if isinstance(node,IdentifierNode):
                return declared.get(node.name) or inferred.get(node.name)
            if isinstance(node,ListLiteralNode):
                declared_item=normalise_type(node.declared_type)
                for item in node.items:
                    item_type=infer_expression(item,inferred,declared,property_types)
                    if declared_item is not None and item_type is not None and not types_compatible(declared_item,item_type):
                        raise SemanticError(
                            f"LIST OF {declared_item} contains incompatible {item_type} value at line {item.line}."
                        )
                return 'LIST'
            if isinstance(node,SetLiteralNode):
                for item in node.items:
                    infer_expression(item,inferred,declared,property_types)
                return 'SET'
            if isinstance(node,TupleLiteralNode):
                for item in node.items:
                    infer_expression(item,inferred,declared,property_types)
                return 'TUPLE'
            if isinstance(node,UnaryNode):
                operand=infer_expression(node.operand,inferred,declared,property_types)
                if node.operator=='NOT':
                    if operand is not None and operand!='BOOLEAN':
                        raise SemanticError(
                            f"Operator 'NOT' requires BOOLEAN operand, found {operand} at line {node.line}."
                        )
                    return 'BOOLEAN'
                if node.operator=='-':
                    if operand is not None and operand not in numeric_types:
                        raise SemanticError(
                            f"Unary '-' requires numeric operand, found {operand} at line {node.line}."
                        )
                    return operand if operand in numeric_types else None
                return None
            if isinstance(node,BinaryNode):
                left=infer_expression(node.left,inferred,declared,property_types)
                right=infer_expression(node.right,inferred,declared,property_types)
                if node.operator in {'+','-','*','/','INTEGER DIVISION','MODULUS','EXP'}:
                    return arithmetic_result(node.operator,left,right,node.line)
                if node.operator in {'AND','OR','XOR'}:
                    for typ in (left,right):
                        if typ is not None and typ!='BOOLEAN':
                            raise SemanticError(
                                f"Operator {node.operator!r} requires BOOLEAN operands, found {typ} at line {node.line}."
                            )
                    return 'BOOLEAN'
                if node.operator in {'==','!=','<','>','<=','>=','IN','NOT IN'}:
                    return comparison_result(node.operator,left,right,node.line)
                return None
            if isinstance(node,IndexNode):
                collection_type=infer_expression(node.collection,inferred,declared,property_types)
                index_type=infer_expression(node.index,inferred,declared,property_types)
                if collection_type=='LIST' and index_type is not None and index_type!='INTEGER':
                    raise SemanticError(
                        f"LIST index must be INTEGER, found {index_type} at line {node.line}."
                    )
                if collection_type=='DICTIONARY' and index_type in {'LIST','SET','DICTIONARY'}:
                    raise SemanticError(
                        f"DICTIONARY key has definitely unhashable type {index_type} at line {node.line}."
                    )
                return None
            if isinstance(node,MemberAccessNode):
                infer_expression(node.object,inferred,declared,property_types)
                if (
                    isinstance(node.object,IdentifierNode)
                    and node.object.name.upper()=='THIS'
                ):
                    return property_types.get(node.member)
                return None
            if isinstance(node,MemberCallNode):
                infer_expression(node.object,inferred,declared,property_types)
                for argument in node.arguments:
                    infer_expression(argument,inferred,declared,property_types)
                return None
            if isinstance(node,CastNode):
                infer_expression(node.expression,inferred,declared,property_types)
                return node.target_type
            if isinstance(node,IsInstanceNode):
                infer_expression(node.expression,inferred,declared,property_types)
                return 'BOOLEAN'
            if isinstance(node,CallNode):
                for argument in node.arguments:
                    infer_expression(argument,inferred,declared,property_types)
                return None
            if isinstance(node,InputNode):
                infer_expression(node.prompt,inferred,declared,property_types)
                return None
            if isinstance(node,LengthNode):
                infer_expression(node.expression,inferred,declared,property_types)
                return 'INTEGER'
            if isinstance(node,JoinNode):
                infer_expression(node.collection,inferred,declared,property_types)
                infer_expression(node.separator,inferred,declared,property_types)
                return 'STRING'
            if isinstance(node,SetOperationNode):
                left_type=infer_expression(node.left,inferred,declared,property_types)
                right_type=infer_expression(node.right,inferred,declared,property_types)
                for operand_type in (left_type,right_type):
                    if operand_type is not None and operand_type!='SET':
                        raise SemanticError(
                            f"{node.operation} requires SET operands, found {operand_type} at line {node.line}."
                        )
                return 'SET'
            if isinstance(node,RandomExpressionNode):
                if node.random_type=='BOOLEAN':
                    return 'BOOLEAN'
                minimum_type=infer_expression(node.minimum,inferred,declared,property_types)
                maximum_type=infer_expression(node.maximum,inferred,declared,property_types)
                if node.random_type=='INT':
                    for bound_type in (minimum_type,maximum_type):
                        if bound_type is not None and bound_type!='INTEGER':
                            raise SemanticError(
                                f"RANDOM INT bounds must be INTEGER, found {bound_type} at line {node.line}."
                            )
                    return 'INTEGER'
                if node.random_type=='FLOAT':
                    for bound_type in (minimum_type,maximum_type):
                        if bound_type is not None and bound_type not in numeric_types:
                            raise SemanticError(
                                f"RANDOM FLOAT bounds must be numeric, found {bound_type} at line {node.line}."
                            )
                    return 'FLOAT'
                return None
            if isinstance(node,GetNode):
                infer_expression(node.dictionary,inferred,declared,property_types)
                infer_expression(node.key,inferred,declared,property_types)
                infer_expression(node.default,inferred,declared,property_types)
                return None
            if isinstance(node,(RemoveFirstExpressionNode,RemoveLastExpressionNode)):
                collection_type=infer_expression(node.collection,inferred,declared,property_types)
                if collection_type is not None and collection_type!='LIST':
                    raise SemanticError(
                        f"REMOVE FIRST/LAST requires LIST collection, found {collection_type} at line {node.line}."
                    )
                return None
            # Statement nodes may be reached through generic recursion in a
            # few compatibility AST shapes.  Validate their expression
            # children without inventing a result type.
            for child in node.children():
                infer_expression(child,inferred,declared,property_types)
            return None

        def require_boolean(node, inferred, declared, property_types, context):
            typ=infer_expression(node,inferred,declared,property_types)
            if typ is not None and typ!='BOOLEAN':
                raise SemanticError(
                    f"{context} condition must be BOOLEAN, found {typ} at line {node.line}."
                )

        def refine_true_types(condition, state:dict[str,str], declared:dict[str,str]):
            """Conservatively narrow untyped locals proven by ISINSTANCE.

            AJ v1.4 type inspection can make an otherwise mixed-type branch
            statically safe.  A single target gives an exact branch-local
            type.  A multi-target test preserves an already-compatible known
            type; otherwise the value becomes unknown rather than inventing a
            union-type system.  AND combines proven refinements from both
            operands.  OR/NOT are deliberately not narrowed.
            """
            refined=dict(state)
            if isinstance(condition,IsInstanceNode) and isinstance(condition.expression,IdentifierNode):
                name=condition.expression.name
                if name in declared:
                    return refined
                targets=[normalise_type(item) for item in condition.type_names]
                targets=[item for item in targets if item is not None]
                if len(targets)==1:
                    refined[name]=targets[0]
                else:
                    current=refined.get(name)
                    if current not in targets:
                        refined.pop(name,None)
                return refined
            if isinstance(condition,BinaryNode) and condition.operator=='AND':
                refined=refine_true_types(condition.left,refined,declared)
                refined=refine_true_types(condition.right,refined,declared)
            return refined

        def merge_type_states(states:list[dict[str,str]]):
            if not states:
                return {}
            common=set(states[0])
            for state in states[1:]:
                common.intersection_update(state)
            return {
                name:states[0][name]
                for name in common
                if all(state.get(name)==states[0][name] for state in states[1:])
            }

        def statement_falls_through(statement)->bool:
            if isinstance(statement,(ReturnNode,RaiseNode,BreakNode,ContinueNode)):
                return False
            if isinstance(statement,IfNode):
                if statement.else_body is None:
                    return True
                branches=[statement.then_body]
                branches.extend(clause.body for clause in statement.else_if)
                branches.append(statement.else_body)
                return any(block_falls_through(branch) for branch in branches)
            if isinstance(statement,TryCatchNode):
                return block_falls_through(statement.try_body) or block_falls_through(statement.catch_body)
            return True

        def block_falls_through(block:BlockNode)->bool:
            for statement in block.statements:
                if not statement_falls_through(statement):
                    return False
            return True

        def parameter_state(parameters, outer_inferred, outer_declared):
            inferred=dict(outer_inferred)
            declared=dict(outer_declared)
            for parameter in parameters:
                # Every parameter shadows an outer local of the same name. A
                # declared parameter type remains known; an untyped parameter
                # deliberately becomes unknown.
                inferred.pop(parameter.name,None)
                declared.pop(parameter.name,None)
                typ=normalise_type(parameter.declared_type)
                if typ is not None:
                    declared[parameter.name]=typ
            return inferred,declared

        def visit_block(block:BlockNode, inferred:dict[str,str], declared:dict[str,str], property_types:dict[str,str]):
            state=dict(inferred)
            for statement in block.statements:
                if isinstance(statement,AssignmentNode):
                    # Validate indexed/member targets as expressions too, e.g.
                    # a statically known LIST with a non-INTEGER index.
                    if isinstance(statement.target,(IndexNode,MemberAccessNode)):
                        infer_expression(statement.target,state,declared,property_types)
                    value_type=infer_expression(statement.value,state,declared,property_types)
                    if isinstance(statement.target,IdentifierNode):
                        if statement.target.name not in declared:
                            if value_type is None:
                                state.pop(statement.target.name,None)
                            else:
                                state[statement.target.name]=value_type
                    continue

                if isinstance(statement,PropertyAssignmentNode):
                    infer_expression(statement.target,state,declared,property_types)
                    infer_expression(statement.value,state,declared,property_types)
                    continue

                if isinstance(statement,OutputNode):
                    infer_expression(statement.expression,state,declared,property_types)
                    continue

                if isinstance(statement,ReturnNode):
                    infer_expression(statement.expression,state,declared,property_types)
                    continue

                if isinstance(statement,IfNode):
                    require_boolean(statement.condition,state,declared,property_types,'IF')
                    incoming=dict(state)
                    outputs=[]
                    then_state=refine_true_types(statement.condition,incoming,declared)
                    then_out=visit_block(statement.then_body,then_state,declared,property_types)
                    if block_falls_through(statement.then_body):
                        outputs.append(then_out)
                    for clause in statement.else_if:
                        require_boolean(clause.condition,incoming,declared,property_types,'ELSE IF')
                        clause_state=refine_true_types(clause.condition,incoming,declared)
                        clause_out=visit_block(clause.body,clause_state,declared,property_types)
                        if block_falls_through(clause.body):
                            outputs.append(clause_out)
                    if statement.else_body is not None:
                        else_out=visit_block(statement.else_body,incoming,declared,property_types)
                        if block_falls_through(statement.else_body):
                            outputs.append(else_out)
                    else:
                        outputs.append(incoming)
                    state=merge_type_states(outputs) if outputs else {}
                    continue

                if isinstance(statement,WhileNode):
                    require_boolean(statement.condition,state,declared,property_types,'WHILE')
                    incoming=dict(state)
                    body_out=visit_block(statement.body,incoming,declared,property_types)
                    # The loop may run zero times, so retain only types that
                    # agree both before the loop and after a normal iteration.
                    state=merge_type_states([incoming,body_out])
                    continue

                if isinstance(statement,ForEachNode):
                    infer_expression(statement.collection,state,declared,property_types)
                    incoming=dict(state)
                    body_state=dict(incoming)
                    body_state.pop(statement.variable.name,None)
                    body_declared=dict(declared)
                    body_declared.pop(statement.variable.name,None)
                    body_out=visit_block(statement.body,body_state,body_declared,property_types)
                    body_out.pop(statement.variable.name,None)
                    state=merge_type_states([incoming,body_out])
                    state.pop(statement.variable.name,None)
                    continue

                if isinstance(statement,ForRangeNode):
                    infer_expression(statement.start,state,declared,property_types)
                    infer_expression(statement.end,state,declared,property_types)
                    infer_expression(statement.step,state,declared,property_types)
                    incoming=dict(state)
                    body_state=dict(incoming)
                    body_state.pop(statement.variable.name,None)
                    body_declared=dict(declared)
                    body_declared.pop(statement.variable.name,None)
                    body_out=visit_block(statement.body,body_state,body_declared,property_types)
                    body_out.pop(statement.variable.name,None)
                    state=merge_type_states([incoming,body_out])
                    state.pop(statement.variable.name,None)
                    continue

                if isinstance(statement,CallNode):
                    infer_expression(statement,state,declared,property_types)
                    continue

                if isinstance(statement,AppendNode):
                    infer_expression(statement.value,state,declared,property_types)
                    collection_type=infer_expression(statement.collection,state,declared,property_types)
                    if collection_type is not None and collection_type not in {'LIST','SET'}:
                        raise SemanticError(
                            f"APPEND requires LIST or SET collection, found {collection_type} at line {statement.line}."
                        )
                    continue

                if isinstance(statement,InsertNode):
                    infer_expression(statement.value,state,declared,property_types)
                    collection_type=infer_expression(statement.collection,state,declared,property_types)
                    index_type=infer_expression(statement.index,state,declared,property_types)
                    if collection_type is not None and collection_type!='LIST':
                        raise SemanticError(
                            f"INSERT requires LIST collection, found {collection_type} at line {statement.line}."
                        )
                    if index_type is not None and index_type!='INTEGER':
                        raise SemanticError(
                            f"INSERT index must be INTEGER, found {index_type} at line {statement.line}."
                        )
                    continue

                if isinstance(statement,RemoveValueNode):
                    infer_expression(statement.value,state,declared,property_types)
                    collection_type=infer_expression(statement.collection,state,declared,property_types)
                    if collection_type is not None and collection_type not in {'LIST','SET'}:
                        raise SemanticError(
                            f"REMOVE value requires LIST or SET collection, found {collection_type} at line {statement.line}."
                        )
                    continue

                if isinstance(statement,(RemoveFirstNode,RemoveLastNode)):
                    collection_type=infer_expression(statement.collection,state,declared,property_types)
                    if collection_type is not None and collection_type!='LIST':
                        raise SemanticError(
                            f"REMOVE FIRST/LAST requires LIST collection, found {collection_type} at line {statement.line}."
                        )
                    continue

                if isinstance(statement,RaiseNode):
                    infer_expression(statement.expression,state,declared,property_types)
                    continue

                if isinstance(statement,TryCatchNode):
                    incoming=dict(state)
                    try_out=visit_block(statement.try_body,incoming,declared,property_types)
                    catch_state=dict(incoming)
                    catch_declared=dict(declared)
                    if statement.error is not None:
                        catch_state.pop(statement.error.name,None)
                        catch_declared.pop(statement.error.name,None)
                    catch_out=visit_block(statement.catch_body,catch_state,catch_declared,property_types)
                    if statement.error is not None:
                        catch_out.pop(statement.error.name,None)
                    outputs=[]
                    if block_falls_through(statement.try_body):
                        outputs.append(try_out)
                    if block_falls_through(statement.catch_body):
                        outputs.append(catch_out)
                    state=merge_type_states(outputs) if outputs else {}
                    continue

                if isinstance(statement,FunctionNode):
                    child_inferred,child_declared=parameter_state(statement.parameters,state,declared)
                    visit_block(statement.body,child_inferred,child_declared,property_types)
                    # A function declaration binds a callable name, not a
                    # typed data value for expression arithmetic.
                    state.pop(statement.name,None)
                    continue

                if isinstance(statement,ClassNode):
                    class_properties={
                        item.name:normalise_type(item.declared_type)
                        for item in statement.body.statements
                        if isinstance(item,PropertyDeclarationNode) and item.declared_type
                    }
                    class_inferred,class_declared=parameter_state(statement.parameters,state,declared)
                    for item in statement.body.statements:
                        if isinstance(item,AssignmentNode):
                            value_type=infer_expression(item.value,class_inferred,class_declared,class_properties)
                            if isinstance(item.target,IdentifierNode) and item.target.name not in class_declared:
                                if value_type is None:
                                    class_inferred.pop(item.target.name,None)
                                else:
                                    class_inferred[item.target.name]=value_type
                        elif isinstance(item,PropertyAssignmentNode):
                            infer_expression(item.value,class_inferred,class_declared,class_properties)
                        elif isinstance(item,ConstructorNode):
                            local_i,local_d=parameter_state(item.parameters,class_inferred,class_declared)
                            visit_block(item.body,local_i,local_d,class_properties)
                        elif isinstance(item,MethodNode):
                            local_i,local_d=parameter_state(item.parameters,class_inferred,class_declared)
                            visit_block(item.body,local_i,local_d,class_properties)
                        elif isinstance(item,FunctionNode):
                            local_i,local_d=parameter_state(item.parameters,class_inferred,class_declared)
                            visit_block(item.body,local_i,local_d,class_properties)
                    state.pop(statement.name,None)
                    continue

                if isinstance(statement,(ConstructorNode,MethodNode)):
                    local_i,local_d=parameter_state(statement.parameters,state,declared)
                    visit_block(statement.body,local_i,local_d,property_types)
                    continue

            return state

        visit_block(BlockNode(root.line,root.body),{}, {}, {})

    def _validate_join_compatibility(self, root:ProgramNode):
        """Conservatively validate JOIN text compatibility.

        AJ v1.2 defines ``JOIN(collection, separator)`` but does not specify an
        implicit element-to-string conversion.  Keep unknown collection
        element types unknown, and reject only cases where explicit evidence
        proves that a separator or every element of a homogeneous LIST is
        non-text.  STRING and CHAR are both Python ``str`` backed in the
        compiler and are therefore text-compatible here.
        """

        text_types={'STRING','CHAR'}
        scalar_types={'INTEGER','FLOAT','STRING','CHAR','BOOLEAN','LIST','SET','TUPLE','DICTIONARY','NONE'}

        def normalise_type(name):
            if not name:
                return None
            text=str(name)
            protected_prefix='__reserved_keyword__'
            if text.lower().startswith(protected_prefix.lower()):
                text=text[len(protected_prefix):]
            return text.upper()

        def literal_type(node):
            if node is None:
                return None
            if isinstance(node,LiteralNode):
                return normalise_type(node.data_type)
            if isinstance(node,EmptyLiteralNode):
                return normalise_type(node.empty_type)
            if isinstance(node,ListLiteralNode):
                return 'LIST'
            if isinstance(node,SetLiteralNode):
                return 'SET'
            if isinstance(node,TupleLiteralNode):
                return 'TUPLE'
            if isinstance(node,LengthNode):
                return 'INTEGER'
            if isinstance(node,JoinNode):
                return 'STRING'
            if isinstance(node,SetOperationNode):
                return 'SET'
            if isinstance(node,RandomExpressionNode):
                return {'INT':'INTEGER','FLOAT':'FLOAT','BOOLEAN':'BOOLEAN'}.get(node.random_type)
            return None

        def expression_type(node, value_types):
            direct=literal_type(node)
            if direct is not None:
                return direct
            if isinstance(node,IdentifierNode):
                return value_types.get(node.name)
            if isinstance(node,UnaryNode):
                inner=expression_type(node.operand,value_types)
                if node.operator=='NOT':
                    return 'BOOLEAN'
                if node.operator=='-' and inner in {'INTEGER','FLOAT'}:
                    return inner
                return None
            if isinstance(node,BinaryNode):
                left=expression_type(node.left,value_types)
                right=expression_type(node.right,value_types)
                if node.operator in {'==','!=','<','>','<=','>=','IN','NOT IN','AND','OR','XOR'}:
                    return 'BOOLEAN'
                if node.operator=='+' and left==right=='STRING':
                    return 'STRING'
                if node.operator in {'+','-','*','EXP'} and left in {'INTEGER','FLOAT'} and right in {'INTEGER','FLOAT'}:
                    return 'FLOAT' if 'FLOAT' in {left,right} else 'INTEGER'
                if node.operator=='/' and left in {'INTEGER','FLOAT'} and right in {'INTEGER','FLOAT'}:
                    return 'FLOAT'
                if node.operator in {'INTEGER DIVISION','MODULUS'} and left==right=='INTEGER':
                    return 'INTEGER'
            return None

        def homogeneous_list_element_type(node, value_types, element_types):
            if isinstance(node,IdentifierNode):
                return element_types.get(node.name)
            if not isinstance(node,ListLiteralNode):
                return None
            declared=normalise_type(node.declared_type)
            if declared is not None:
                return declared
            if not node.items:
                return None
            known=[]
            for item in node.items:
                typ=expression_type(item,value_types)
                if typ is None:
                    return None
                known.append(typ)
            first=known[0]
            if all(typ==first for typ in known):
                return first
            if all(typ in text_types for typ in known):
                return 'STRING'
            return None

        def merge(states):
            if not states:
                return {},{}
            value_states=[state[0] for state in states]
            element_states=[state[1] for state in states]
            value_names=set(value_states[0])
            element_names=set(element_states[0])
            for state in value_states[1:]: value_names.intersection_update(state)
            for state in element_states[1:]: element_names.intersection_update(state)
            values={
                name:value_states[0][name]
                for name in value_names
                if all(state.get(name)==value_states[0][name] for state in value_states[1:])
            }
            elements={
                name:element_states[0][name]
                for name in element_names
                if all(state.get(name)==element_states[0][name] for state in element_states[1:])
            }
            return values,elements

        def statement_falls_through(statement):
            if isinstance(statement,(ReturnNode,RaiseNode,BreakNode,ContinueNode)):
                return False
            if isinstance(statement,IfNode):
                if statement.else_body is None:
                    return True
                branches=[statement.then_body]
                branches.extend(clause.body for clause in statement.else_if)
                branches.append(statement.else_body)
                return any(block_falls_through(branch) for branch in branches)
            if isinstance(statement,TryCatchNode):
                return block_falls_through(statement.try_body) or block_falls_through(statement.catch_body)
            return True

        def block_falls_through(block):
            for statement in block.statements:
                if not statement_falls_through(statement):
                    return False
            return True

        def validate_expression(node, value_types, element_types):
            if node is None:
                return
            if isinstance(node,JoinNode):
                separator_type=expression_type(node.separator,value_types)
                if separator_type is not None and separator_type not in text_types:
                    raise SemanticError(
                        f"JOIN separator must be STRING/CHAR-compatible, found {separator_type} at line {node.line}."
                    )
                element_type=homogeneous_list_element_type(node.collection,value_types,element_types)
                if element_type is not None and element_type not in text_types:
                    raise SemanticError(
                        f"JOIN collection elements must be STRING/CHAR-compatible, found {element_type} at line {node.line}."
                    )
            for child in node.children():
                validate_expression(child,value_types,element_types)

        def visit_block(block, value_types, element_types):
            values=dict(value_types)
            elements=dict(element_types)
            for statement in block.statements:
                if isinstance(statement,AssignmentNode) and isinstance(statement.target,IdentifierNode):
                    validate_expression(statement.value,values,elements)
                    name=statement.target.name
                    typ=expression_type(statement.value,values)
                    if typ is None:
                        values.pop(name,None)
                    else:
                        values[name]=typ
                    elem=homogeneous_list_element_type(statement.value,values,elements)
                    if elem is None:
                        elements.pop(name,None)
                    else:
                        elements[name]=elem
                    continue
                if isinstance(statement,FunctionNode):
                    child_values=dict(values); child_elements=dict(elements)
                    # Local assignments and parameters shadow enclosing evidence.
                    local_names=set()
                    stack=list(statement.body.statements)
                    while stack:
                        item=stack.pop()
                        if isinstance(item,AssignmentNode) and isinstance(item.target,IdentifierNode):
                            local_names.add(item.target.name)
                        if isinstance(item,FunctionNode):
                            continue
                        stack.extend(item.children())
                    for name in local_names:
                        child_values.pop(name,None); child_elements.pop(name,None)
                    for parameter in statement.parameters:
                        child_values.pop(parameter.name,None); child_elements.pop(parameter.name,None)
                        declared=normalise_type(parameter.declared_type)
                        if declared is not None:
                            child_values[parameter.name]=declared
                    visit_block(statement.body,child_values,child_elements)
                    continue
                if isinstance(statement,ClassNode):
                    for item in statement.body.statements:
                        if isinstance(item,(ConstructorNode,MethodNode,FunctionNode)):
                            child_values=dict(values); child_elements=dict(elements)
                            for parameter in item.parameters:
                                child_values.pop(parameter.name,None); child_elements.pop(parameter.name,None)
                                declared=normalise_type(parameter.declared_type)
                                if declared is not None:
                                    child_values[parameter.name]=declared
                            visit_block(item.body,child_values,child_elements)
                        else:
                            validate_expression(item,values,elements)
                    continue
                if isinstance(statement,(ConstructorNode,MethodNode)):
                    child_values=dict(values); child_elements=dict(elements)
                    for parameter in statement.parameters:
                        child_values.pop(parameter.name,None); child_elements.pop(parameter.name,None)
                        declared=normalise_type(parameter.declared_type)
                        if declared is not None:
                            child_values[parameter.name]=declared
                    visit_block(statement.body,child_values,child_elements)
                    continue
                if isinstance(statement,IfNode):
                    validate_expression(statement.condition,values,elements)
                    incoming=(dict(values),dict(elements)); outputs=[]
                    then_out=visit_block(statement.then_body,*incoming)
                    if block_falls_through(statement.then_body): outputs.append(then_out)
                    for clause in statement.else_if:
                        clause_out=visit_block(clause.body,*incoming)
                        if block_falls_through(clause.body): outputs.append(clause_out)
                    if statement.else_body is not None:
                        else_out=visit_block(statement.else_body,*incoming)
                        if block_falls_through(statement.else_body): outputs.append(else_out)
                    else:
                        outputs.append(incoming)
                    values,elements=merge(outputs) if outputs else ({},{})
                    continue
                if isinstance(statement,(WhileNode,ForEachNode,ForRangeNode)):
                    if isinstance(statement,WhileNode):
                        validate_expression(statement.condition,values,elements)
                    elif isinstance(statement,ForEachNode):
                        validate_expression(statement.collection,values,elements)
                    else:
                        validate_expression(statement.start,values,elements)
                        validate_expression(statement.end,values,elements)
                        validate_expression(statement.step,values,elements)
                    incoming=(dict(values),dict(elements))
                    body_values=dict(values); body_elements=dict(elements)
                    if isinstance(statement,(ForEachNode,ForRangeNode)):
                        body_values.pop(statement.variable.name,None)
                        body_elements.pop(statement.variable.name,None)
                    body_out=visit_block(statement.body,body_values,body_elements)
                    values,elements=merge([incoming,body_out])
                    if isinstance(statement,(ForEachNode,ForRangeNode)):
                        values.pop(statement.variable.name,None); elements.pop(statement.variable.name,None)
                    continue
                if isinstance(statement,TryCatchNode):
                    incoming=(dict(values),dict(elements)); outputs=[]
                    try_out=visit_block(statement.try_body,*incoming)
                    if block_falls_through(statement.try_body): outputs.append(try_out)
                    catch_values=dict(values); catch_elements=dict(elements)
                    if statement.error is not None:
                        catch_values.pop(statement.error.name,None); catch_elements.pop(statement.error.name,None)
                    catch_out=visit_block(statement.catch_body,catch_values,catch_elements)
                    if block_falls_through(statement.catch_body): outputs.append(catch_out)
                    values,elements=merge(outputs) if outputs else ({},{})
                    continue
                validate_expression(statement,values,elements)
            return values,elements

        visit_block(BlockNode(root.line,root.body),{}, {})

    def _validate_declared_type_entries(self, root:ProgramNode):
        """Enforce explicitly declared target/parameter types at value entry.

        AJ v1.2 permits parameters and properties to carry declared types and
        requires compatible types.  This pass intentionally checks only cases
        where both the destination declaration/signature and the supplied
        value type are statically explicit.  Untyped/unknown values remain
        unknown; no coercion or protocol inference is introduced.
        """

        numeric_types={'INTEGER','FLOAT'}

        def normalise_type(name):
            if not name:
                return None
            text=str(name)
            protected_prefix='__reserved_keyword__'
            if text.lower().startswith(protected_prefix.lower()):
                text=text[len(protected_prefix):]
            upper=text.upper()
            standard={
                'INTEGER','FLOAT','STRING','CHAR','BOOLEAN','LIST','TUPLE',
                'SET','DICTIONARY','NONE'
            }
            return upper if upper in standard else text

        def compatible(expected, supplied):
            if expected is None or supplied is None:
                return True
            expected=normalise_type(expected); supplied=normalise_type(supplied)
            if expected==supplied:
                return True
            return expected in numeric_types and supplied in numeric_types

        classes={
            statement.name:statement
            for statement in root.body
            if isinstance(statement,ClassNode)
        }
        property_types={
            class_name:{
                item.name:normalise_type(item.declared_type)
                for item in class_node.body.statements
                if isinstance(item,PropertyDeclarationNode) and item.declared_type
            }
            for class_name,class_node in classes.items()
        }
        method_signatures={
            class_name:{
                item.name:[normalise_type(p.declared_type) for p in item.parameters]
                for item in class_node.body.statements
                if isinstance(item,MethodNode)
            }
            for class_name,class_node in classes.items()
        }

        def local_assignment_names(block:BlockNode)->set[str]:
            names=set()
            def visit(current:BlockNode):
                for statement in current.statements:
                    if isinstance(statement,AssignmentNode) and isinstance(statement.target,IdentifierNode):
                        names.add(statement.target.name)
                    elif isinstance(statement,IfNode):
                        visit(statement.then_body)
                        for clause in statement.else_if:
                            visit(clause.body)
                        if statement.else_body is not None:
                            visit(statement.else_body)
                    elif isinstance(statement,(WhileNode,ForEachNode,ForRangeNode)):
                        visit(statement.body)
                    elif isinstance(statement,TryCatchNode):
                        visit(statement.try_body); visit(statement.catch_body)
                    # Nested routines/classes establish distinct local scopes.
            visit(block)
            return names

        def signatures_for(block:BlockNode, inherited):
            visible=dict(inherited)
            for statement in block.statements:
                if isinstance(statement,FunctionNode):
                    visible[statement.name]=[
                        normalise_type(p.declared_type) for p in statement.parameters
                    ]
            return visible

        def routine_types(parameters, inherited:dict[str,str], body:BlockNode):
            visible=dict(inherited)
            # Simple assignments in a nested routine bind locals and therefore
            # shadow same-named explicit types from enclosing lexical scopes.
            for name in local_assignment_names(body):
                visible.pop(name,None)
            for parameter in parameters:
                visible.pop(parameter.name,None)
                typ=normalise_type(parameter.declared_type)
                if typ is not None:
                    visible[parameter.name]=typ
            return visible

        def receiver_class(node, visible_types:dict[str,str], current_class):
            if isinstance(node,IdentifierNode):
                if node.name.upper()=='THIS':
                    return current_class
                typ=visible_types.get(node.name)
                return typ if typ in classes else None
            if isinstance(node,MemberAccessNode):
                owner=receiver_class(node.object,visible_types,current_class)
                if owner is None:
                    return None
                typ=property_types.get(owner,{}).get(node.member)
                return typ if typ in classes else None
            return None

        def known_type(node, visible_types:dict[str,str], current_class):
            if node is None:
                return None
            if isinstance(node,LiteralNode):
                return normalise_type(node.data_type)
            if isinstance(node,EmptyLiteralNode):
                return normalise_type(node.empty_type)
            if isinstance(node,IdentifierNode):
                return visible_types.get(node.name)
            if isinstance(node,ListLiteralNode):
                return 'LIST'
            if isinstance(node,SetLiteralNode):
                return 'SET'
            if isinstance(node,TupleLiteralNode):
                return 'TUPLE'
            if isinstance(node,RandomExpressionNode):
                return {'INT':'INTEGER','FLOAT':'FLOAT','BOOLEAN':'BOOLEAN'}.get(node.random_type)
            if isinstance(node,LengthNode):
                return 'INTEGER'
            if isinstance(node,JoinNode):
                return 'STRING'
            if isinstance(node,SetOperationNode):
                return 'SET'
            if isinstance(node,MemberAccessNode):
                owner=receiver_class(node.object,visible_types,current_class)
                if owner is not None:
                    return property_types.get(owner,{}).get(node.member)
                return None
            if isinstance(node,UnaryNode):
                operand=known_type(node.operand,visible_types,current_class)
                if node.operator=='NOT':
                    return 'BOOLEAN'
                if node.operator=='-' and operand in numeric_types:
                    return operand
                return None
            if isinstance(node,CastNode):
                known_type(node.expression,visible_types,current_class)
                return node.target_type
            if isinstance(node,IsInstanceNode):
                known_type(node.expression,visible_types,current_class)
                return 'BOOLEAN'
            if isinstance(node,BinaryNode):
                left=known_type(node.left,visible_types,current_class)
                right=known_type(node.right,visible_types,current_class)
                if node.operator in {'==','!=','<','>','<=','>=','IN','NOT IN','AND','OR','XOR'}:
                    return 'BOOLEAN'
                if node.operator=='+' and left==right=='STRING':
                    return 'STRING'
                if node.operator in {'+','-','*','EXP'} and left in numeric_types and right in numeric_types:
                    return 'FLOAT' if 'FLOAT' in {left,right} else 'INTEGER'
                if node.operator=='/' and left in numeric_types and right in numeric_types:
                    return 'FLOAT'
                if node.operator in {'INTEGER DIVISION','MODULUS'} and left==right=='INTEGER':
                    return 'INTEGER'
                return None
            return None

        def check_value(expected, value, visible_types, current_class, context, line):
            supplied=known_type(value,visible_types,current_class)
            if expected is not None and supplied is not None and not compatible(expected,supplied):
                raise SemanticError(
                    f"{context} expects {normalise_type(expected)}, found {normalise_type(supplied)} at line {line}."
                )

        def validate_expression(node, function_signatures, visible_types, current_class):
            if node is None:
                return
            if isinstance(node,(CastNode,IsInstanceNode)):
                validate_expression(node.expression,function_signatures,visible_types,current_class)
                return
            if isinstance(node,CallNode):
                signature=function_signatures.get(node.name)
                if signature is not None and len(signature)==len(node.arguments):
                    for parameter_type,argument in zip(signature,node.arguments):
                        check_value(
                            parameter_type,argument,visible_types,current_class,
                            f"Argument to function {node.name!r}",node.line
                        )
                for argument in node.arguments:
                    validate_expression(argument,function_signatures,visible_types,current_class)
                return
            if isinstance(node,MemberCallNode):
                validate_expression(node.object,function_signatures,visible_types,current_class)
                owner=receiver_class(node.object,visible_types,current_class)
                signature=method_signatures.get(owner,{}).get(node.member) if owner is not None else None
                if signature is not None and len(signature)==len(node.arguments):
                    for parameter_type,argument in zip(signature,node.arguments):
                        check_value(
                            parameter_type,argument,visible_types,current_class,
                            f"Argument to method {owner}.{node.member}",node.line
                        )
                for argument in node.arguments:
                    validate_expression(argument,function_signatures,visible_types,current_class)
                return
            for child in node.children():
                validate_expression(child,function_signatures,visible_types,current_class)

        def visit_block(block:BlockNode, inherited_signatures, inherited_types, current_class):
            signatures=signatures_for(block,inherited_signatures)
            visible_types=dict(inherited_types)
            for statement in block.statements:
                if isinstance(statement,AssignmentNode):
                    validate_expression(statement.value,signatures,visible_types,current_class)
                    if isinstance(statement.target,IdentifierNode):
                        expected=visible_types.get(statement.target.name)
                        # Only an explicit routine parameter declaration makes
                        # this assignment a declared-type entry point.  Locals
                        # inherited from enclosing routines were removed by
                        # routine_types when shadowed.
                        if expected is not None:
                            check_value(
                                expected,statement.value,visible_types,current_class,
                                f"Assignment to {statement.target.name!r}",statement.line
                            )
                    else:
                        validate_expression(statement.target,signatures,visible_types,current_class)
                    continue

                if isinstance(statement,PropertyAssignmentNode):
                    validate_expression(statement.value,signatures,visible_types,current_class)
                    owner=receiver_class(statement.target.object,visible_types,current_class)
                    expected=property_types.get(owner,{}).get(statement.target.member) if owner is not None else None
                    if expected is not None:
                        check_value(
                            expected,statement.value,visible_types,current_class,
                            f"Assignment to property {owner}.{statement.target.member}",statement.line
                        )
                    continue

                if isinstance(statement,FunctionNode):
                    child_types=routine_types(statement.parameters,visible_types,statement.body)
                    visit_block(statement.body,signatures,child_types,current_class)
                    continue

                if isinstance(statement,ClassNode):
                    class_types=routine_types(statement.parameters,visible_types,statement.body)
                    class_signatures=signatures_for(statement.body,signatures)
                    for item in statement.body.statements:
                        if isinstance(item,ConstructorNode):
                            child_types=routine_types(item.parameters,class_types,item.body)
                            visit_block(item.body,class_signatures,child_types,statement.name)
                        elif isinstance(item,MethodNode):
                            child_types=routine_types(item.parameters,class_types,item.body)
                            visit_block(item.body,class_signatures,child_types,statement.name)
                        elif isinstance(item,FunctionNode):
                            child_types=routine_types(item.parameters,class_types,item.body)
                            visit_block(item.body,class_signatures,child_types,statement.name)
                        else:
                            validate_expression(item,class_signatures,class_types,statement.name)
                    continue

                if isinstance(statement,(ConstructorNode,MethodNode)):
                    child_types=routine_types(statement.parameters,visible_types,statement.body)
                    visit_block(statement.body,signatures,child_types,current_class)
                    continue

                if isinstance(statement,IfNode):
                    validate_expression(statement.condition,signatures,visible_types,current_class)
                    visit_block(statement.then_body,signatures,dict(visible_types),current_class)
                    for clause in statement.else_if:
                        validate_expression(clause.condition,signatures,visible_types,current_class)
                        visit_block(clause.body,signatures,dict(visible_types),current_class)
                    if statement.else_body is not None:
                        visit_block(statement.else_body,signatures,dict(visible_types),current_class)
                    continue

                if isinstance(statement,WhileNode):
                    validate_expression(statement.condition,signatures,visible_types,current_class)
                    visit_block(statement.body,signatures,dict(visible_types),current_class)
                    continue

                if isinstance(statement,ForEachNode):
                    validate_expression(statement.collection,signatures,visible_types,current_class)
                    body_types=dict(visible_types); body_types.pop(statement.variable.name,None)
                    visit_block(statement.body,signatures,body_types,current_class)
                    continue

                if isinstance(statement,ForRangeNode):
                    for expression in (statement.start,statement.end,statement.step):
                        validate_expression(expression,signatures,visible_types,current_class)
                    body_types=dict(visible_types); body_types.pop(statement.variable.name,None)
                    visit_block(statement.body,signatures,body_types,current_class)
                    continue

                if isinstance(statement,TryCatchNode):
                    visit_block(statement.try_body,signatures,dict(visible_types),current_class)
                    catch_types=dict(visible_types)
                    if statement.error is not None:
                        catch_types.pop(statement.error.name,None)
                    visit_block(statement.catch_body,signatures,catch_types,current_class)
                    continue

                validate_expression(statement,signatures,visible_types,current_class)

        visit_block(BlockNode(root.line,root.body),{}, {}, None)

    def _validate_identifier_bindings(self, root:ProgramNode):
        """Conservatively enforce direct declared/assigned-before-read cases.

        AJ v1.2 retains the declared/assigned-before-read rule from v1.1.
        The validator implements the unambiguous direct-read subset: a bare
        identifier used as an assignment/property RHS, RETURN value, OUTPUT
        value, or immediate CALL argument must already be bound in the visible
        scope.  Control-flow joins are conservative: names introduced on only
        some paths are not considered definitely assigned after the join, and
        loop-body-only assignments do not escape a potentially zero-iteration
        loop.  Compound-expression definite-assignment analysis remains outside
        this deliberately narrow check.

        CallNode routine names are syntax, not IdentifierNode value reads, so
        this check does not turn undefined-routine policy into an import system.
        """

        compatibility_values={'NULL'}

        def statement_falls_through(statement)->bool:
            if isinstance(statement,(ReturnNode,RaiseNode,BreakNode,ContinueNode)):
                return False
            if isinstance(statement,IfNode):
                if statement.else_body is None:
                    return True
                branches=[statement.then_body]
                branches.extend(clause.body for clause in statement.else_if)
                branches.append(statement.else_body)
                return any(block_falls_through(branch) for branch in branches)
            if isinstance(statement,TryCatchNode):
                return (
                    block_falls_through(statement.try_body)
                    or block_falls_through(statement.catch_body)
                )
            return True

        def block_falls_through(block:BlockNode)->bool:
            for statement in block.statements:
                if not statement_falls_through(statement):
                    return False
            return True

        def require_bare_value(node, bound:set[str]):
            if (
                isinstance(node,IdentifierNode)
                and node.name not in bound
                and node.name.upper() not in compatibility_values
            ):
                raise SemanticError(
                    f"Identifier {node.name!r} is read before declaration or assignment at line {node.line}."
                )

        placeholder_re=re.compile(
            r"(?<!\{)\{([A-Za-z_][A-Za-z0-9_]*)\}(?!\})"
        )

        def validate_output_placeholders(node, bound:set[str]):
            """Check only AJ's exact ``{identifier}`` OUTPUT placeholders.

            Other brace contents have no defined interpolation semantics in
            v1.2 and are therefore left as literal text for the compiler.
            """
            if not (
                isinstance(node,LiteralNode)
                and node.data_type=='STRING'
                and isinstance(node.value,str)
            ):
                return
            for match in placeholder_re.finditer(node.value):
                name=match.group(1)
                if name not in bound and name.upper() not in compatibility_values:
                    raise SemanticError(
                        f"STRING placeholder identifier {name!r} is read before declaration or assignment at line {node.line}."
                    )

        def validate_call_argument_values(node, bound:set[str]):
            """Validate the approved immediate-bare CALL argument subset.

            Routine names carried by CallNode.name remain syntax and are not
            treated as value identifiers.  Each immediate argument that is a
            bare IdentifierNode, however, is an ordinary value read and must
            already be bound.  Nested calls are visited so the same rule
            applies wherever a CALL expression occurs, while compound
            arguments such as ``x + missing`` remain outside this deliberately
            narrow definite-assignment extension.
            """
            if node is None:
                return
            if isinstance(node,(CastNode,IsInstanceNode)):
                require_bare_value(node.expression,bound)
                validate_call_argument_values(node.expression,bound)
                return
            if isinstance(node,CallNode):
                for argument in node.arguments:
                    require_bare_value(argument,bound)
                    validate_call_argument_values(argument,bound)
                return
            for child in node.children():
                validate_call_argument_values(child,bound)

        def validate_block(block:BlockNode, incoming:set[str], *, implicit:set[str]|None=None)->set[str]:
            bound=set(incoming)
            if implicit:
                bound.update(implicit)

            for statement in block.statements:
                if isinstance(statement,ImportDirectiveNode):
                    if statement.directive_type == "IMPORT":
                        bound.add(statement.alias or statement.module.split(".", 1)[0])
                    elif statement.directive_type == "FROM_IMPORT":
                        for imported_name in statement.names:
                            if imported_name != "*":
                                bound.add(imported_name)
                    continue

                if isinstance(statement,AssignmentNode):
                    validate_call_argument_values(statement.value,bound)
                    require_bare_value(statement.value,bound)
                    if isinstance(statement.target,IdentifierNode):
                        bound.add(statement.target.name)
                    continue

                if isinstance(statement,PropertyAssignmentNode):
                    validate_call_argument_values(statement.value,bound)
                    require_bare_value(statement.value,bound)
                    continue

                if isinstance(statement,OutputNode):
                    validate_call_argument_values(statement.expression,bound)
                    require_bare_value(statement.expression,bound)
                    validate_output_placeholders(statement.expression,bound)
                    continue

                if isinstance(statement,ReturnNode):
                    validate_call_argument_values(statement.expression,bound)
                    require_bare_value(statement.expression,bound)
                    continue

                if isinstance(statement,IfNode):
                    validate_call_argument_values(statement.condition,bound)
                    incoming=set(bound)
                    branch_outputs=[]
                    then_out=validate_block(statement.then_body,incoming)
                    if block_falls_through(statement.then_body):
                        branch_outputs.append(then_out)
                    for clause in statement.else_if:
                        validate_call_argument_values(clause.condition,incoming)
                        clause_out=validate_block(clause.body,incoming)
                        if block_falls_through(clause.body):
                            branch_outputs.append(clause_out)
                    if statement.else_body is not None:
                        else_out=validate_block(statement.else_body,incoming)
                        if block_falls_through(statement.else_body):
                            branch_outputs.append(else_out)
                    else:
                        # The condition chain may select no body at all.
                        branch_outputs.append(set(incoming))
                    if branch_outputs:
                        definitely_assigned=set.intersection(*(set(names) for names in branch_outputs))
                        bound.update(definitely_assigned)
                    continue

                if isinstance(statement,WhileNode):
                    validate_call_argument_values(statement.condition,bound)
                    # Validate reads inside the body, but do not promote names
                    # first introduced there: the loop may execute zero times.
                    validate_block(statement.body,bound)
                    continue

                if isinstance(statement,ForEachNode):
                    validate_call_argument_values(statement.collection,bound)
                    loop_bound=set(bound)
                    loop_bound.add(statement.variable.name)
                    # The loop binder itself belongs to the containing scope
                    # under the existing implementation policy; body-only
                    # assignments remain conditional on at least one iteration.
                    bound.add(statement.variable.name)
                    validate_block(statement.body,loop_bound)
                    continue

                if isinstance(statement,ForRangeNode):
                    validate_call_argument_values(statement.start,bound)
                    validate_call_argument_values(statement.end,bound)
                    validate_call_argument_values(statement.step,bound)
                    loop_bound=set(bound)
                    loop_bound.add(statement.variable.name)
                    bound.add(statement.variable.name)
                    validate_block(statement.body,loop_bound)
                    continue

                if isinstance(statement,CallNode):
                    validate_call_argument_values(statement,bound)
                    continue

                if isinstance(statement,AppendNode):
                    validate_call_argument_values(statement.value,bound)
                    validate_call_argument_values(statement.collection,bound)
                    continue

                if isinstance(statement,InsertNode):
                    validate_call_argument_values(statement.value,bound)
                    validate_call_argument_values(statement.collection,bound)
                    validate_call_argument_values(statement.index,bound)
                    continue

                if isinstance(statement,RemoveValueNode):
                    validate_call_argument_values(statement.value,bound)
                    validate_call_argument_values(statement.collection,bound)
                    continue

                if isinstance(statement,(RemoveFirstNode,RemoveLastNode)):
                    validate_call_argument_values(statement.collection,bound)
                    continue

                if isinstance(statement,RaiseNode):
                    validate_call_argument_values(statement.expression,bound)
                    continue

                if isinstance(statement,TryCatchNode):
                    incoming=set(bound)
                    try_out=validate_block(statement.try_body,incoming)
                    catch_bound=set(incoming)
                    if statement.error is not None:
                        catch_bound.add(statement.error.name)
                    catch_out=validate_block(statement.catch_body,catch_bound)
                    if statement.error is not None:
                        catch_out.discard(statement.error.name)
                    post_paths=[]
                    if block_falls_through(statement.try_body):
                        post_paths.append(set(try_out))
                    if block_falls_through(statement.catch_body):
                        post_paths.append(set(catch_out))
                    # Only bindings established on every path that can actually
                    # reach ENDTRY are definitely assigned afterwards. Named
                    # catch bindings therefore do not leak outward.
                    if post_paths:
                        bound.update(set.intersection(*post_paths))
                    continue

                if isinstance(statement,FunctionNode):
                    bound.add(statement.name)
                    local=set(bound)
                    local.update(p.name for p in statement.parameters)
                    validate_block(statement.body,local)
                    continue

                if isinstance(statement,ClassNode):
                    bound.add(statement.name)
                    class_bound=set(bound)
                    class_bound.update(p.name for p in statement.parameters)
                    for item in statement.body.statements:
                        if isinstance(item,AssignmentNode):
                            validate_call_argument_values(item.value,class_bound)
                            require_bare_value(item.value,class_bound)
                            if isinstance(item.target,IdentifierNode):
                                class_bound.add(item.target.name)
                        elif isinstance(item,ConstructorNode):
                            local=set(class_bound)
                            local.update(p.name for p in item.parameters)
                            validate_block(item.body,local,implicit={'THIS'})
                        elif isinstance(item,MethodNode):
                            local=set(class_bound)
                            local.update(p.name for p in item.parameters)
                            validate_block(item.body,local,implicit={'THIS'})
                        elif isinstance(item,FunctionNode):
                            class_bound.add(item.name)
                            local=set(class_bound)
                            local.update(p.name for p in item.parameters)
                            validate_block(item.body,local,implicit={'THIS'})
                    continue

                if isinstance(statement,(ConstructorNode,MethodNode)):
                    local=set(bound)
                    local.update(p.name for p in statement.parameters)
                    validate_block(statement.body,local,implicit={'THIS'})
                    continue

            return bound

        validate_block(BlockNode(root.line,root.body),set())

    def _resolve_member_intrinsics(self, root:ProgramNode):
        # AJ v1.1 parses all object.method(...) forms uniformly. Dictionary
        # GET is resolved semantically only while the receiver is *currently*
        # evidenced as dictionary-backed in the visible lexical/control-flow
        # state; otherwise GET remains an ordinary user method.  Evidence is
        # therefore flow-sensitive: reassignment can clear it, conditional
        # evidence survives only when every path preserves it, and loop-local
        # evidence cannot become definite after a potentially zero-iteration
        # loop.
        loop_flow_stack: list[dict[str, list[set[str]]]] = []

        def statement_falls_through(statement)->bool:
            if isinstance(statement,(ReturnNode,RaiseNode,BreakNode,ContinueNode)):
                return False
            if isinstance(statement,IfNode):
                if statement.else_body is None:
                    return True
                branches=[statement.then_body]
                branches.extend(clause.body for clause in statement.else_if)
                branches.append(statement.else_body)
                return any(block_falls_through(branch) for branch in branches)
            if isinstance(statement,TryCatchNode):
                return (
                    block_falls_through(statement.try_body)
                    or block_falls_through(statement.catch_body)
                )
            return True

        def block_falls_through(block:BlockNode)->bool:
            for statement in block.statements:
                if not statement_falls_through(statement):
                    return False
            return True

        def resolve_expression(node, dictionaries:set[str], dictionary_properties:set[str]):
            if node is None:
                return
            if isinstance(node,MemberCallNode):
                resolve_expression(node.object,dictionaries,dictionary_properties)
                for argument in node.arguments:
                    resolve_expression(argument,dictionaries,dictionary_properties)
                is_dictionary=False
                if isinstance(node.object,IdentifierNode):
                    is_dictionary=node.object.name in dictionaries
                elif isinstance(node.object,MemberAccessNode):
                    is_dictionary=(
                        isinstance(node.object.object,IdentifierNode)
                        and node.object.object.name.upper()=='THIS'
                        and node.object.member in dictionary_properties
                    )
                if node.member.upper()=='GET' and is_dictionary:
                    if len(node.arguments) not in {1,2}:
                        raise SemanticError(f'DICTIONARY.GET requires one or two arguments at line {node.line}.')
                    node.resolved_intrinsic='DICTIONARY_GET'
                return
            for child in node.children():
                resolve_expression(child,dictionaries,dictionary_properties)

        def parameter_dictionary_state(parameters, enclosing:set[str])->set[str]:
            state=set(enclosing)
            for parameter in parameters:
                # A parameter is a local binder and shadows same-named outer
                # representation evidence.  A declared DICTIONARY parameter
                # then establishes fresh local evidence.
                state.discard(parameter.name)
                if (parameter.declared_type or '').upper()=='DICTIONARY':
                    state.add(parameter.name)
            return state

        def visit_block(block:BlockNode, dictionaries:set[str], dictionary_properties:set[str])->set[str]:
            state=set(dictionaries)
            for statement in block.statements:
                if isinstance(statement,BreakNode):
                    if loop_flow_stack:
                        loop_flow_stack[-1]["break_states"].append(set(state))
                    continue

                if isinstance(statement,ContinueNode):
                    if loop_flow_stack:
                        loop_flow_stack[-1]["continue_states"].append(set(state))
                    continue

                # Resolve the RHS before applying assignment type evidence so
                # x <- x.GET(...) cannot self-declare a dictionary.
                if isinstance(statement,AssignmentNode):
                    resolve_expression(statement.value,state,dictionary_properties)
                    resolve_expression(statement.target,state,dictionary_properties)
                    if isinstance(statement.target,IdentifierNode):
                        if (
                            isinstance(statement.value,EmptyLiteralNode)
                            and statement.value.empty_type=='DICTIONARY'
                        ):
                            state.add(statement.target.name)
                        else:
                            # Any other reassignment removes prior certainty.
                            state.discard(statement.target.name)
                    continue

                if isinstance(statement,PropertyAssignmentNode):
                    resolve_expression(statement.value,state,dictionary_properties)
                    continue

                if isinstance(statement,IfNode):
                    resolve_expression(statement.condition,state,dictionary_properties)
                    incoming=set(state)
                    branch_outputs=[]
                    then_out=visit_block(statement.then_body,incoming,dictionary_properties)
                    if block_falls_through(statement.then_body):
                        branch_outputs.append(then_out)
                    for clause in statement.else_if:
                        resolve_expression(clause.condition,incoming,dictionary_properties)
                        clause_out=visit_block(clause.body,incoming,dictionary_properties)
                        if block_falls_through(clause.body):
                            branch_outputs.append(clause_out)
                    if statement.else_body is not None:
                        else_out=visit_block(statement.else_body,incoming,dictionary_properties)
                        if block_falls_through(statement.else_body):
                            branch_outputs.append(else_out)
                    else:
                        branch_outputs.append(set(incoming))
                    state=(
                        set.intersection(*(set(names) for names in branch_outputs))
                        if branch_outputs else set(incoming)
                    )
                    continue

                if isinstance(statement,WhileNode):
                    resolve_expression(statement.condition,state,dictionary_properties)
                    incoming=set(state)
                    loop_flow={"break_states": [], "continue_states": []}
                    loop_flow_stack.append(loop_flow)
                    body_out=visit_block(statement.body,incoming,dictionary_properties)
                    loop_flow_stack.pop()
                    post_states=[incoming]
                    post_states.extend(loop_flow["break_states"])
                    post_states.extend(loop_flow["continue_states"])
                    if block_falls_through(statement.body):
                        post_states.append(body_out)
                    state=set.intersection(*(set(names) for names in post_states))
                    continue

                if isinstance(statement,ForEachNode):
                    resolve_expression(statement.collection,state,dictionary_properties)
                    incoming=set(state)
                    body_state=set(incoming)
                    body_state.discard(statement.variable.name)
                    loop_flow={"break_states": [], "continue_states": []}
                    loop_flow_stack.append(loop_flow)
                    body_out=visit_block(statement.body,body_state,dictionary_properties)
                    loop_flow_stack.pop()
                    post_states=[incoming]
                    post_states.extend(loop_flow["break_states"])
                    post_states.extend(loop_flow["continue_states"])
                    if block_falls_through(statement.body):
                        post_states.append(body_out)
                    state=set.intersection(*(set(names) for names in post_states))
                    continue

                if isinstance(statement,ForRangeNode):
                    resolve_expression(statement.start,state,dictionary_properties)
                    resolve_expression(statement.end,state,dictionary_properties)
                    resolve_expression(statement.step,state,dictionary_properties)
                    incoming=set(state)
                    body_state=set(incoming)
                    body_state.discard(statement.variable.name)
                    loop_flow={"break_states": [], "continue_states": []}
                    loop_flow_stack.append(loop_flow)
                    body_out=visit_block(statement.body,body_state,dictionary_properties)
                    loop_flow_stack.pop()
                    post_states=[incoming]
                    post_states.extend(loop_flow["break_states"])
                    post_states.extend(loop_flow["continue_states"])
                    if block_falls_through(statement.body):
                        post_states.append(body_out)
                    state=set.intersection(*(set(names) for names in post_states))
                    continue

                if isinstance(statement,TryCatchNode):
                    incoming=set(state)
                    try_out=visit_block(statement.try_body,incoming,dictionary_properties)
                    catch_state=set(incoming)
                    if statement.error is not None:
                        catch_state.discard(statement.error.name)
                    catch_out=visit_block(statement.catch_body,catch_state,dictionary_properties)
                    if statement.error is not None:
                        catch_out.discard(statement.error.name)
                    post_states=[]
                    if block_falls_through(statement.try_body):
                        post_states.append(set(try_out))
                    if block_falls_through(statement.catch_body):
                        post_states.append(set(catch_out))
                    state=(set.intersection(*post_states) if post_states else set(incoming))
                    continue

                if isinstance(statement,FunctionNode):
                    fn_dicts=parameter_dictionary_state(statement.parameters,state)
                    visit_block(statement.body,fn_dicts,set())
                    # The local function declaration itself binds its name and
                    # therefore shadows any previous same-named dictionary.
                    state.discard(statement.name)
                    continue

                if isinstance(statement,ClassNode):
                    class_dict_props={
                        item.name for item in statement.body.statements
                        if isinstance(item,PropertyDeclarationNode) and (item.declared_type or '').upper()=='DICTIONARY'
                    }
                    for item in statement.body.statements:
                        if isinstance(item,ConstructorNode):
                            local=parameter_dictionary_state(item.parameters,state)
                            visit_block(item.body,local,class_dict_props)
                        elif isinstance(item,MethodNode):
                            local=parameter_dictionary_state(item.parameters,state)
                            visit_block(item.body,local,class_dict_props)
                        elif isinstance(item,FunctionNode):
                            local=parameter_dictionary_state(item.parameters,state)
                            visit_block(item.body,local,class_dict_props)
                        elif isinstance(item,AssignmentNode):
                            resolve_expression(item.value,state,class_dict_props)
                    state.discard(statement.name)
                    continue

                resolve_expression(statement,state,dictionary_properties)

            return state

        visit_block(BlockNode(root.line,root.body),set(),set())

    def walk(self,n):
        yield n
        for c in n.children(): yield from self.walk(c)

@dataclass
class AdjacencyList:
    root_id:str; nodes:dict[str,dict]=field(default_factory=dict); adjacency:dict[str,list[str]]=field(default_factory=dict)
    @classmethod
    def from_ast(cls,root):
        g=cls(root.node_id); g._walk(root); g.validate(); return g
    def _walk(self,n):
        self.nodes[n.node_id]={'kind':n.kind,'line':n.line,'attributes':n.attrs()}; cs=list(n.children()); self.adjacency[n.node_id]=[c.node_id for c in cs]
        for c in cs: self._walk(c)
    def validate(self):
        if self.root_id not in self.nodes: raise ValueError('Missing root node.')
        for a,bs in self.adjacency.items():
            if a not in self.nodes: raise ValueError(f'Missing source node {a}.')
            for b in bs:
                if b not in self.nodes: raise ValueError(f'Missing target node {b}.')
    def to_dict(self): return {'root_id':self.root_id,'nodes':self.nodes,'adjacency':self.adjacency}
    def to_json(self): return json.dumps(self.to_dict(),indent=2,default=str)
    def pretty(self): return '\n'.join(f"{n} ({self.nodes[n]['kind']}) -> {self.adjacency[n] or '[]'}" for n in self.adjacency)

@dataclass
class ParseResult:
    success:bool; ast:ProgramNode|None; adjacency_list:AdjacencyList|None; tokens:list[Token]; report:ProcessReport; error:str|None=None

class AJParserFacade:
    def __init__(self,lexer=None,validator=None): self.lexer=lexer or AJLexer(); self.validator=validator or SemanticValidator()
    def parse(self,source:str)->ParseResult:
        report=ProcessReport(); tokens=[]; ast=None; graph=None
        def stage(name,fn,success_message,**meta):
            start=time.perf_counter()
            try:
                value=fn(); details={k:f(value) for k,f in meta.items()}; report.add(name,StageStatus.SUCCESS,success_message,(time.perf_counter()-start)*1000,**details); return value,None
            except Exception as e:
                report.add(name,StageStatus.FAILURE,str(e),(time.perf_counter()-start)*1000); return None,e
        _,err=stage('INPUT_VALIDATION',lambda:self._validate(source),'Input accepted.',characters=lambda _:len(source))
        if err:return ParseResult(False,None,None,[],report,str(err))
        tokens,err=stage('LEXICAL_ANALYSIS',lambda:self.lexer.tokenise(source),'Source tokenised.',token_count=lambda x:len(x))
        if err:return ParseResult(False,None,None,[],report,str(err))
        ast,err=stage('SYNTAX_ANALYSIS',lambda:AJParser(tokens).parse(),'AST constructed.',top_level_nodes=lambda x:len(x.body))
        if err:return ParseResult(False,None,None,tokens,report,str(err))
        _,err=stage('STATIC_SEMANTIC_ANALYSIS',lambda:self.validator.validate(ast),'Static semantic analysis completed.',warning_count=lambda x:len(x))
        if err:return ParseResult(False,ast,None,tokens,report,str(err))
        graph,err=stage('ADJACENCY_LIST_GENERATION',lambda:AdjacencyList.from_ast(ast),'Adjacency list generated.',node_count=lambda x:len(x.nodes),edge_count=lambda x:sum(map(len,x.adjacency.values())))
        if err:return ParseResult(False,ast,None,tokens,report,str(err))
        report.add('PIPELINE_RESULT',StageStatus.SUCCESS,'All stages completed successfully.')
        return ParseResult(True,ast,graph,tokens,report)
    @staticmethod
    def _validate(source):
        if not isinstance(source,str): raise TypeError('Pseudocode must be text.')
        if not source.strip(): raise ValueError('Pseudocode cannot be empty.')
        return True
