function setup_retrievable_stats_page() {
    let section = document.getElementsByClassName('retrievable-stats-page')[0]
    new PhenotypeFractionsStatsPage(section)
}

class PhenotypeFractionsStatsPage extends RetrievableStatsPage {
    constructor(section) {
        super(section)
        this.section = section
    }
    discover_stats_table(section) {
        let id = section.getElementsByClassName('stats-table')[0].getAttribute('id')
        return new PhenotypeFractionsStatsTable(id, this)
    }
    get_section() {
        return this.section
    }
    initialize_phenotype_selection_table() {
        let table = this.get_section().getElementsByClassName('selection-table')[0]
        this.phenotype_selection_table = new SelectionTable(table, this.stats_table.get_phenotype_names())
    }
}

class SelectionTable {
    constructor(table, phenotype_names) {
        let table_header = document.createElement('tr')
        let th = document.createElement('th')
        th.innerHTML = 'Phenotype'
        table_header.appendChild(th)
        table.appendChild(table_header)
        for (let i = 0; i < phenotype_names.length; i++) {
            let table_row = this.create_table_row(phenotype_names[i])
            table.appendChild(table_row)
        }
    }
    create_table_row(phenotype_name) {
        let tr = document.createElement('tr')
        let td = document.createElement('td')
        td.innerHTML = phenotype_name
        td.setAttribute('class', 'first last')
        td.addEventListener('click', function(event) {
            this.parentElement.classList.toggle('selected-row')
        })
        tr.appendChild(td)
        return tr
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
        let obj = stats[Object.keys(stats)[0]]
        let outcome_column = this.get_outcome_column(obj)
        for (let i = 0; i < obj.length; i++) {
            this.table.appendChild(this.create_table_row(obj[i]))
        }
        this.patch_header(outcome_column)
        this.update_row_counter()
        this.record_phenotype_names_from_response(obj)
        this.get_parent_page().initialize_phenotype_selection_table()
        this.get_and_handle_phenotype_criteria_names()
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
    get_and_handle_phenotype_criteria_names() {
        for (let phenotype_name of this.get_phenotype_names()) {
            this.get_and_handle_phenotype_criteria_name(phenotype_name)
        }
    }
    get_and_handle_phenotype_criteria_name(phenotype_name) {
        let encoded_phenotype_name = encodeURIComponent(phenotype_name)
        let url_base = get_api_url_base()
        let url=`${url_base}/phenotype-criteria-name/?phenotype_symbol=${encoded_phenotype_name}`
        let reference = this
        get_from_url({url, callback: function(response, event) {
            reference.update_phenotype_criteria_name(phenotype_name, response, event)
        }})
    }
    update_phenotype_criteria_name(phenotype_name, response, event) {
        let obj = JSON.parse(response.responseText)
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
