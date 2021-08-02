
BOLD_RED='\e[1;31m'
BOLD_GREEN='\e[1;32m'
BOLD_YELLOW='\e[1;33m'
BOLD_BLUE='\e[1;34m'
BOLD_MAGENTA='\e[1;35m'
BOLD_CYAN='\e[1;36m'
RESET='\e[0m'

FOUND_OFFENDERS="no"
for f in $(find .); do
if test -d $f; then
    g=$(echo $f | grep -oE '(__pycache__|egg-info)$')
    if [[ "$g" == "__pycache__" || "$g" == "egg-info" ]]; then
        printf "$BOLD_YELLOW""Will remove:$RESET"" $f\n"
        FOUND_OFFENDERS="yes"
    fi
fi
done

if [[ "$FOUND_OFFENDERS" == "no" ]]; then
    printf "$BOLD_GREEN""No __pycache__ or ...egg-info subdirectories found.""$RESET""\n"
    printf "$BOLD_RED""No action taken""$RESET""\n"
    exit
fi

echo ""
RESPONSE=""
while [[ "$RESPONSE" == "" ]]; do
    printf "$BOLD_GREEN""Proceed? ""$RESET""(yes/no) "
    read RESPONSEVAR
    if [[ "$RESPONSEVAR" == "no" ]]; then
        printf "$BOLD_RED""No action taken""$RESET""\n"
        break
    fi
    if [[ "$RESPONSEVAR" == "yes" ]]; then
        printf "$BOLD_GREEN""Deleting __pycache__ and ...egg-info subdirectories ... ""$RESET""\n"

        for f in $(find .); do
        if test -d $f; then
            g=$(echo $f | grep -oE '(__pycache__|egg-info)$')
            if [[ "$g" == "__pycache__" || "$g" == "egg-info" ]]; then
                printf "$BOLD_YELLOW""rm $RESET$BOLD_MAGENTA -rf$RESET"" $f\n"
                rm -rf "$f"
            fi
        fi
        done

        break
    fi
done
