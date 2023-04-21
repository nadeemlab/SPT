
function check_image_exists(){
    exactname="$1"
    found=$(docker image ls | cut -f1 -d' ' | grep "^$exactname\$" | head -n1)
    if [[ "$found" == "$exactname" ]];
    then
        echo "yes"
    else
        echo "no"
    fi
}
