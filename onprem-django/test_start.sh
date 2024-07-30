sudo apt update
sudo apt install python3-venv -y

VENV_DIR=venv

python3 -m venv $VENV_DIR

source $VENV_DIR/bin/activate

pip install -r requirements.txt

python3 manage.py makemigrations 
python3 manage.py migrate
python manage.py createsuperuser --noinput --username=yoonan --email=yoonan@teiren.io --password=cute428!
python3 manage.py runserver 8888

deactivate
