import { markdown } from "@codemirror/lang-markdown"
import { json } from "@codemirror/lang-json"

const bypassText = (view, bypass) => {
    const { from, to } = view.state.selection.main
    if (from === to) return

    const selectedText = view.state.doc.sliceString(from, to)
    const changes = [
        { from, to, insert: `${bypass}${selectedText}${bypass}` }
    ]

    view.dispatch({
        changes,
        selection: { anchor: from + bypass.length + selectedText.length }
    })
}

const bypassTextInStart = (view, bypass) => {
    const { from } = view.state.selection.main

    const line = view.state.doc.lineAt(from)
    const lineStart = line.from
    const lineText = line.text

    const re = /^\#+\s*/
    const match = re.exec(lineText)

    let insertPos, insertText;
    if (!match) {
        insertPos = lineStart;
        insertText = `${bypass} `
    } else {
        insertPos = lineStart;
        insertText = "";
    }

    view.dispatch({
        changes: { from: insertPos, to: insertPos + (match ? match[0].length : 0), insert: insertText },
        selection: { anchor: from + (insertText.length - (match ? match[0].length : 0)) }
    })
}

export const addons = {
    "markdown": {
        "toolbox": () => {
            return /*html*/`
            <div class="toolbox">
                <div>
                    <div id="title" class="lessicon" title="Título">
                    <svg width="16" height="16">
                        <use xlink:href="#icon-title"></use>
                    </svg>
                    </div>
                    <div id="bold" class="lessicon" title="Texto em Negrito">
                    <svg width="16" height="16">
                        <use xlink:href="#icon-bold"></use>
                    </svg>
                    </div>
                    <div id="italic" class="lessicon" title="Texto em Itálico">
                    <svg width="16" height="16">
                        <use xlink:href="#icon-italic"></use>
                    </svg>
                    </div>
                    <span class="toolbox__bar"></span>
                    <div id="indent" class="lessicon" title="Indentar">
                    <svg width="16" height="16">
                        <use xlink:href="#icon-indent"></use>
                    </svg>
                    </div>
                </div>
                <div>
                    <div id="collapse" class="lessicon" title="Colapsar">
                    <svg width="16" height="16">
                        <use xlink:href="#icon-right-close"></use>
                    </svg>
                    </div>
                    <div id="fullscreen" class="lessicon" title="Tela cheia">
                    <svg width="16" height="16">
                        <use xlink:href="#icon-fullscreen"></use>
                    </svg>
                    </div>
                </div>
            </div>
            `
        },
        "downbox": () => {
            return  /*html*/`<div class="downbox">
                <div></div>
                <div>
                    <a href="https://www.markdownguide.org/" target="_blank" class="lessicon" title="Markdown">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 208 128">
                        <rect width="198" height="118" x="5" y="5" ry="10" stroke="var(--high-emphasis-color)" stroke-width="10" fill="none"/>
                        <path fill="var(--high-emphasis-color)" d="M30 98V30h20l20 25 20-25h20v68H90V59L70 84 50 59v39zm125 0l-30-33h20V30h20v35h20z"/>
                        </svg>
                    </a>
                </div>    
            </div>
            `
        },
        "events": (self, view) => {
            const _onBoldHandler = (event) => {
                bypassText(view, "**")
            }

            const _onItalicHandler = (event) => {
                bypassText(view, "*")
            }

            const _onTitleHandler = (event) => {
                bypassTextInStart(view, "#")
            }

            const _onIndentHandler = (event) => {
                bypassTextInStart(view, ">")
            }

            self.onBoldHandler = _onBoldHandler.bind(self)
            self.onItalicHandler = _onItalicHandler.bind(self)
            self.onTitleHandler = _onTitleHandler.bind(self)
            self.onIndentHandler = _onIndentHandler.bind(self)
            
            self.querySelector('#bold').addEventListener('click', self.onBoldHandler)
            self.querySelector('#italic').addEventListener('click', self.onItalicHandler)
            self.querySelector('#title').addEventListener('click', self.onTitleHandler)
            self.querySelector('#indent').addEventListener('click', self.onIndentHandler)
        },
        langCodemirror: markdown
    },
    "json": {
        "toolbox": () => {
            return /*html*/`
            <div class="toolbox">
                <div>
                </div>
                <div>
                    <div id="fullscreen" class="lessicon" title="Tela cheia">
                    <svg width="16" height="16">
                        <use xlink:href="#icon-fullscreen"></use>
                    </svg>
                    </div>
                </div>
            </div>
            `
        },
        "downbox": () => {
            return  /*html*/`<div class="downbox">  
                <div style="min-height: 16px"></div>
            </div>
            `
        },
        "events": (self) => {
            self.onCollapseHandler()
        },
        langCodemirror: json
    },
    "default": {
        "toolbox": () => {
            return /*html*/`
            <div class="toolbox">
                <div>
                </div>
                <div>
                    <div id="fullscreen" class="lessicon" title="Tela cheia">
                    <svg width="16" height="16">
                        <use xlink:href="#icon-fullscreen"></use>
                    </svg>
                    </div>
                </div>
            </div>
            `
        },
        "downbox": () => {
            return  /*html*/`<div class="downbox">  
                <div style="min-height: 16px"></div>
            </div>
            `
        },
        "events": (self) => {
            self.onCollapseHandler()
        },
        langCodemirror: () => {}
    }
}