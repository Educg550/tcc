import styles from './style.module.css'

const COMPONENT_TAG = 'popup-element'

export const element = customElements.define(COMPONENT_TAG,
    class extends HTMLElement {
        constructor(...props) {
            super(props)

            styles.use()

            this.onExitHandler = this.onExitHandler.bind(this)
        }

        async connectedCallback() {
            if (!this.rendered) {
                await this.render()
                this.rendered = true
                this.addAllListeners()
            }
        }

        disconnectedCallback() { 
            styles.unuse()
            this.removeAllListeners()
        }

        addAllListeners() {
            this.querySelector("#obfuscation-popup").addEventListener('click', this.onExitHandler)
            this.querySelector("#close-popup").addEventListener('click', this.onExitHandler)
        }

        removeAllListeners() {
            this.querySelector("#obfuscation-popup").removeEventListener('click', this.onExitHandler)
            this.querySelector("#close-popup").removeEventListener('click', this.onExitHandler)
        }

        onExitHandler() {
            document.body.style.removeProperty('overflow')
            this.remove()
            // setTimeout(() => {
            //     this.remove()
            // }, 300)
        }

        async render() {
            this.state = {
                url_request: this.dataset.url_request || '',
                title: this.dataset.title || ''
            }
            document.body.style.overflow = "hidden"
            try {
                let response = await fetch(this.state.url_request)
                if (!response.ok) {
                    throw new Error("Ocorreu uma falha ao carregar a página")
                }
                this.appendDOM(/*html*/`
                    <div id="obfuscation-popup" class="obfuscation"></div>

                    <div class="card">
                        <div class="menu">
                            <div><h3>${this.state.title}</h3></div>
                            <div></div>
                            <div class="menu__icons">
                                <div id="close-popup" class="lessicon">
                                    <svg width="16" height="16"><use xlink:href="#icon-close"></use></svg>
                                </div>
                            </div>
                        </div>
                        ${await response.text()}
                    </div>
                `)
            } catch (error) {
                const message = document.querySelector('message-info');
				message.addMessageInfo({ description: error, type: "error" });
                console.error('Failed to fetch page: ', error)
                this.onExitHandler()
            }
        }
    })