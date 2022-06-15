function setup_interactive_elements(){
    setup_openable_sections()
    setup_retrievable_stats_page()
}

function setup_retrievable_stats_page() {
    let section = document.getElementsByClassName('retrievable-stats-page')[0]
    new PhenotypeFractionsStatsPage(section)
}

class PhenotypeFractionsStatsPage extends RetrievableStatsPage {
    discover_stats_table(section) {
        let id = section.getElementsByClassName('stats-table')[0]
        return new PhenotypeFractionsStatsTable(id)
    }    
}

class PhenotypeFractionsStatsTable extends StatsTable {
    setup_table_header() {
        this.table.innerHTML = ''
        let header = ["Marker", "Multiplicity", "Assay", "Result", "Mean % <br/>cells positive", "Standard deviation <br/>of % values", "Maximum", "Value", "Minimum", "Value"]
        let header_row = document.createElement("tr")
        for (let i = 0; i < header.length; i++) {
            let cell = document.createElement("th")
            cell.innerHTML = header[i] + '&nbsp;'
            let sort_button = document.createElement("span");
            sort_button.innerHTML = " [+] "
            let reference = this
            sort_button.addEventListener('click', function(event) {
                reference.sort_data_rows(i, 1)
            })
            sort_button.setAttribute("class", "sortbutton")
            let sort_button2 = document.createElement("span");
            sort_button2.innerHTML = " [-] "
            sort_button2.addEventListener('click', function(event) {
                reference.sort_data_rows(i, -1)
            })
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
