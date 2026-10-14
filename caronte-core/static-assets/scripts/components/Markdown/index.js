import DOMPurify from "dompurify"
import { marked } from "marked"

import styles from "./style.module.css"

const COMPONENT_TAG = 'markdown-text'

export const element = customElements.define(COMPONENT_TAG,
    class extends HTMLElement {
        constructor(...props) {
            super(props)

            this.attachShadow({ mode: "open" })
            styles.use({ id: "markdown-styles" })
            
            const render = document.createElement("div")
            const stylesTag = document.querySelectorAll('[data-id="markdown-styles"]')
            const cssValue = []
            stylesTag.forEach(tag => {
                const css = new CSSStyleSheet()
                css.replace(tag.innerHTML)
                cssValue.push(css)
            })
            this.shadowRoot.adoptedStyleSheets = cssValue
            if (Object.keys(this.dataset).includes("preview")) {
                render.classList.add("preview")
            }
            render.setAttribute("id", "render")
            this.shadowRoot.appendChild(render)
            this.set = this.set.bind(this)
        }

        connectedCallback() {
            if (!this.rendered) {
                this.render()
                this.rendered = true
            }
        }

        disconnectedCallback() { 
            styles.unuse()
        }

        set(text) {
            const renderer = new marked.Renderer()

            renderer.image = function(href, title, text) {
                return ""
            }

            renderer.link = function(href, title, text) {
                // https://developer.chrome.com/docs/lighthouse/best-practices/external-anchors-use-rel-noopener
                var link = marked.Renderer.prototype.link.call(this, href, title, text)
                return link.replace("<a",`<a class="land__link" rel="noopener noreferrer" target="_blank" `)
            }

            marked.use({ renderer })

            const cleanedText = text.replace(/[\u200B\u200C\u200D\u200E\u200F\uFEFF]+/g, "")

            const plainText = cleanedText.replace(/\\n/g, "\n\n");

            const markdownHtml = marked.parse(plainText, {
                gfm: false,
                pedantic: false,
                breaks: true
            })

            DOMPurify.addHook('beforeSanitizeAttributes', function(node) {
                if (node.tagName === 'A') {
                    node.setAttribute('target', '_blank')
                    node.setAttribute('rel', 'noopener noreferrer')
                }
            })

            const sanitizedHtml = DOMPurify.sanitize(markdownHtml, {
                ALLOWED_TAGS: [
                    "b", "i", "em", "strong", "a", "ul", "ol", "li", "br", "p",
                    "code", "pre", "blockquote", "h1", "h2", "h3", "h4", "h5", "h6"
                ],
                ALLOWED_ATTR: ["class", "href", "target", "rel"]
            })

            this.shadowRoot.querySelector('#render').innerHTML = sanitizedHtml
        }

        render() {
            if (this.textContent) {
                this.set(this.textContent)
                this.textContent = ""
            }
        }
    })