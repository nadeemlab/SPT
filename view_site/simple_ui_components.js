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

class ExportableElementWidget {
    constructor(exportable_element, hovering_trigger_element) {
        this.exportable_element = exportable_element
        this.hovering_trigger_element = hovering_trigger_element
        this.ensure_relative_positioning()
        this.create_and_add_export_buttons_panel()
        this.setup_mouseover_events()
    }
    get_exportable_element() {
        return this.exportable_element
    }
    get_hovering_trigger_element() {
        return this.hovering_trigger_element
    }
    ensure_relative_positioning() {
        if (! (this.get_hovering_trigger_element().style.position == 'relative')) {
            this.get_hovering_trigger_element().style.position = 'relative'
            console.warn('Exportable elements should have the "relative" position style property.')
        }
    }
    create_and_add_export_buttons_panel() {
        let export_buttons_panel = document.createElement('div')
        export_buttons_panel.classList.add('export-buttons-panel')
        export_buttons_panel.style.display = 'none'
        this.add_export_buttons(export_buttons_panel)
        this.get_hovering_trigger_element().prepend(export_buttons_panel)
    }
    get_export_buttons_panel() {
        return this.get_exportable_element().getElementsByClassName('export-buttons-panel')[0]
    }
    add_export_buttons(export_buttons_panel) {
        for (let name of this.get_button_types()) {
            let button = this.create_export_button(name)
            button.classList.add(name)
            export_buttons_panel.appendChild(button)
        }
    }
    get_button_types() {
        return ['copy-text', 'save-html']
    }
    create_export_button(name) {
        let button = document.createElement('span')
        button.classList.add(name)
        let reference = this
        button.addEventListener('click', function(event) {
            reference.handle_click(this)
        })
        return button
    }
    get_export_button(name) {
        return this.get_export_buttons_panel().getElementsByClassName(name)[0]
    }
    setup_mouseover_events() {
        let reference = this
        this.get_hovering_trigger_element().addEventListener('mouseenter', function(event) {
            reference.show_export_buttons()
        })
        this.get_hovering_trigger_element().addEventListener('mouseleave', function(event) {
            reference.hide_export_buttons()
        })
    }
    show_export_buttons() {
        this.get_export_buttons_panel().style.display = 'inline'
    }
    hide_export_buttons() {
        this.get_export_buttons_panel().style.display = 'none'
    }
    handle_click(button) {
        if (button.classList.contains('copy-text')) {
            this.copy_text_to_clipboard()
        }
        if (button.classList.contains('save-html')) {
            this.save_html_to_file()
        }
    }
    copy_text_to_clipboard() {
        if (this.get_exportable_element().tagName == 'TABLE') {
            let rows = this.get_string_rows()
            let csv_contents = rows.join('\n')
            navigator.clipboard.writeText(csv_contents)
        }
    }
    get_string_rows() {
        let rows = []
        for (let tr of this.get_exportable_element().getElementsByTagName('tr')) {
            rows.push(this.get_string_row(tr))
        }
        return rows
    }
    get_string_row(tr) {
        let text_elements = []
        let cells = Array.from(tr.getElementsByTagName('th')).concat(Array.from(tr.getElementsByTagName('td')))
        for (let cell of cells) {
            let text = cell.innerText
            text = text.normalize()
            text = text.replace('\n', '')
            text = text.replace(/[^\x00-\x7F]/g, '')
            if (text.indexOf('"') == -1) {
                text_elements.push('"' + text + '"')
            } else {
                text_elements.push(text)
            }
        }
        return text_elements.join(',')
    }
    save_html_to_file() {

    }
}