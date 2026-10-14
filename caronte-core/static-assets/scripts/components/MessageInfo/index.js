import styles from './style.module.css'

import { createElementFromHTML } from '../../common/index.js'

const MINIMUM_TIME_WAIT = 10000

const COMPONENT_TAG = 'message-info'

export const element = customElements.define(COMPONENT_TAG,
    class extends HTMLElement {
        constructor(...props) {
            super(props)

            styles.use()

            this.onClickCloseHandler = this.onClickCloseHandler.bind(this)
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

        onClickCloseHandler(event) {
            const message = event.target.parentElement.parentElement
            message.classList.add('message-info__remove')
            setTimeout(() => {
                message.remove()
            }, 300)
        }

        addMessageInfo({ description, type }) {
            const message = createElementFromHTML(this.#createdMessage({ description, type }))
            this.append(message)
            message.querySelector('.close-button').addEventListener('click', this.onClickCloseHandler)
            setTimeout(() => {
                message.classList.add('message-info__remove')
                setTimeout(() => {
                    message.remove()
                }, 800)
            }, MINIMUM_TIME_WAIT)
        }

        #createdMessage({ description, type }) {
            let classType = "message-info--info"
            if (type === "warning") {
                classType = "message-info--warn"
            } else if (type === "error") {
                classType = "message-info--error"
            }
            return(/*html*/`
                <div class="message-info ${ classType }">
                    <div class="description-info" title="${ description }">
                        ${ description }
                    </div>
                    <div class="close-button">
                        <svg width="16" height="16"><use xlink:href="#icon-close"></use></svg>
                    </div>
                </div>
            `)
        }

        render() { }
    })