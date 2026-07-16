web: cd backend && python manage.py migrate && python manage.py index_knowledge_base && gunicorn codementor.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 180
