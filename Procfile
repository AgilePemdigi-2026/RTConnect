release: cd backend && python -m database.migrate
web: cd backend && gunicorn --workers 2 --threads 4 --timeout 60 -b 0.0.0.0:$PORT app:app
