
python -m venv venv 2>/dev/null 1>/dev/null
source venv/bin/activate
python -m pip install toml 2>/dev/null 1>/dev/null
python building/create_requirements.py $1
deactivate
rm -rf venv/
