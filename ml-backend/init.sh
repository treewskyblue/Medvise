#!/bin/bash

python create_model_in_container.py

exec uvicorn main:app --host 0.0.0.0 --port 8000