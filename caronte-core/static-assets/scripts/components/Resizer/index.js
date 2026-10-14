import { EditorView, basicSetup } from "codemirror"
import { EditorState } from "@codemirror/state"
import { lintGutter } from "@codemirror/lint";

import styles from './style.module.css'
import { addons } from "./addons.js"
import { loadSchema, jsonSchemaLinter } from "../../common/schema.js"
import { myTheme } from "./theme.js";

const COMPONENT_TAG = 'resizer-text'

export const element = customElements.define(COMPONENT_TAG,
    class extends HTMLElement {
        constructor(...props) {
            super(props)

            styles.use()

            this.prevSiblingHeight = 0
			this.prevSiblingWidth = 0

            this.state = {
                collapse: false,
                fullscreen: false,
                language: this.getAttribute('data-language') ? this.getAttribute('data-language') : "markdown",
                schema: this.getAttribute('data-schema-url') ? this.getAttribute('data-schema-url') : null,
                textarea: this.getElementsByTagName("textarea")[0]
            }

            if (!Object.hasOwn(addons, this.state.language)) {
                this.state.language = "default"
            }

            if (this.getAttribute('data-direction') === "auto" && window.matchMedia("(max-width:650px)").matches) {
                this.setAttribute('data-direction', 'vertical')
            } else {
                this.setAttribute('data-direction', 'horizontal')
            }

            this.onMouseDownHandler = this.onMouseDownHandler.bind(this)
            this.onMouseMoveHandler = this.onMouseMoveHandler.bind(this)
            this.onMouseUpHandler = this.onMouseUpHandler.bind(this)
            this.onCollapseHandler = this.onCollapseHandler.bind(this)
            this.onFullScreenHandler = this.onFullScreenHandler.bind(this)
            this.updatePreview = this.updatePreview.bind(this)
        }

        async connectedCallback() {
            if (!this.rendered) {
                this.render()
                this.rendered = true

                this.direction = this.getAttribute('data-direction') || 'horizontal'
                this._prevSibling = this.querySelector('.resizer').previousElementSibling
                this._nextSibling = this.querySelector('.resizer').nextElementSibling

                const extensions = [
                    basicSetup,
                    myTheme,
                    addons[this.state.language].langCodemirror(),
                    EditorView.lineWrapping
                ]
                if (this.state.language == "json" && this.state.schema) {
                    const { schema, validate } = await loadSchema(this.state.schema)
                    if (schema) {
                        extensions.push(lintGutter())
                        extensions.push(jsonSchemaLinter(validate))
                    }
                }
                extensions.push(
                    EditorView.updateListener.of((update) => {
                        if (update.docChanged) {
                            this.updatePreview()
                        }
                    })) 

                this.view = new EditorView({
                    state: EditorState.create({
                        doc: this.state.textarea.textContent.replace(/\\n/g, "\n").trim(),
                        extensions: extensions
                    }),
                    parent: this.querySelector(".code")
                })

                this.events = addons[this.state.language].events.bind(this)
                this.events(this, this.view)

                this.querySelector('.resizer').addEventListener('mousedown', this.onMouseDownHandler)
                this._prevSibling.addEventListener('input', this.onInputHandler)
                if (this.querySelector('#collapse')) {
                    this.querySelector('#collapse').addEventListener('click', this.onCollapseHandler)
                }
                if (this.querySelector('#fullscreen')) {
                    this.querySelector('#fullscreen').addEventListener('click', this.onFullScreenHandler)
                }
                if (!this.state.collapse) this.onCollapseHandler()                
            }
        }

        disconnectedCallback() {
            styles.unuse()
        }

        updatePreview() {
            const value = this.view.state.doc.toString()
            if (this.state.language === "json") {
                this.state.textarea.innerHTML = value
            } else {
                this.state.textarea.innerHTML = value.replace(/\n/g, "\\n").trim()
            }
            
            if (!this.state.collapse) {
                this.querySelector("markdown-text").set(value)
            }
        }

        onMouseUpHandler() {
            this.style.removeProperty('cursor')
            document.body.style.removeProperty('cursor')

            this._prevSibling.style.removeProperty('user-select')
            this._prevSibling.style.removeProperty('pointer-events')

            this._nextSibling.style.removeProperty('user-select')
            this._nextSibling.style.removeProperty('pointer-events')

            document.removeEventListener('mousemove', this.onMouseMoveHandler)
            document.removeEventListener('mouseup', this.onMouseUpHandler)
        }

        onMouseDownHandler(event) {
            this.x = event.clientX
            this.y = event.clientY
            const rect = this._prevSibling.getBoundingClientRect()
            this.prevSiblingHeight = rect.height
            this.prevSiblingWidth = rect.width

            document.addEventListener('mousemove', this.onMouseMoveHandler)
            document.addEventListener('mouseup', this.onMouseUpHandler)
        }

        onMouseMoveHandler(event) {
            const dx = event.clientX - this.x
            const dy = event.clientY - this.y

            switch (this.direction) {
                case 'vertical':
                    const h = ((this.prevSiblingHeight + dy) * 100) / this.parentNode.getBoundingClientRect().height
                    this._prevSibling.style.height = h + '%'
                    break
                case 'horizontal':
                default:
                    const w = ((this.prevSiblingWidth + dx) * 100) / this.parentNode.getBoundingClientRect().width
                    this._prevSibling.style.width = w + '%'
                    break
            }

            // prevent flicking
            const cursor = this.direction === 'horizontal' ? 'col-resize' : 'row-resize'
            this.style.cursor = cursor
            document.body.style.cursor = cursor

            this._prevSibling.style.userSelect = 'none'
            this._prevSibling.style.pointerEvents = 'none'

            this._nextSibling.style.userSelect = 'none'
            this._nextSibling.style.pointerEvents = 'none'
        }

        onCollapseHandler() {
            if (this.state.collapse) {
                this._prevSibling.style.removeProperty('width')
                this._prevSibling.style.removeProperty('height')

                this._nextSibling.style.removeProperty('display')
                this.querySelector('.resizer').style.removeProperty('display')

                this.state.collapse = false

                if (this.querySelector('#collapse')) {
                    this.querySelector('#collapse').innerHTML = '<svg width="16" height="16"><use xlink:href="#icon-right-close"></use></svg>'
                }

                this.updatePreview()
            } else {
                this._prevSibling.style.width = '100%'
                this._prevSibling.style.height = '100%'
                this._nextSibling.style.display = 'none'
                this.querySelector('.resizer').style.display = 'none'

                this.state.collapse = true

                if (this.querySelector('#collapse')) {
                    this.querySelector('#collapse').innerHTML = '<svg width="16" height="16"><use xlink:href="#icon-left-close"></use></svg>'
                }
            }   
        }

        onFullScreenHandler(event) {
            if (this.state.fullscreen) {
                this.classList.remove("fullscreen")
                document.body.style.removeProperty('overflow')
                
                this.state.fullscreen = false

                this.querySelector('#fullscreen').innerHTML = '<svg width="16" height="16"><use xlink:href="#icon-fullscreen"></use></svg>'
            } else {
                this.classList.add("fullscreen")
                document.body.style.overflow = "hidden"

                this.state.fullscreen = true

                this.querySelector('#fullscreen').innerHTML = '<svg width="16" height="16"><use xlink:href="#icon-minimize"></use></svg>'
            }   
        }

        render() {
            this.appendDOM(addons[this.state.language].toolbox(), 'afterbegin')
            this.appendDOM(addons[this.state.language].downbox())

            this.querySelector(".wrapper").appendDOM(`<div class="resizer"></div>`)

            this.querySelector(".wrapper").appendDOM(`<markdown-text class="container__item" data-preview></markdown-text>`)
        }
    })