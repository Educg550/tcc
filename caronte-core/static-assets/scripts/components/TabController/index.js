customElements.define('tab-controller',
    class TabController extends HTMLElement {
        connectedCallback() {
            const tabIds = (this.dataset.tabs || '').split(',')
            const panelIds = (this.dataset.panels || '').split(',')

            const tabs = tabIds.map(id => document.getElementById(id.trim()))
            const panels = panelIds.map(id => document.getElementById(id.trim()))

            if (tabs.some(t => !t) || panels.some(p => !p)) return

            const activeIndex = tabs.findIndex(t => t.classList.contains('tab-btn--active'))
            panels.forEach((p, j) => { p.style.display = j === activeIndex ? '' : 'none' })

            tabs.forEach((tab, i) => {
                tab.addEventListener('click', () => {
                    tabs.forEach((t, j) => {
                        t.classList.toggle('tab-btn--active', i === j)
                        panels[j].style.display = i === j ? '' : 'none'
                    })
                })
            })
        }
    }
)
