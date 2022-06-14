class TemplateFiller {
    get_class_name() {
        throw new Error('Abstract method unimplemented.')
    }
    fill_element(element) {
        throw new Error('Abstract method unimplemented.')
    }
    get_fill_text() {
        return fill_texts_by_class[this.get_class_name()]
    }
    fill() {
        let class_name = this.get_class_name()
        let nodes = document.getElementsByClassName(class_name);
        for (let i = 0; i < nodes.length; i++) {
            this.fill_element(nodes.item(i))
        }
    }
}

class PrependedURLBaseFiller extends TemplateFiller{
    get_class_name() {
        return 'prepend_api_url_base'
    }
    fill_element(element) {
        let href = element.getAttribute('href')
        element.setAttribute('href', this.get_fill_text() + href)
    }
}

class HostIPFiller extends TemplateFiller{
    get_class_name() {
        return 'host_ip'
    }
    fill_element(element) {
        element.innerHTML = this.get_fill_text()        
    }
}

function fill_in_template() {
    let fillers = [
        new HostIPFiller(),
        new PrependedURLBaseFiller(),
    ]
    let i = 0
    for (; i < fillers.length; i++) {
        fillers[i].fill()
    }
}
