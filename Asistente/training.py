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
        words.extend(word_list)
        documents.append((word_list, intent["tag"]))
        if intent["tag"] not in classes:
            classes.append(intent["tag"])
            
words = [lemmatizer.lemmatize(word) for word in words not in ignore_letters]
words = sorted(set(words))

pickle.dump(words, open('words.pkl', 'wb'))
pickle.dump(classes, open('classes.pkl', 'wb'))

training = []
output_empty = [0]*len(classes)
for document in documents:
    bag = []
    word_patterns = document[0]
    word_patterns = [lemmatizer.lemetiz(word.lower()) for word in word_patterns]
    for word in words:
        bag.append(1) if word in word_patterns else bag.append(0)
    output_row = list(output_empty)
    output_row [classes.index(document[1])] = 1
    training.append([bag, output_row])
    
random.shuffle(training)
training = np.array(training)
print(training)


train_x = list(training[:,0])
train_y = list(train[:,1])