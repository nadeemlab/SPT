async function promise_http_request(method, url) {
    return new Promise(function (resolve, reject) {
        let xhr = new XMLHttpRequest()
        xhr.open(method, url)
        xhr.onload = function () {
            if (this.status >= 200 && this.status < 300) {
                resolve(xhr.response)
            } else {
                reject({
                    status: this.status,
                    statusText: xhr.statusText
                })
            }
        }
        xhr.onerror = function () {
            reject({
                status: this.status,
                statusText: xhr.statusText
            })
        }
        xhr.send()
    })
}

class RetrievableStatsPage {
    constructor(section) {
        this.stats_table = this.discover_stats_table(section)
        let selectors = section.getElementsByClassName('retrieving-selector')
        let stats_table = this.stats_table
        let reference = this
        this.retrieving_selectors = Array.from(selectors).map(function(selector) {
            return new RetrievingSelector(selector.getAttribute('id'), stats_table, reference)
        })
    }
    discover_stats_table(section) {
        throw new Error('Abstract method unimplemented.')
    }
    get_stats_page() {
        return this.stats_table
    }
    close_all_selectors_except(retrieving_selector) {
        for (let other of this.retrieving_selectors) {
            if (! other.is_equal_to(retrieving_selector)) {
                other.hide_options()
            }
        }
    }
    close_all_selectors() {
        this.close_all_selectors_except({})
    }
}

class RetrievingSelector {
    constructor(selector_id, stats_table, parent) {
        this.parent = parent
        this.selector = document.getElementById(selector_id)
        let attributes_table_section = this.selector.parentElement.getElementsByClassName('attributes-table-container')[0]
        let completed_table_callback = async function() {stats_table.pull_data_given_selections()}
        this.attributes_table = new AttributesTable(this.get_retrieve_summary_query_fragment(), attributes_table_section, completed_table_callback)
        stats_table.add_loaded_item_dependency(this.get_display_name(), this.attributes_table)
        let retrieve_names_query_fragment = this.selector.getAttribute('retrieve_names_query_fragment')
        this.pull_names(retrieve_names_query_fragment)
    }
    is_equal_to(retrieving_selector) {
        if (retrieving_selector.hasOwnProperty('selector')) {
            return (this.selector.getAttribute('id') == retrieving_selector.selector.getAttribute('id'))
        } else {
            return false
        }
    }
    get_solicitation_text() {
        return 'Select ' + this.selector.getAttribute('display_solicitation_name')
    }
    get_display_name() {
        return this.selector.getAttribute('display_solicitation_name')
    }
    get_retrieve_summary_query_fragment() {
        return this.selector.getAttribute('retrieve_summary_query_fragment')
    }
    get_attributes_table() {
        return this.attributes_table
    }
    async pull_names(retrieve_names_query_fragment) {
        let url_base = get_api_url_base()
        let url=`${url_base}/${retrieve_names_query_fragment}`
        let reference = this
        let response_text = await promise_http_request('GET', url)
        this.handle_query_response(response_text)
    }
    handle_query_response(response_text) {
        let obj = JSON.parse(response_text)
        let option_names = Array.from(
            new Set(
                obj[Object.keys(obj)[0]]
            )
        )
        this.setup_document_elements(option_names)
    }
    setup_document_elements(option_names) {
        this.selection = new RetrievedSelection(this)
        this.retrieved_options = new RetrievedOptions(this, option_names)
        document.addEventListener('click', this.close_all_selectors)
    }
    select_option(option, event) {
        this.set_selection(option)
    }
    get_option_name(option) {
        return option.innerHTML
    }
    async set_selection(option) {
        this.selection.set_selection(option)
        this.retrieved_options.set_selection(option)
        this.hide_options()
        await this.attributes_table.pull_summary(this.get_option_name(option))
    }
    toggle_options_visibility() {
        this.retrieved_options.toggle_hide()
        this.selection.toggle_arrow()
    }
    hide_options() {
        this.retrieved_options.hide()
        this.selection.inactivate_arrow()
    }
}

class RetrievedSelection {
    constructor(retrieving_selector) {
        this.selection_element = document.createElement('div')
        this.selection_element.setAttribute('class', 'retrieving-selected')
        this.selection_element.innerHTML = retrieving_selector.get_solicitation_text()
        this.selection_element.addEventListener('click', function(event) {
            event.stopPropagation();
            retrieving_selector.parent.close_all_selectors_except(retrieving_selector)
            retrieving_selector.toggle_options_visibility()
        })
        retrieving_selector.selector.appendChild(this.selection_element)
    }
    get_element() {
        return this.selection_element
    }
    set_selection(option) {
        this.selection_element.innerHTML = option.innerHTML
    }
    inactivate_arrow() {
        this.selection_element.classList.remove('select-arrow-active')
    }
    toggle_arrow() {
        this.selection_element.classList.toggle('select-arrow-active')
    }
}

class RetrievedOptions {
    constructor(retrieving_selector, option_names) {
        this.retrieved_options_element = document.createElement('div');
        this.retrieved_options_element.setAttribute('class', 'retrieving-select-items retrieving-select-hide')
        for (let option_name of option_names) {
            let option = document.createElement('div')
            option.innerHTML = option_name;
            option.addEventListener('click', function(event) {retrieving_selector.select_option(this, event)})
            this.retrieved_options_element.appendChild(option)
        }
        retrieving_selector.selector.appendChild(this.retrieved_options_element)
    }
    get_element() {
        return this.retrieved_options_element
    }
    hide() {
        this.retrieved_options_element.classList.add('retrieving-select-hide')
    }
    toggle_hide() {
        this.retrieved_options_element.classList.toggle('retrieving-select-hide')
    }
    set_selection(option) {
        for (let other_option of this.retrieved_options_element.getElementsByClassName('same-as-selected')) {
            other_option.removeAttribute('class')
        }
        option.setAttribute('class', 'same-as-selected');
    }
}

class AttributesTable {
    constructor(retrieve_summary_query_fragment, attributes_table_section, completed_table_callback) {
        this.retrieve_summary_query_fragment = retrieve_summary_query_fragment
        this.table = attributes_table_section.getElementsByTagName('table')[0]
        this.loading_gif = attributes_table_section.getElementsByTagName('img')[0]
        this.completed_table_callback = completed_table_callback
    }
    async pull_summary(item_name) {
        this.selected_item_name = item_name
        let encoded_item_name = encodeURIComponent(item_name)
        let url_base = get_api_url_base()
        let query_fragment = this.retrieve_summary_query_fragment
        let url=`${url_base}/${query_fragment}/${encoded_item_name}`
        this.toggle_loading_gif('on')
        let response_text = await promise_http_request('GET', url)
        this.load_item_summary(response_text)
    }
    load_item_summary(response_text, event) {
        let properties = JSON.parse(response_text)
        this.table.style.display = 'inline'
        for (let key of Object.keys(properties)) {
            let tr = this.create_attribute_row(key, properties[key])
            this.table.appendChild(tr)
        }
        this.toggle_loading_gif('off')
        this.completed_table_callback()
    }
    create_attribute_row(key, property) {
        let tr = document.createElement('tr')
        let key_td = document.createElement('td')
        let value_td = document.createElement('td')
        key_td.setAttribute('class', 'key')
        key_td.innerHTML = key
        value_td.innerHTML = '' + property
        tr.appendChild(key_td)
        tr.appendChild(value_td)
        return tr
    }
    toggle_loading_gif(state) {
        if (state == 'off') {
            this.loading_gif.style.display = 'none'
        }
        if (state == 'on') {
            this.loading_gif.style.display = 'inline'
        }
    }
    is_loaded() {
        return (this.table.children.length > 0)
    }
    get_selected_item_name() {
        return this.selected_item_name
    }
}

class StatsTable {
    constructor(table_id, parent_page) {
        this.table = document.getElementById(table_id)
        this.parent_page = parent_page
        this.setup_table_header()
        this.dependencies = []
    }
    get_parent_page() {
        return this.parent_page
    }
    add_loaded_item_dependency(display_name, attributes_table) {
        this.dependencies.push({ 'display_name' : display_name, 'attributes_table' : attributes_table})
    }
    setup_table_header() {
        throw new Error('Abstract method unimplemented.')
    }
    get_numeric_flags() {
        throw new Error('Abstract method unimplemented.')
    }
    clear_table() {
        this.setup_table_header()
    }
    all_dependencies_loaded() {
        return this.dependencies.every(function(dependency) {
            return dependency['attributes_table'].is_loaded()
        })
    }
    get_selections() {
        let selections = {}
        this.dependencies.forEach(function(dependency) {
            selections[dependency['display_name']] = dependency['attributes_table'].get_selected_item_name()
        })
        return selections
    }
    async pull_data_given_selections() {
        if (! this.all_dependencies_loaded()) {
            return
        }
        await this.pull_data_from_selections(this.get_selections())
    }
    pull_data_from_selections(selections) {
        throw new Error('Abstract method unimplemented.')
    }
    sort_data_rows(column_index, sign) {
        let tr_elements = this.get_ordered_data_rows(column_index, sign)
        for (let i = 0; i < tr_elements.length; i++) {
            this.table.appendChild(tr_elements[i])
        }
        this.update_row_counter()
    }
    get_ordered_data_rows(column_index, sign) {
        let all_rows = Array.from(this.table.children)
        let values_indices = [];
        for (let i = 1; i < all_rows.length; i++) {
            let row = all_rows[i]
            let td = Array.from(row.children)[column_index]
            values_indices.push([i-1, td.innerText]);
        }
        let reference = this
        let compare = function(a, b) {
            if (reference.get_numeric_flags()[column_index]) {
                return (parseFloat(a[1]) - parseFloat(b[1])) * sign;
            } else {
                if (a[1] > b[1]) {
                    return 1 * sign
                }
                if (a[1] < b[1]) {
                    return -1 * sign
                }
                if (a[1] == b[1]) {
                    return 0
                }
            }
        }
        values_indices.sort(compare)
        let new_rows = [];
        for (let i = 0; i < values_indices.length; i++) {
            let index = values_indices[i][0]
            new_rows.push(all_rows[index + 1])
        }
        return new_rows
    }
}

class MultiSelectionHandler {
    add_item(item_name) {
        throw new Error('Abstract method unimplemented.')
    }
    remove_item(item_name) {
        throw new Error('Abstract method unimplemented.')
    }
    is_removal_locked() {
        throw new Error('Abstract method unimplemented.')
    }
}

class SelectionTable {
    constructor(table, names, header, multi_selection_handler) {
        this.table = table
        this.setup_header(header)
        this.multi_selection_handler = multi_selection_handler
        for (let i = 0; i < names.length; i++) {
            this.add_entry(names[i])
        }
    }
    setup_header(header_text) {
        let table_header = document.createElement('tr')
        let th = document.createElement('th')
        th.innerHTML = header_text
        table_header.appendChild(th)
        this.table.appendChild(table_header)
    }
    add_entry(name) {
        let table_row = this.create_table_row(name, this.multi_selection_handler)
        this.table.appendChild(table_row)
    }
    create_table_row(name, multi_selection_handler) {
        let tr = document.createElement('tr')
        let td = document.createElement('td')
        td.innerHTML = name
        td.setAttribute('class', 'first last')
        td.addEventListener('click', function(event) {
            if (this.parentElement.classList.contains('selected-row')) {
                if (! multi_selection_handler.is_removal_locked()) {
                    multi_selection_handler.remove_item(name)
                    this.parentElement.classList.toggle('selected-row')
                }
            } else {
                multi_selection_handler.add_item(name)
                this.parentElement.classList.toggle('selected-row')
            }
        })
        tr.appendChild(td)
        return tr
    }
    clear_selections() {
        for (let tr of this.table.children) {
            tr.classList.remove('selected-row')
        }
    }
    get_dom_element() {
        return this.table
    }
}
