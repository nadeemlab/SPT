
if [[ "$1" == "--help"  || "$1" == "" ]]; then
    echo "Supply the (binary format) file created by the expression matrix caching command, to parse it."
    exit
fi

if ! command -v ggrep &> /dev/null
then
    ggrep=grep
else
    ggrep=ggrep
fi

xxd -c 16 -g 0 -b $1 | $ggrep -oP '(?<=[01]{64})[01]+' | grep -oE '[01]+' | sed 's/0/ /g'
