function setup_interactive_elements(){
    setup_openable_sections()
    setup_stats_table()
    setup_retrieving_selectors()
}

function setup_openable_sections() {
    for (let section_in_document of document.getElementsByClassName('openable-section')) {
        new OpenableSection(section_in_document)
    }
}

let stats_table;
function setup_stats_table() {
    stats_table = new PhenotypeFractionsStatsTable('fractions table')
}

let retrieving_selectors = []
function setup_retrieving_selectors() {
    retrieving_selectors.push(new RetrievingSelector('measurement study selector', function() {stats_table.pull_data_given_selections(stats_table)}))
    retrieving_selectors.push(new RetrievingSelector('data analysis study selector', function() {stats_table.pull_data_given_selections(stats_table)}))
    for (r of retrieving_selectors) {
        stats_table.add_loaded_item_dependency(r.get_display_name(), r.get_attributes_table())
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

class RetrievedSelection {
    constructor(retrieving_selector) {
        this.selection_element = document.createElement('div')
        this.selection_element.setAttribute('class', 'retrieving-selected')
        this.selection_element.innerHTML = retrieving_selector.get_solicitation_text()
        this.selection_element.addEventListener('click', function(event) {
            event.stopPropagation();
            close_all_selectors_except(retrieving_selector)
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
            option.addEventListener('click', function(event) {retrieving_selector.select_option(this)})
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
    constructor(selector_id, completed_table_callback) {
        this.selector = document.getElementById(selector_id)
        let attributes_table_section = this.selector.parentElement.getElementsByClassName('attributes-table-container')[0]
        this.attributes_table = new AttributesTable(this.get_retrieve_summary_query_fragment(), attributes_table_section, completed_table_callback)
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
            reference.handle_query_response(reference, response, event)
        }})
    }
    handle_query_response(reference, response, event) {
        let obj = JSON.parse(response.responseText)
        let option_names = Array.from(
            new Set(
                obj[Object.keys(obj)[0]]
            )
        )
        reference.setup_document_elements(option_names)
    }
    setup_document_elements(option_names) {
        this.selection = new RetrievedSelection(this)
        this.retrieved_options = new RetrievedOptions(this, option_names)
        document.addEventListener('click', close_all_selectors_except)
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

function close_all_selectors_except(retrieving_selector) {
    for (let other of retrieving_selectors) {
        if (! other.is_equal_to(retrieving_selector)) {
            other.hide_options()
        }
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
            reference.load_item_summary(reference, response.responseText, event)
        }})
    }
    load_item_summary(reference, response_text, event) {
        let properties = JSON.parse(response_text)
        reference.table.style.display = 'inline'
        for (let key of Object.keys(properties)) {
            let tr = reference.create_attribute_row(key, properties[key])
            reference.table.appendChild(tr)
        }
        reference.toggle_loading_gif('off')
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

function get_from_url({url, callback=function(response, event){}}){
    let httpreq = new XMLHttpRequest();
    httpreq.open("GET", url, async=true);
    httpreq.onload = function(event) {callback(this, event)}
    httpreq.send(null);
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
    pull_data_given_selections(stats_table) {
        if (! stats_table.all_dependencies_loaded()) {
            return
        }
        stats_table.pull_data_from_selections(stats_table.get_selections())
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

class PhenotypeFractionsStatsTable extends StatsTable {
    setup_table_header() {
        this.table.innerHTML = ''
        let header = ["Marker", "Multiplicity", "Assay", "Result", "Mean % <br/>cells positive", "Standard deviation <br/>of % values", "Maximum", "Value", "Minimum", "Value"]
        let header_row = document.createElement("tr")
        for (var i = 0, len = header.length; i < len; ++i) {
            let cell = document.createElement("th")
            cell.innerHTML = header[i] + '&nbsp;'
            let sort_button = document.createElement("span");
            sort_button.innerHTML = " [+] "
            sort_button.setAttribute("onclick", "stats_table.sort_data_rows(" + i + "," + "1)")
            sort_button.setAttribute("class", "sortbutton")
            let sort_button2 = document.createElement("span");
            sort_button2.innerHTML = " [-] "
            sort_button2.setAttribute("onclick", "stats_table.sort_data_rows(" + i + "," + "-1)")
            sort_button2.setAttribute("class", "sortbutton")
            cell.appendChild(sort_button)
            cell.appendChild(sort_button2)
            header_row.appendChild(cell)
        }
        this.table.appendChild(header_row)
    }
    get_numeric_flags() {
        return [false, false, false, false, true, true, false, true, false, true]        
    }
    pull_data_from_selections(selections) {
        let encoded_measurement_study = encodeURIComponent(selections['measurement study'])
        let encoded_data_analysis_study = encodeURIComponent(selections['data analysis study'])
        let url_base = get_api_url_base()
        let url=`${url_base}/phenotype-summary/?specimen_measurement_study=${encoded_measurement_study}&data_analysis_study=${encoded_data_analysis_study}`
        let reference = this
        get_from_url({url, callback: function(response, event) { reference.load_fractions(reference, response, event) }})
    }
    load_fractions(reference, response, event) {
        reference.load_fractions_from_response(response.responseText)
    }
    load_fractions_from_response(response_text) {
        this.clear_table()
        let stats = JSON.parse(response_text)
        let obj = stats[Object.keys(stats)[0]];
        for (let i = 0; i < obj.length; i++) {
            let data_row = obj[i]
            let table_row = document.createElement("tr")
            for (let j = 0; j < 10; j++) {
                let cell = document.createElement("td")
                let entry = data_row[j]
                if (j==4) {
                    let integer_percent = Math.round(parseFloat(entry))
                    let container = document.createElement("div")
                    container.setAttribute("class", "overlayeffectcontainer")
                    let underlay = document.createElement("div")
                    underlay.setAttribute("class", "underlay")
                    let overlay = document.createElement("div")
                    overlay.setAttribute("class", "overlay")
                    overlay.innerHTML = entry
                    underlay.style.width = integer_percent + "%"
                    container.appendChild(underlay)
                    container.appendChild(overlay)
                    cell.appendChild(container)
                } else {
                    if (j==2 || j==3) {
                        entry = entry.replace(/<any>/, '<em>any</em>')
                    }
                    cell.innerHTML = entry
                }
                table_row.appendChild(cell)
            }
            this.table.appendChild(table_row)
        }
        this.update_row_counter()
    }
    update_row_counter() {
        let number_rows = this.table.children.length - 1
        let rowcountbox = this.table.parentElement.getElementsByClassName('row-counter')[0]
        rowcountbox.style.display = "inline-block"
        rowcountbox.getElementsByTagName('span')[0].innerHTML = number_rows
    }
}
