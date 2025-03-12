import json
import random
import pickle
import numpy as np

import nltk
from nltk.stem import WordNetLemmatizer

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Activation, Dropout
from tensorflow.keras.optimizers import SGD

lemmatizer = WordNetLemmatizer()

with open('intents.json', 'r', encoding='utf-8') as file:
    intents = json.load(file)
    
# nltk.download('punkt_tab')  # This seems to be an error
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('omw-1.4')

words = []
classes = []
documents = []
ignore_letters = ['?','!','¿','.',',']

for intent in intents['intents']:
    if 'patterns' in intent:
        for pattern in intent['patterns']:
            word_list = nltk.word_tokenize(pattern)
            words.extend(word_list)
            documents.append((word_list, intent["tag"]))
            if intent["tag"] not in classes:
                classes.append(intent["tag"])
            
words = [lemmatizer.lemmatize(word) for word in words if word not in ignore_letters]
words = sorted(set(words))

pickle.dump(words, open('words.pkl', 'wb'))
pickle.dump(classes, open('classes.pkl', 'wb'))

training = []
output_empty = [0] * len(classes)
for document in documents:
    bag = []
    word_patterns = document[0]
    word_patterns = [lemmatizer.lemmatize(word.lower()) for word in word_patterns]
    for word in words:
        bag.append(1) if word in word_patterns else bag.append(0)
    if len(bag) != len(words):
        print(f"Error: bag tiene longitud {len(bag)}, debería ser {len(words)}")
    
    output_row = list(output_empty)
    output_row[classes.index(document[1])] = 1
    training.append([bag, output_row])
    
random.shuffle(training)
train_x = []
train_y = []
for bag, output_row in training:
    train_x.append(bag)
    train_y.append(output_row)

train_x = np.array(train_x)
train_y = np.array(train_y)

# Create the model properly
model = Sequential()  # Instantiate the Sequential model
model.add(Dense(128, input_shape=(len(train_x[0]),), activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(len(train_y[0]), activation='softmax'))

# Fix the SGD optimizer
sgd = SGD(learning_rate=0.001, decay=1e-6, momentum=0.9, nesterov=True)  # Use standard SGD, not sgd_experimental
model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])
train_process = model.fit(np.array(train_x), np.array(train_y), epochs=100, batch_size=5, verbose=1)

# Save the model
model.save('chatbot_model.h5')
print("Model trained and saved successfully!")