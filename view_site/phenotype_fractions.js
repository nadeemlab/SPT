function setup_retrievable_stats_page() {
    let section = document.getElementsByClassName('retrievable-stats-page')[0]
    new PhenotypeFractionsStatsPage(section)
}

class PhenotypeFractionsStatsPage extends RetrievableStatsPage {
    constructor(section) {
        super(section)
        this.section = section
        this.phenotype_comparisons_grid = new PhenotypeComparisonsGrid(section, this)
    }
    discover_stats_table(section) {
        let id = section.getElementsByClassName('phenotype-stats-table')[0].getAttribute('id')
        return new PhenotypeFractionsStatsTable(id, this)
    }
    get_section() {
        return this.section
    }
    initialize_phenotype_selection_table() {
        let table = this.get_section().getElementsByClassName('selection-table')[0]
        this.phenotype_selection_table = new SelectionTable(
            table,
            this.stats_table.get_phenotype_names(),
            'Phenotype',
            this.phenotype_comparisons_grid,
        )
    }
}

class PhenotypeFractionsStatsTable extends StatsTable {
    setup_table_header() {
        this.table.innerHTML = ''
        let header = this.get_header_values()
        let header_row = document.createElement('tr')
        for (let i = 0; i < header.length; i++) {
            let cell = document.createElement('th')
            let text = document.createElement('span')
            text.innerHTML = header[i] + ' &nbsp;'
            cell.appendChild(text)
            let sort_button = document.createElement('span');
            sort_button.innerHTML = ' [+] '
            let reference = this
            sort_button.addEventListener('click', function(event) {
                reference.sort_data_rows(i, 1)
            })
            sort_button.setAttribute('class', 'sortbutton')
            let sort_button2 = document.createElement('span');
            sort_button2.innerHTML = ' [-] '
            sort_button2.addEventListener('click', function(event) {
                reference.sort_data_rows(i, -1)
            })
            sort_button2.setAttribute('class', 'sortbutton')
            cell.appendChild(sort_button)
            cell.appendChild(sort_button2)
            header_row.appendChild(cell)
        }
        this.table.appendChild(header_row)
    }
    patch_header(outcome_column) {
        let index_of_assay = this.get_header_values().indexOf('Result')
        let span = this.table.children[0].children[index_of_assay].children[0]
        span.innerHTML = outcome_column
    }
    get_assay_index() {
        return 1
    }
    get_outcome_column(obj) {
        let assay_index = this.get_assay_index()
        let assay_values = new Set(obj.map(function(data_row) {return data_row[assay_index]}))
        assay_values.delete('<any>')
        return Array.from(assay_values)[0]
    }
    get_header_values() {
        return ['Phenotype', 'Result', 'Mean % <br/>cells positive', 'Standard deviation <br/>of % values', 'Maximum', 'Value', 'Minimum', 'Value']        
    }
    get_numeric_flags() {
        return [false, false, true, true, false, true, false, true]        
    }
    async pull_data_from_selections(selections) {
        let encoded_measurement_study = encodeURIComponent(selections['measurement study'])
        let encoded_data_analysis_study = encodeURIComponent(selections['data analysis study'])
        let url_base = get_api_url_base()
        let url=`${url_base}/phenotype-summary/?specimen_measurement_study=${encoded_measurement_study}&data_analysis_study=${encoded_data_analysis_study}`
        let response_text = await promise_http_request('GET', url)
        this.load_fractions_from_response(response_text)
    }
    async load_fractions_from_response(response_text) {
        this.clear_table()
        let stats = JSON.parse(response_text)
        let obj = stats[Object.keys(stats)[0]]
        let outcome_column = this.get_outcome_column(obj)
        for (let i = 0; i < obj.length; i++) {
            this.table.appendChild(this.create_table_row(obj[i]))
        }
        this.patch_header(outcome_column)
        this.update_row_counter()
        this.record_phenotype_names_from_response(obj)
        this.get_parent_page().initialize_phenotype_selection_table()
        await this.get_and_handle_phenotype_criteria_names()
    }
    create_table_row(data_row) {
        let table_row = document.createElement('tr')
        data_row.splice(this.get_assay_index(), 1)
        for (let j = 0; j < data_row.length; j++) {
            let cell = document.createElement('td')
            let entry = data_row[j]
            if (this.get_header_values()[j] == 'Result') {
                entry = entry.replace(/<any>/, '<em>any</em>')
            }
            if (this.get_header_values()[j] == 'Mean % <br/>cells positive') {
                let integer_percent = Math.round(parseFloat(entry))
                let container = document.createElement('div')
                container.setAttribute('class', 'overlayeffectcontainer')
                let underlay = document.createElement('div')
                underlay.setAttribute('class', 'underlay')
                let overlay = document.createElement('div')
                overlay.setAttribute('class', 'overlay')
                overlay.innerHTML = entry
                underlay.style.width = integer_percent + '%'
                container.appendChild(underlay)
                container.appendChild(overlay)
                cell.appendChild(container)
            } else if (this.get_header_values()[j] == 'Phenotype') {
                cell.setAttribute('class', 'hoverdiv')
                let hoverdiv_content = document.createElement('span')
                hoverdiv_content.setAttribute('class', 'hoverdiv-content')
                hoverdiv_content.innerHTML = entry
                let tooltip = document.createElement('span')
                tooltip.setAttribute('class', 'tooltip')
                tooltip.innerHTML = entry
                cell.appendChild(hoverdiv_content)
                cell.appendChild(tooltip)
            } else {
                cell.innerHTML = entry
            }
            cell.addEventListener('click', function(event) {
                this.parentElement.classList.toggle('selected-row')
            })
            if (j == 0) {
                cell.classList.toggle('first')
            }
            if (j == data_row.length - 1) {
                cell.classList.toggle('last')
            }
            table_row.appendChild(cell)
        }
        return table_row
    }
    record_phenotype_names_from_response(obj) {
        let index = this.get_header_values().indexOf('Phenotype')
        this.phenotype_names = Array.from(new Set(Array.from(obj).map(function(data_row) {return data_row[index]}))).sort()
    }
    get_phenotype_names() {
        return this.phenotype_names
    }
    async get_and_handle_phenotype_criteria_names() {
        for (let phenotype_name of this.get_phenotype_names()) {
            await this.get_and_handle_phenotype_criteria_name(phenotype_name)
        }
    }
    async get_and_handle_phenotype_criteria_name(phenotype_name) {
        let encoded_phenotype_name = encodeURIComponent(phenotype_name)
        let url_base = get_api_url_base()
        let url=`${url_base}/phenotype-criteria-name/?phenotype_symbol=${encoded_phenotype_name}`
        let response_text = await promise_http_request('GET', url)
        this.update_phenotype_criteria_name(phenotype_name, response_text)
    }
    update_phenotype_criteria_name(phenotype_name, response_text) {
        let obj = JSON.parse(response_text)
        let phenotype_criteria_name = obj[Object.keys(obj)[0]]
        let phenotype_index = this.get_header_values().indexOf('Phenotype')
        for (let i = 1; i < this.table.children.length; i++) {
            let phenotype_name_cell = this.table.children[i].children[phenotype_index]
            let row_phenotype_name = phenotype_name_cell.getElementsByClassName('hoverdiv-content')[0].innerHTML
            if (row_phenotype_name == phenotype_name) {
                let tooltip = phenotype_name_cell.getElementsByClassName('tooltip')[0]
                tooltip.innerHTML = this.markup_criteria_name(phenotype_criteria_name)
            }
        }
    }
    markup_criteria_name(phenotype_criteria_name) {
        let positives_marked = phenotype_criteria_name.replace(/([a-zA-Z0-9\_\.]+\+)/g, '<span class="positives">$1</span> ')
        let and_negatives_marked = positives_marked.replace(/([a-zA-Z0-9\_\.]+\-)/g, '<span class="negatives">$1</span> ')
        return and_negatives_marked
    }
    update_row_counter() {
        let number_rows = this.table.children.length - 1
        let rowcountbox = this.table.parentElement.getElementsByClassName('row-counter')[0]
        rowcountbox.style.display = 'inline-block'
        rowcountbox.getElementsByTagName('span')[0].innerHTML = number_rows
    }
}

class PairwiseComparisonsGrid extends MultiSelectionHandler{
    constructor(section) {
        super()
        this.labels = []
        this.table = this.setup_table(section)
        this.detail_bar = this.setup_detail_bar()
        this.feature_matrix = this.setup_feature_matrix()
        this.lock_count = 0
    }
    setup_table(section) {
        let table = section.getElementsByClassName('pairwise-comparison')[0]
        table.innerHTML = ''
        let tr = document.createElement('tr')
        tr.setAttribute('class', 'pairwise-comparison-header-row')
        tr.appendChild(document.createElement('th'))
        table.appendChild(tr)
        return table
    }
    setup_detail_bar() {
        let detail_bar = this.table.parentElement.getElementsByTagName('span')[0]
        detail_bar.innerHTML = '%'
        return detail_bar
    }
    setup_feature_matrix() {
        return new FeatureMatrix(this.table.parentElement.parentElement.getElementsByClassName('feature-matrix')[0])
    }
    lock_interaction() {
        this.lock_count = this.lock_count + 1
    }
    unlock_interaction() {
        this.lock_count = this.lock_count - 1
    }
    locked() {
        return (this.lock_count > 0)
    }
    async add_item(item_name) {
        this.lock_interaction()
        await this.add_label(item_name)
        this.unlock_interaction()
    }
    remove_item(item_name) {
        this.remove_label(item_name)
    }
    async add_label(label) {
        if (this.labels.includes(label)) {
            return
        }
        this.add_new_row(label)
        this.add_new_column(label)
        this.labels.push(label)
        await this.fire_off_queries_for_new_cell_values(label)
    }
    add_new_row(row_label) {
        let tr = document.createElement('tr')
        tr.setAttribute('row_label', row_label)
        tr.appendChild(this.create_row_label_cell(row_label))
        for (let column_label of this.labels) {
            let td = this.create_new_cell(row_label, column_label)
            tr.appendChild(td)
        }
        this.table.appendChild(tr)
    }
    create_row_label_cell(row_label) {
        let th = document.createElement('th')
        th.innerHTML = row_label
        th.setAttribute('class', 'pairwise-comparison-row-label')
        return th
    }
    create_new_cell(row_label, column_label) {
        console.log(JSON.stringify([row_label, column_label]))
        let td = document.createElement('td')
        td.setAttribute('class', 'pairwise-comparison-cell')
        let span = document.createElement('span')
        td.appendChild(span)
        let mini_loading_gif = document.createElement('img')
        mini_loading_gif.setAttribute('src', 'mini_loading_gif.gif')
        mini_loading_gif.setAttribute('class', 'mini-loading-gif')
        td.appendChild(mini_loading_gif)
        let reference = this
        td.addEventListener('mousemove', function(event) {
            let value = this.getElementsByTagName('span')[0].innerText
            reference.set_detail_bar(value)
            reference.highlight_cell_pair(row_label, column_label)
        })
        td.addEventListener('mouseleave', function(event) {
            reference.set_detail_bar('')
            reference.unhighlight_cell_pair(row_label, column_label)
        })
        td.addEventListener('click', function(event) {
            reference.toggle_cell_selection(this, row_label, column_label)
            reference.toggle_phenotype_pair_details(row_label, column_label)
        })
        return td
    }
    get_cells(row_label, column_label) {
        let cells = []
        cells.push(this.get_cell(row_label, column_label))
        if (row_label != column_label) {
            cells.push(this.get_cell(column_label, row_label))            
        }
        return cells
    }
    highlight_cell_pair(row_label, column_label) {
        for (let cell of this.get_cells(row_label, column_label)) {
            cell.classList.remove('highlighted-cell')
            cell.classList.add('highlighted-cell')
        }
    }
    unhighlight_cell_pair(row_label, column_label) {
        for (let cell of this.get_cells(row_label, column_label)) {
            cell.classList.remove('highlighted-cell')
        }
    }
    set_detail_bar(value) {
        if (value != '') {
            let percentage = Math.round(100 * 100 * value)/100
            this.detail_bar.innerHTML = percentage + ' %'
        } else {
            this.detail_bar.innerHTML = '%'            
        }
    }
    toggle_cell_selection(cell, row_label, column_label) {
        cell.classList.toggle('detail-selected')
        if (row_label != column_label) {
            let other_cell = this.get_cell(column_label, row_label)
            other_cell.classList.toggle('detail-selected')
        }
    }
    toggle_phenotype_pair_details(row_label, column_label) {
        if (this.feature_matrix.is_showing(row_label, column_label)) {
            this.feature_matrix.remove_feature(row_label, column_label)
        } else {
            let feature_values = this.retrieve_feature_values(row_label, column_label)
            this.feature_matrix.add_feature(row_label, column_label, feature_values)
        }
    }
    retrieve_feature_values(row_label, column_label) {
        // egg
        return 'dummy feature values'
    } 
    add_new_column(label) {
        this.table.children[0].appendChild(this.create_column_label_cell(label))
        for (let i = 1; i < this.table.children.length; i++) {
            let tr = this.table.children[i]
            this.add_new_column_to_row(tr, label)
        }
    }
    create_column_label_cell(column_label) {
        let th = document.createElement('th')
        let span = document.createElement('span')
        span.innerHTML = column_label
        th.appendChild(span)
        th.setAttribute('class', 'pairwise-comparison-column-label')
        return th
    }
    add_new_column_to_row(tr, column_label) {
        let td = this.create_new_cell(tr.getAttribute('row_label'), column_label)
        tr.appendChild(td)
    }
    remove_label(label) {
        if (! this.labels.includes(label)) {
            return
        }
        let index = this.labels.indexOf(label)
        this.labels.splice(index, 1)
        this.remove_column(label, index)
        this.remove_row(label, index)
    }
    remove_column(label, index) {
        let column_label_element = this.table.children[0].children[index + 1]
        this.table.children[0].removeChild(column_label_element)
        for (let i = 1; i < this.table.children.length; i++) {
            let tr = this.table.children[i]
            let cell = tr.children[index + 1]
            tr.removeChild(cell)
        }
    }
    remove_row(label, index) {
        let labelled_row = this.table.children[index + 1]
        this.table.removeChild(labelled_row)
    }
    async fire_off_queries_for_new_cell_values(label) {
        let promises = []
        for (let existing_label of this.labels) {
            let reference = this
            promises.push(
                new Promise(async function(resolve, reject) {
                    await reference.fire_off_query_for_cell_value(existing_label, label)
                    resolve()
                })
            )
        }
        await Promise.all(promises)
    }
    async fire_off_query_for_cell_value(row_label, column_label) {
        let percentage = await this.get_pair_comparison(row_label, column_label)
        this.set_cell_contents_by_location(row_label, column_label, percentage)
    }
    get_cell(row_label, column_label) {
        let row_index = this.labels.indexOf(row_label)
        let column_index = this.labels.indexOf(column_label)
        let cell = this.table.children[1 + row_index].children[1 + column_index]
        return cell        
    }
    set_cell_contents_by_location(row_label, column_label, percentage) {
        let cell = this.get_cell(row_label, column_label)
        this.set_cell_contents(cell, percentage)
        if (row_label != column_label) {
            let other_cell = this.get_cell(column_label, row_label)
            this.set_cell_contents(other_cell, percentage)
        }
    }
    set_cell_contents(cell, percentage) {
        let value = percentage / 100
        let color = this.get_cool_warm(value)
        let red = color['red']
        let green = color['green']
        let blue = color['blue']
        cell.style.background = `rgb(${red}, ${green}, ${blue})`
        let span = cell.getElementsByTagName('span')[0]
        span.innerHTML = value
        let img = span.parentElement.getElementsByTagName('img')[0]
        img.remove()
    }
    get_cool_warm(value) {
        return this.interpolate(value, [242, 242, 242], [252, 0, 0])
    }
    interpolate(value, initial, final) {
        let skewness = 1/4
        let rescaled = Math.pow(value, skewness)
        return {
            'red' : (1 - value) * initial[0] + value * final[0],
            'green' : (1 - value) * initial[1] + value * final[1],
            'blue' : (1 - value) * initial[2] + value * final[2],
        }
    }
    async get_pair_comparison(row_label, column_label) {
        throw new Error('Abstract method unimplemented.')
    }
}

class PhenotypeComparisonsGrid extends PairwiseComparisonsGrid {
    constructor(section, parent) {
        super(section)
        this.parent = parent
    }
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    async get_pair_comparison(row_label, column_label) {
        let signatures = []
        for (let label of [row_label, column_label]) {
            let signature = await this.get_signature(label)
            signatures.push(signature)
        }
        let merged_signature = this.merge_criteria(signatures)

        let parameter_names = ['positive_markers_tab_delimited', 'negative_markers_tab_delimited', 'specimen_measurement_study']
        let parameter_values = []
        for (let key of ['positive markers', 'negative markers']) {
            parameter_values.push(encodeURIComponent(merged_signature[key].join('\t')))
        }
        parameter_values.push(encodeURIComponent(this.parent.get_stats_page().get_selections()['measurement study']))

        let fragments = []
        for (let i = 0; i < 3; i++) {
            fragments.push([parameter_names[i], parameter_values[i]].join('='))
        }
        let url_base = get_api_url_base()
        let counts_url = `${url_base}/anonymous-phenotype-counts/?` + fragments.join('&')
        let counts_response = await promise_http_request('GET', counts_url)

        let root = JSON.parse(counts_response)
        let cell_count = 0
        for (let entry of root['phenotype counts']['per specimen counts']) {
            cell_count = cell_count + entry['phenotype count']
        }

        let percentage = 100 * cell_count / root['phenotype counts']['total number of cells in all specimens of study']
        percentage = Math.round(10000 * percentage) / 10000
        return percentage
    }
    async get_signature(phenotype_label) {
        let url_base = get_api_url_base()
        let url = `${url_base}/phenotype-criteria/?phenotype_symbol=` + encodeURIComponent(phenotype_label)
        let response = await promise_http_request('GET', url)
        let wrapped_object = JSON.parse(response)
        let signature = wrapped_object[Object.keys(wrapped_object)[0]]
        return signature
    }
    merge_criteria(signatures) {
        let positive_markers = []
        let negative_markers = []
        for (let signature of signatures) {
            positive_markers = positive_markers.concat(signature['positive markers'])
            negative_markers = negative_markers.concat(signature['negative markers'])
        }
        return {
            'positive markers' : Array.from(new Set(positive_markers)),
            'negative markers' : Array.from(new Set(negative_markers)),
        }
    }
}

class FeatureMatrix {
    constructor(table) {
        this.table = table
        this.showing_features = []
        this.update_table()
    }
    update_table() {
        this.clear_table()
        this.create_header()
        this.create_rows()
    }
    clear_table() {
        this.table.innerHTML = ''
    }
    create_header() {
        let tr = document.createElement('tr')
        let th = document.createElement('th')
        th.innerHTML = 'Sample'
        tr.appendChild(th)
        this.table.appendChild(tr)
    }
    create_rows() {
        for (let key of this.showing_features) {
            let tr = document.createElement('tr')
            let td = document.createElement('td')
            td.innerText = key
            tr.appendChild(td)
            this.table.appendChild(tr)
        }
    }
    is_showing(row_label, column_label) {
        let key = this.get_key(row_label, column_label)
        if (this.showing_features.includes(key)) {
            return true
        } else {
            return false
        }
    }
    get_key(row_label, column_label) {
        let pair = [row_label, column_label]
        pair.sort()
        return JSON.stringify(pair)
    }
    remove_feature(row_label, column_label) {
        let key = this.get_key(row_label, column_label)
        let index = this.showing_features.indexOf(key)
        this.showing_features.splice(index, 1)
        this.update_table()
    }
    add_feature(row_label, column_label, feature_values) {
        let key = this.get_key(row_label, column_label)
        this.showing_features.push(key)
        this.update_table()
    }
}
