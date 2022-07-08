function setup_retrievable_stats_page() {
    let section = document.getElementsByClassName('retrievable-stats-page')[0]
    new PhenotypeFractionsStatsPage(section)
    make_page_exportable()
    make_sections_exportable()
    add_scroll_padding()
}

function make_page_exportable() {
    let main_section = document.getElementsByClassName('all-content-section')[0]
    let all_headers = main_section.querySelectorAll('h1,h2,h3,h4')
    if (all_headers.length == 0) {
        return
    }
    let first_header_encountered = all_headers[0]
    let export_widget = new ExportableElementWidget(main_section, first_header_encountered, raw_style_sheet)
}

function make_sections_exportable() {
    let openable_sections = document.getElementsByClassName('openable-section')
    for (let section of openable_sections) {
        let header = section.getElementsByClassName('show-more-button')[0]
        let export_widget = new ExportableElementWidget(section, header, raw_style_sheet)    
    }
}

function add_scroll_padding() {
    let whitespace_element = document.createElement('div')
    resize_whitespace_padding(whitespace_element)
    let body = document.getElementsByTagName('body')[0]
    body.appendChild(whitespace_element)
    body.addEventListener('resize', function(event) {
        resize_whitespace_padding(whitespace_element)
    })
    window.scrollTo({top: 0})
}

function resize_whitespace_padding(whitespace_element) {
    let viewport_height = window.innerHeight
    let viewport_width = window.innerWidth
    whitespace_element.style.position = 'absolute'
    whitespace_element.style.height = viewport_height + 'px'
    whitespace_element.style.width = viewport_width + 'px'
}

class PhenotypeFractionsStatsPage extends RetrievableStatsPage {
    constructor(section) {
        super(section)
        this.section = section
        this.specimen_level_counts = new SpecimenLevelCounts()
        this.phenotype_comparisons_grid = new PhenotypeComparisonsGrid(section, this, this.specimen_level_counts)
    }
    discover_stats_table(section) {
        let id = section.getElementsByClassName('phenotype-stats-table')[0].getAttribute('id')
        return new PhenotypeFractionsStatsTable(id, this)
    }
    get_section() {
        return this.section
    }
    make_study_dependent_sections_available() {
        for (let element of this.section.getElementsByClassName('clickable-text')) {
            element.classList.remove('unavailable')
        }
    }
    initialize_phenotype_selection_table() {
        let table = this.get_section().getElementsByClassName('selection-table')[1]
        this.phenotype_selection_table = new SelectionTable(
            table,
            this.stats_table.get_phenotype_names(),
            'Phenotype',
            this.phenotype_comparisons_grid,
        )
    }
    initialize_channel_selection_table() {
        let table = this.get_section().getElementsByClassName('selection-table')[0]
        let phenotype_adder = new PhenotypeAdder(this.phenotype_selection_table)
        this.channel_selection_table = new SelectionTable(
            table,
            this.stats_table.get_channel_names(),
            'Select markers',
            phenotype_adder,
        )
        phenotype_adder.register_selections_clearer(this.channel_selection_table)
        this.phenotype_comparisons_grid.register_alternative_signatures_provider(phenotype_adder.get_signatures_provider())
    }
}

class PhenotypeAdder extends MultiSelectionHandler{
    constructor(phenotype_selection_table) {
        super()
        this.phenotype_selection_table = phenotype_selection_table
        this.positive_markers = []
        this.signatures_provider = new SignaturesProvider()
        this.setup_add_button()
    }
    setup_add_button() {
        this.add_button = this.phenotype_selection_table.get_dom_element().parentElement.parentElement.getElementsByClassName('add-button')[0]
        this.add_button.classList.add('unavailable')
        let reference = this
        this.add_button.addEventListener('click', function(event) {
            reference.finalize_new_phenotype_definition()
        })
    }
    add_item(item_name) {
        if (! this.positive_markers.includes(item_name)) {
            this.positive_markers.push(item_name)
            this.add_button.classList.remove('unavailable')
        }
    }
    remove_item(item_name) {
        if (this.positive_markers.includes(item_name)) {
            let index = this.positive_markers.indexOf(item_name)
            this.positive_markers.splice(index, 1)
        }
        if (this.positive_markers.length == 0) {
            this.add_button.classList.add('unavailable')
        }
    }
    is_removal_locked() {
        return false
    }
    finalize_new_phenotype_definition() {
        if (this.positive_markers.length == 0) {
            return
        }
        this.positive_markers.sort()
        let phenotype_munged_name = this.positive_markers.join('+ ') + '+'
        let new_phenotype = {'name' : phenotype_munged_name, 'positive markers' : [...this.positive_markers]}
        this.positive_markers = []
        this.signatures_provider.push_phenotype(new_phenotype)
        this.phenotype_selection_table.add_entry(phenotype_munged_name)
        this.clearer.clear_selections()
        this.add_button.classList.add('unavailable')
    }
    register_selections_clearer(clearer) {
        this.clearer = clearer
    }
    get_signatures_provider() {
        return this.signatures_provider
    }
}

class SignaturesProvider {
    constructor() {
        this.signatures = []
    }
    has_label(phenotype_label) {
        for (let signature of this.signatures) {
            if (signature['name'] == phenotype_label) {
                return true
            }
        }
        return false
    }
    get_signature(phenotype_label) {
        for (let signature of this.signatures) {
            if (signature['name'] == phenotype_label) {
                return {'positive markers' : signature['positive markers'], 'negative markers' : []}
            }
        }
    }
    push_phenotype(new_phenotype) {
        this.signatures.push(new_phenotype)        
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
        let export_widget = new ExportableElementWidget(this.table, this.table, raw_style_sheet)
    }
    patch_header(outcome_column) {
        let index_of_assay = this.get_header_values().indexOf('Result')
        let span = this.table.children[1].children[index_of_assay].children[0]
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
    get_custom_comparator(column_index, sign) {
        if (column_index == this.get_header_values().indexOf('Phenotype')) {
            let reference = this
            return function(a, b) {
                let multiplicity_a = reference.get_multiplicity(a[1])
                let multiplicity_b = reference.get_multiplicity(b[1])
                if (multiplicity_a == multiplicity_b) {
                    if (a[1] > b[1]) {
                        return 1 * sign
                    }
                    if (a[1] < b[1]) {
                        return -1 * sign
                    }
                    if (a[1] == b[1]) {
                        return 0
                    }
                } else {
                    let internal_sign = 0
                    if (multiplicity_a > multiplicity_b) {
                        internal_sign = 1
                    } else {
                        internal_sign = -1
                    }
                    return internal_sign * sign
                }
            }
        }
        return null
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
        let obj_without_multiplicity = this.drop_multiplicity(obj)
        let outcome_column = this.get_outcome_column(obj_without_multiplicity)
        for (let i = 0; i < obj_without_multiplicity.length; i++) {
            this.table.appendChild(this.create_table_row(obj_without_multiplicity[i]))
        }
        this.patch_header(outcome_column)
        this.update_row_counter()
        this.record_phenotype_names_from_response(obj)
        this.get_parent_page().initialize_phenotype_selection_table()
        this.get_parent_page().initialize_channel_selection_table()
        this.get_parent_page().make_study_dependent_sections_available()
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
    drop_multiplicity(obj) {
        let index_of_multiplicity_field = 1
        return Array.from(obj).map( function(data_row) {
            let data_row_copy = [...data_row]
            data_row_copy.splice(index_of_multiplicity_field, 1)
            return data_row_copy
        })        
    }
    record_phenotype_names_from_response(obj) {
        this.phenotype_names = this.retrieve_phenotype_names_by_multiplicity(obj, 'composite')
        this.channel_names = this.retrieve_phenotype_names_by_multiplicity(obj, 'single')
    }
    get_multiplicity(phenotype_or_channel_name) {
        let name = phenotype_or_channel_name
        if (this.phenotype_names.includes(name)) {
            return 'composite'
        }
        if (this.channel_names.includes(name)) {
            return 'single'
        }
        console.warn('Phenotype or channel name "' + name + '" not known.')
    }
    retrieve_phenotype_names_by_multiplicity(obj, multiplicity) {
        let rows_with_given_multiplicity = this.get_rows_with_multiplicity(obj, multiplicity)
        let index = this.get_header_values().indexOf('Phenotype')
        let names = Array.from(new Set(
            rows_with_given_multiplicity.map(function(data_row) {
                return data_row[index]
            })
        ))
        names.sort()
        return names
    }
    get_rows_with_multiplicity(obj, multiplicity) {
        let index_of_multiplicity_field = 1
        return Array.from(obj).filter( function(data_row) {
            return (data_row[index_of_multiplicity_field] == multiplicity)
        }).map( function(data_row) {
            let data_row_copy = [...data_row]
            data_row_copy.splice(index_of_multiplicity_field, 1)
            return data_row_copy            
        })
    }
    get_phenotype_names() {
        return this.phenotype_names
    }
    get_channel_names() {
        return this.channel_names
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
        for (let i = 2; i < this.table.children.length; i++) {
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
        let number_rows = this.table.children.length - 2
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
    is_removal_locked() {
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
            if (Array.from(this.getElementsByTagName('img')).length == 0) {
                reference.toggle_cell_selection(this, row_label, column_label)
                reference.toggle_phenotype_pair_details(row_label, column_label)
            }
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
        throw new Error('Abstract method unimplemented.')
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
        let rgb_color = CoolWarmColorMap.get_rgb_color(value)
        cell.style.background = rgb_color
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

class CoolWarmColorMap {
    static get_rgb_color(value) {
        let color = this.get_cool_warm(value)
        let red = color['red']
        let green = color['green']
        let blue = color['blue']
        return `rgb(${red}, ${green}, ${blue})`
    }
    static get_cool_warm(value) {
        return this.interpolate(value, [242, 242, 242], [252, 0, 0])
    }
    static interpolate(value, initial, final) {
        let skewness = 1/4
        let rescaled = Math.pow(value, skewness)
        return {
            'red' : (1 - value) * initial[0] + value * final[0],
            'green' : (1 - value) * initial[1] + value * final[1],
            'blue' : (1 - value) * initial[2] + value * final[2],
        }
    }
}

class PhenotypeComparisonsGrid extends PairwiseComparisonsGrid {
    constructor(section, parent, specimen_level_counts) {
        super(section)
        this.parent = parent
        this.signatures_provider = null
        this.specimen_level_counts = specimen_level_counts
    }
    register_alternative_signatures_provider(signatures_provider) {
        this.signatures_provider = signatures_provider
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
        let counts = JSON.parse(JSON.stringify(root['phenotype counts']['per specimen counts']))
        let phenotype_symbol = this.specimen_level_counts.get_key(row_label, column_label)
        this.specimen_level_counts.cache_counts(phenotype_symbol, counts)

        let percentage = 100 * cell_count / root['phenotype counts']['total number of cells in all specimens of study']
        percentage = Math.round(10000 * percentage) / 10000
        return percentage
    }
    async get_signature(phenotype_label) {
        if (! (this.signatures_provider == null) ) {
            if (this.signatures_provider.has_label(phenotype_label)) {
                return this.signatures_provider.get_signature(phenotype_label)
            }
        }
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
    retrieve_feature_values(row_label, column_label) {
        if (this.specimen_level_counts.has_cached(row_label, column_label)) {
            return this.specimen_level_counts.get_counts(row_label, column_label)
        }
    } 
}

class SpecimenLevelCounts {
    constructor() {
        this.specimen_counts_by_phenotype_name = {}
    }
    cache_counts(phenotype_symbol, counts) {
        counts.sort(function(a,b) {
            if(a['specimen'] < b['specimen']){
                return -1;
            }else if(a['specimen'] > b['specimen']){
                return 1;
            }
            return 0;
        })
        this.specimen_counts_by_phenotype_name[phenotype_symbol] = counts
    }
    has_cached(row_label, column_label) {
        let key = this.get_key(row_label, column_label)
        return (key in this.specimen_counts_by_phenotype_name)
    }
    get_key(row_label, column_label) {
        let pair = [row_label, column_label]
        pair.sort()
        return JSON.stringify(pair)
    }
    get_counts(row_label, column_label) {
        return this.specimen_counts_by_phenotype_name[this.get_key(row_label, column_label)]
    }
}

class FeatureMatrix {
    constructor(table) {
        this.table = table
        this.showing_features = []
        this.feature_labels = {}
        this.feature_values_by_name = {}
        this.update_table()
    }
    update_table() {
        this.clear_table()
        this.create_header()
        this.create_rows()
        this.add_exportability()
    }
    clear_table() {
        this.table.innerHTML = ''
    }
    create_header() {
        if (this.showing_features.length == 0) {
            return
        }
        let tr = document.createElement('tr')
        let th = document.createElement('th')
        let th_span = document.createElement('span')
        th.appendChild(th_span)
        th_span.innerText = 'Sample'
        tr.appendChild(th)
        for (let feature_name in this.feature_labels) {
            let feature_label = this.feature_labels[feature_name]
            let th_feature = document.createElement('th')
            let span = document.createElement('span')
            span.innerText = feature_label
            th_feature.appendChild(span)
            th_feature.setAttribute('colspan', 2)
            tr.appendChild(th_feature)
        }
        this.table.appendChild(tr)
    }
    create_rows() {
        let specimens = this.get_specimens_list()
        for (let specimen of specimens) {
            let tr = document.createElement('tr')
            let td = document.createElement('td')
            td.innerText = specimen
            tr.appendChild(td)
            this.table.appendChild(tr)
        }
        for (let feature_name in this.feature_values_by_name) {
            let feature_values = this.feature_values_by_name[feature_name]
            for (let i = 1; i < this.table.children.length; i++) {
                let tr = this.table.children[i]
                let td = document.createElement('td')
                td.innerText = feature_values[i-1]['phenotype count']
                tr.appendChild(td)
                let td_percent = document.createElement('td')
                let percentage = feature_values[i-1]['percent of all cells in specimen']
                td_percent.innerText = feature_values[i-1]['percent of all cells in specimen'] + '%'
                td_percent.setAttribute('class', 'de-emphasized secondary-cell')
                tr.appendChild(td_percent)

                let value = percentage / 100
                let rgb_color = CoolWarmColorMap.get_rgb_color(value)
                td_percent.style.background = rgb_color
                td.style.background = rgb_color

                td_percent.style.color = Math.round(255 * (0.25 + value/2.0))
            }
        }
    }
    get_specimens_list() {
        let keys = Array.from(Object.keys(this.feature_values_by_name))
        if (keys.length == 0) {
            return []
        }
        return this.feature_values_by_name[keys[0]].map( function(data_row){
            return data_row['specimen']
        })
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
        delete this.feature_labels[key]
        delete this.feature_values_by_name[key]
        this.update_table()
    }
    add_feature(row_label, column_label, feature_values) {
        let key = this.get_key(row_label, column_label)
        this.showing_features.push(key)
        this.feature_labels[key] = Array.from(new Set([row_label, column_label])).join(' and ' )
        this.feature_values_by_name[key] = feature_values
        this.update_table()
    }
    add_exportability() {
        if (this.table.children.length == 0) {
            return
        }
        let export_widget = new ExportableElementWidget(this.table, this.table, raw_style_sheet)
    }
}
