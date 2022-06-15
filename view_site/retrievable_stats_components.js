function get_from_url({url, callback=function(response, event){}}){
    let httpreq = new XMLHttpRequest();
    httpreq.open("GET", url, async=true);
    httpreq.onload = function(event) {callback(this, event)}
    httpreq.send(null);
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

class RetrievingSelector {
    constructor(selector_id, stats_table, parent) {
        this.parent = parent
        this.selector = document.getElementById(selector_id)
        let attributes_table_section = this.selector.parentElement.getElementsByClassName('attributes-table-container')[0]
        let completed_table_callback = function() {stats_table.pull_data_given_selections()}
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
    pull_names(retrieve_names_query_fragment) {
        let url_base = get_api_url_base()
        let url=`${url_base}/${retrieve_names_query_fragment}`
        let reference = this
        get_from_url({url, callback: function(response, event) {
            reference.handle_query_response(response, event)
        }})
    }
    handle_query_response(response, event) {
        let obj = JSON.parse(response.responseText)
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
    set_selection(option) {
        this.selection.set_selection(option)
        this.retrieved_options.set_selection(option)
        this.hide_options()
        this.attributes_table.pull_summary(this.get_option_name(option))
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

class AttributesTable {
    constructor(retrieve_summary_query_fragment, attributes_table_section, completed_table_callback) {
        this.retrieve_summary_query_fragment = retrieve_summary_query_fragment
        this.table = attributes_table_section.getElementsByTagName('table')[0]
        this.loading_gif = attributes_table_section.getElementsByTagName('img')[0]
        this.completed_table_callback = completed_table_callback
    }
    pull_summary(item_name) {
        this.selected_item_name = item_name
        let encoded_item_name = encodeURIComponent(item_name)
        let url_base = get_api_url_base()
        let query_fragment = this.retrieve_summary_query_fragment
        let url=`${url_base}/${query_fragment}/${encoded_item_name}`
        this.toggle_loading_gif('on')
        let reference = this
        get_from_url({url, callback: function(response, event){
            reference.load_item_summary(response.responseText, event)
        }})
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
    constructor(table_id) {
        this.table = document.getElementById(table_id)
        this.setup_table_header()
        this.dependencies = []
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
    pull_data_given_selections() {
        if (! this.all_dependencies_loaded()) {
            return
        }
        this.pull_data_from_selections(this.get_selections())
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
