source activate py39-torch20
gunicorn -w 1 -b :5023 -t 30 --reload slack_bot:app