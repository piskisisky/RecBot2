#!/bin/bash

# Оновлюємо пакети
apt-get update && apt-get install -y portaudio19-dev

# Встановлюємо Python-залежності
pip install -r requirements.txt