# Monografia do TCC

O texto fica em `tese.tex`; as referências, em `bibliografia.bib`.
A pasta é parte do repositório TCC, sem Git próprio e fora do build do site.
O arquivo principal está configurado como TCC e começa pelo capítulo do harness.
Resumo, abstract, palavras-chave, data de defesa e licença do texto ainda precisam
ser definidos. A bibliografia começa vazia.

## Compilação

Com TeX Live, `latexmk` e `biber` instalados, execute nesta pasta:

```sh
make
# ou: latexmk tese.tex
```

O resultado é `tese.pdf`. `make clean` remove os auxiliares; `make distclean`
remove também o PDF. Esses arquivos gerados ficam fora do versionamento.
Os estilos do modelo requerem pacotes adicionais do TeX Live; a relação completa
está no [README original](https://gitlab.com/ccsl-usp/modelo-latex/-/blob/cb57593d28d3d441c847fec4a7c4870128d3ea3b/README.md).

## Pseudocódigo

O suporte já é carregado por `imelooks.sty`, com `listings` e `lstpseudocode.sty`.
Exemplo mínimo de sintaxe em português, para inserir no corpo de `tese.tex`:

```latex
\begin{program}
  \begin{lstlisting}[language={[brazilian]pseudocode}, style=pseudocode]
    funcao identidade(valor)
        devolva valor
    fim
  \end{lstlisting}
  \caption{Função identidade.}
  \label{prog:identidade}
\end{program}
```

Use `\ref{prog:identidade}` para a referência. Para algoritmos com mais de uma
página, use `programruledcaption` no lugar do float `program`:

```latex
\begin{programruledcaption}{Título do algoritmo.\label{prog:algoritmo}}
  \begin{lstlisting}[language={[brazilian]pseudocode}, style=pseudocode]
    funcao identidade(valor)
        devolva valor
    fim
  \end{lstlisting}
\end{programruledcaption}
```

## Origem e licenças

Adaptado de [ccsl-usp/modelo-latex](https://gitlab.com/ccsl-usp/modelo-latex),
commit `cb57593d28d3d441c847fec4a7c4870128d3ea3b`.
Criação: Jesús P. Mena-Chalco; revisão: Fabio Kon e Paulo Feofiloff;
adaptação para UTF-8, biblatex e outras melhorias: Nelson Lago.

O código do modelo tem licença MIT, preservada em `LICENSE`. Textos explicativos,
tutoriais e comentários originais têm licença CC BY 4.0; arquivos derivados de
outros projetos preservam seus próprios avisos. Essas licenças do modelo não
escolhem a licença do texto autoral da monografia.

Foram retirados os modelos de artigo, apresentação e pôster, os capítulos de
exemplo, imagens demonstrativas, PDFs prontos e estilos bibliográficos não usados
pela tese. Os estilos necessários e a configuração de compilação foram mantidos.
