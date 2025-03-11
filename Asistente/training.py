import json
import random
import pickle
import numpy

import nltk
from nltk.stem import WordNetLemmatizer

from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout
from keras.optimizers import sgd_experimental

lemmatizer = WordNetLemmatizer()

intents = json.load(open('intents.json').read)

nltk.download('punkt')
nltk.download('wordnet')
nltk.download('omw-1.4')

words = []
classes= []
documents = []
ignore_letters = ['?','!','¿','.',',']

for intent in intents['intents']:
    for pattern in intents['patterns']:
        word_list = nltk.word_tokenize(pattern)
        