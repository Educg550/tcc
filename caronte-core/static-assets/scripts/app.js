import './components/MessageInfo/index.js'
import './components/Resizer/index.js'
import './components/Markdown/index.js'
import './components/Popup/index.js'
import './components/FormBuilder/index.js'
import './components/TabController/index.js'

(async () => {
    `strict`

    const dropdowns = document.querySelectorAll("[data-dropdown]")
    dropdowns.forEach(dropdown => {
        const menu_clicker = dropdown.querySelector("#menu_clicker")
        if (menu_clicker)
            menu_clicker.addEventListener("click", toggleDropdown)
    })
    
    let node = null

    function toggleDropdown() {
        if (node != null && node != this.parentNode) return
        const userMenu = this.parentNode.querySelector("#menu")
        if (userMenu.classList.contains("disabled")) {
            userMenu.style.removeProperty('display')

            document.addEventListener("click", clickOutside)
            node = this.parentNode
        } else {
            setTimeout(() => {
                userMenu.style.display = "none"
            }, 100)

            document.removeEventListener("click", clickOutside)
            node = null
        }
        userMenu.classList.toggle("disabled")
    }

    function clickOutside(event) {
        const target = event.target || event.srcElement || event.currentTarget
        if (!node.contains(target)) {
            node.querySelector("#menu_clicker").click()
        }
    }
})()