function setup_openable_sections() {
    for (let section_in_document of document.getElementsByClassName('openable-section')) {
        new OpenableSection(section_in_document)
    }
}

class OpenableSection {
    constructor(section_in_document) {
        this.clickable_text = section_in_document.getElementsByClassName('show-more-button')[0].getElementsByClassName('clickable-text')[0]
        this.title = this.clickable_text.innerHTML.replace(/\+ /, '')
        this.showable_text = section_in_document.getElementsByClassName('toggleable-text')[0]
        let reference = this
        this.clickable_text.addEventListener('click', function(event) { reference.toggle_open(event) })
    }
    toggle_open(event) {
        if (this.clickable_text.innerHTML == '+ ' + this.title) {
            this.clickable_text.innerHTML = '- ' + this.title
            this.showable_text.style.display = 'block'
        } else {
            this.clickable_text.innerHTML = '+ ' + this.title
            this.showable_text.style.display = 'none'
        }
    }
}
