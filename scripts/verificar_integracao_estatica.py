from pathlib import Path
from collections import defaultdict
import ast,re,sys
# Usa a pasta do próprio projeto e nunca consulta o banco.
base=Path(__file__).resolve().parent.parent
errors=[]
# Todos os arquivos Python devem compilar e não possuir marcas de conflito.
for f in base.rglob('*.py'):
 if 'management' in f.parts:continue
 s=f.read_text(encoding='utf-8-sig')
 try: ast.parse(s,filename=str(f))
 except SyntaxError as e: errors.append(f'Syntax: {f.relative_to(base)}:{e}')
 if re.search(r'^(<<<<<<< |=======\s*$|>>>>>>> )',s,re.M):errors.append(f'Conflito: {f}')
# Uma só folha final por aplicação.
for app in ['usuarios','academico','atividades','avaliacoes','frequencia','comunicacao']:
 folder=base/'apps'/app/'migrations';names={f.stem for f in folder.glob('[0-9]*.py')};dependencies=set()
 for f in folder.glob('[0-9]*.py'):
  tree=ast.parse(f.read_text(encoding='utf-8-sig'))
  for node in ast.walk(tree):
   if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='dependencies' for t in node.targets):
    try: deps=ast.literal_eval(node.value)
    except Exception: continue
    for d in deps:
     if isinstance(d,tuple) and len(d)==2 and d[0]==app:dependencies.add(d[1])
 leaves=sorted(names-dependencies)
 print('Migration leaf',app,leaves)
 if len(leaves)!=1:errors.append(f'Múltiplas folhas {app}: {leaves}')
# URLs presentes nos templates.
urls=(base/'core/urls.py').read_text()
names=set(re.findall(r"name=['\"]([^'\"]+)['\"]", urls))
for f in (base/'Templates').rglob('*.html'):
 for name in re.findall(r"{%\s*url\s+['\"]([^'\"]+)['\"]",f.read_text(encoding='utf-8-sig')):
  if name not in names and name not in ('admin:index',):errors.append(f'Rota ausente: {f.relative_to(base)} {name}')
print('Rota-count:',len(names),'Erro-count:',len(errors))
for e in errors:print('ERROR',e)
sys.exit(bool(errors))
