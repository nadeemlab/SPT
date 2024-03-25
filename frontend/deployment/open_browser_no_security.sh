
if [[ "$OSTYPE" == "linux-gnu"* ]];
then
    browser=google-chrome ;
elif [[ "$OSTYPE" == "darwin"* ]];
then
    browser="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ;
else
    browser="start chrome" ;
fi

echo "Opening browser..."
"$browser" --user-data-dir=tempuserdatadir/ --disable-web-security 127.0.0.1:80
echo "Browser was closed."
