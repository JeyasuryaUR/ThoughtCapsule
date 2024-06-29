pip install -r requirements.txt
python -m spacy download en_core_web_sm
python manage.py makemigrations
python manage.py migrate