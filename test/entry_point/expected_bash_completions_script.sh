
### Start added by spatialprofilingtoolbox

_spt_completions()
{
    if [[ "${#COMP_WORDS[@]}" -eq "2" ]]; then
        COMPREPLY=($(compgen -W "cggnn ondemand db workflow" "${COMP_WORDS[1]}"));
    fi
    if [[ "${#COMP_WORDS[@]}" -eq "3" ]]; then
        case ${COMP_WORDS[1]} in
            cggnn)
                COMPREPLY=($(compgen -W "run" "${COMP_WORDS[2]}"));
            ;;
            ondemand)
                COMPREPLY=($(compgen -W "cache-expressions-data-array start" "${COMP_WORDS[2]}"));
            ;;
            db)
                COMPREPLY=($(compgen -W "create-schema guess-channels-from-object-files modify-constraints retrieve-feature-matrices status" "${COMP_WORDS[2]}"));
            ;;
            workflow)
                COMPREPLY=($(compgen -W "aggregate-core-results configure core-job extract-compartments generate-run-information initialize merge-performance-reports merge-sqlite-dbs report-on-logs report-run-configuration" "${COMP_WORDS[2]}"));
            ;;
        esac
    fi
    if [[ "${#COMP_WORDS[@]}" -eq "4" ]]; then
        case ${COMP_WORDS[1]} in
            cggnn)
                case ${COMP_WORDS[2]} in
                    'run')
                        echo ''
                        spt cggnn ${COMP_WORDS[2]} --help
                        echo '<press enter>'
                    ;;
                esac
            ;;
            ondemand)
                case ${COMP_WORDS[2]} in
                    'cache-expressions-data-array'|'start')
                        echo ''
                        spt ondemand ${COMP_WORDS[2]} --help
                        echo '<press enter>'
                    ;;
                esac
            ;;
            db)
                case ${COMP_WORDS[2]} in
                    'create-schema'|'guess-channels-from-object-files'|'modify-constraints'|'retrieve-feature-matrices'|'status')
                        echo ''
                        spt db ${COMP_WORDS[2]} --help
                        echo '<press enter>'
                    ;;
                esac
            ;;
            workflow)
                case ${COMP_WORDS[2]} in
                    'aggregate-core-results'|'configure'|'core-job'|'extract-compartments'|'generate-run-information'|'initialize'|'merge-performance-reports'|'merge-sqlite-dbs'|'report-on-logs'|'report-run-configuration')
                        echo ''
                        spt workflow ${COMP_WORDS[2]} --help
                        echo '<press enter>'
                    ;;
                esac
            ;;
        esac
    fi
}

complete -F _spt_completions spt
### End added by spatialprofilingtoolbox
