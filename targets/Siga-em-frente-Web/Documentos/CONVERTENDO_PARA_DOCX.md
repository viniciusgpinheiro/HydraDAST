# Convertendo Documentos para DOCX

Os documentos foram criados em formato Markdown (`.md`), que é versátil e facilita versionamento. Aqui estão as opções para convertê-los para DOCX (Microsoft Word).

## Opção 1: Usar Pandoc (Recomendado)

Pandoc é a ferramenta mais poderosa para conversão de documentos.

### Instalação

**Windows:**
- Baixar: https://github.com/jgm/pandoc/releases
- Escolher `pandoc-X.X-windows-x86_64.msi`

**Mac:**
```bash
brew install pandoc
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install pandoc
```

**Linux (Fedora/CentOS):**
```bash
sudo yum install pandoc
```

### Uso Básico

```bash
# Converter um arquivo
pandoc PLANO_DE_TESTE.md -o PLANO_DE_TESTE.docx

# Converter com formatação
pandoc PLANO_DE_TESTE.md \
  -o PLANO_DE_TESTE.docx \
  --from markdown \
  --to docx \
  -V geometry:margin=1in

# Converter todos os arquivos importantes
pandoc PLANO_DE_TESTE.md -o PLANO_DE_TESTE.docx
pandoc RELATORIO_VULNERABILIDADES.md -o RELATORIO_VULNERABILIDADES.docx
pandoc LISTA_COMPLETA_4_VULNERABILIDADES.md -o LISTA_COMPLETA_4_VULNERABILIDADES.docx
```

### Template Personalizado (Avançado)

Se desejar usar um template customizado com logo da AulasHack:

```bash
pandoc PLANO_DE_TESTE.md \
  -o PLANO_DE_TESTE.docx \
  --reference-doc=custom-template.docx
```

## Opção 2: Google Docs

Método manual mas sem instalações:

1. Copiar conteúdo do arquivo `.md`
2. Abrir Google Docs: https://docs.google.com
3. Criar novo documento
4. Colar conteúdo
5. Formatar manualmente
6. Fazer download como `.docx`

**Vantagens:**
- Sem instalação
- Colaboração em tempo real
- Acesso de qualquer lugar

**Desvantagens:**
- Formatação manual
- Mais demorado para documentos grandes

## Opção 3: Microsoft Word Online

Similar ao Google Docs:

1. Fazer upload do arquivo `.md` para OneDrive
2. Abrir em Word Online
3. Converter/formatar conforme necessário
4. Fazer download

## Opção 4: Usar Python

Se tiver Python instalado:

```bash
# Instalar libraria
pip install python-docx

# Script Python para conversão (basic)
python -c "
import markdown
from docx import Document

# Ler arquivo markdown
with open('PLANO_DE_TESTE.md', 'r', encoding='utf-8') as f:
    md_text = f.read()

# Converter para HTML primeiro
html = markdown.markdown(md_text)

# Depois para DOCX (simplificado)
doc = Document()
doc.add_paragraph(md_text)
doc.save('PLANO_DE_TESTE.docx')
"
```

## Opção 5: LibreOffice (Gratuito)

**Instalação:**
```bash
# Ubuntu/Debian
sudo apt-get install libreoffice

# Fedora/CentOS
sudo yum install libreoffice

# macOS
brew install libreoffice
```

**Conversão via Command Line:**
```bash
libreoffice --headless --convert-to docx PLANO_DE_TESTE.md
```

## Recomendação Final

Para melhor resultado com melhor velocidade:

```bash
# 1. Instalar Pandoc (uma vez)
# Seguir instruções acima para seu SO

# 2. Executar conversão
pandoc PLANO_DE_TESTE.md -o PLANO_DE_TESTE.docx

# 3. Abrir em Word para ajustes finos
# Adicionar logo, ajustar margens, etc
```

## Arquivos para Converter

Estes arquivos Markdown devem ser convertidos para DOCX:

```bash
pandoc PLANO_DE_TESTE.md -o PLANO_DE_TESTE.docx
pandoc RELATORIO_VULNERABILIDADES.md -o RELATORIO_VULNERABILIDADES.docx
pandoc LISTA_COMPLETA_4_VULNERABILIDADES.md -o LISTA_COMPLETA_4_VULNERABILIDADES.docx
```

## Adicionando Logo AulasHack

Após conversão para DOCX:

1. Abrir arquivo `.docx` no Word
2. Ir para "Insert" → "Pictures"
3. Adicionar logo da AulasHack
4. Formatar conforme desejado
5. Salvar

## Ajustes de Formatação

No Word, após conversão, você pode:

- Adicionar numeração de página
- Alterar espaçamento entre linhas
- Adicionar índice automático
- Adicionar rodapés com "Powered by AulasHack"
- Formatar cabeçalhos
- Adicionar marca d'água

## Salvar com Proteção

Para proteger o documento:

1. Ir para "File" → "Protect Document" → "Encrypt with Password"
2. Digitar senha
3. Repetir senha
4. Salvar

## Checklist de Conversão

- [ ] Pandoc instalado
- [ ] Arquivo PLANO_DE_TESTE.md existe
- [ ] Arquivo RELATORIO_VULNERABILIDADES.md existe
- [ ] Executar conversão
- [ ] Abrir DOCX em Word
- [ ] Adicionar logo AulasHack
- [ ] Adicionar rodapé com "Powered by AulasHack"
- [ ] Ajustar formatação conforme necessário
- [ ] Salvar arquivo final
- [ ] Testar abertura em outros computadores

---

**Desenvolvido por AulasHack**
