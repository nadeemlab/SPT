#!/bin/bash
# Usage:
#     source login.sh

source scripts/printing.sh

print_heading_line "Logging in for management of SPT deployment."

if [[ -f "_login.exp" ]];
then
    ./_login.exp
else
    print_regular_line "'expect' script "_login.exp" not found, so this will run interactively, for initialization."
    autoexpect ./scripts/_login.sh
    sed 's/set force_conservative 0/set force_conservative 1/g' script.exp > _login.exp
    chmod +x _login.exp
    rm script.exp
fi

source _saml2aws_script.sh
rm _saml2aws_script.sh
rm _login.exp
